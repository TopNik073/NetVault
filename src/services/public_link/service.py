from datetime import datetime, UTC, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.core.config import config
from src.database.repository import (
    PublicLinkRepository,
    FileRepository,
    FolderRepository,
    BucketRepository,
    BucketPermissionRepository,
)
from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.database.repository.postgres.public_link.dtos import PublicLink
from src.exceptions import NotFound, ClientError, PermissionDenied
from src.handlers.api.v1.public_links.models import CreatePublicLinkResponse, PublicLinkListResponse, \
    PublicLinkDetailResponse
from src.integrations.minio.client import MinioClient
from src.services.access.service import AccessService


class PublicLinkService:
    def __init__(  # noqa: PLR0913
        self,
        public_link_repository: Annotated[PublicLinkRepository, Depends(PublicLinkRepository)],
        file_repository: Annotated[FileRepository, Depends(FileRepository)],
        folder_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        bucket_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        bucket_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
        minio_client: Annotated[MinioClient, Depends(MinioClient)],
        access_service: Annotated[AccessService, Depends(AccessService)],
    ):
        self._public_link_repository = public_link_repository
        self._file_repository = file_repository
        self._folder_repository = folder_repository
        self._bucket_repository = bucket_repository
        self._bucket_permission_repository = bucket_permission_repository
        self._minio_client = minio_client
        self._access_service = access_service

    def _get_public_base_url(self) -> str:
        scheme = 'https' if config.SECURE else 'http'
        return f'{scheme}://{config.EXTERNAL_ADDRESS}'

    def _generate_public_link_url(self, link_id: UUID) -> str:
        base_url = self._get_public_base_url()
        return f'{base_url}/public/download/{link_id}'

    async def create_link_with_url(
        self,
        actor_user_id: UUID,
        file_id: UUID | None,
        folder_id: UUID | None,
        expires_in_seconds: int | None,
        max_downloads: int | None,
    ) -> dict:
        link = await self.create_link(
            actor_user_id=actor_user_id,
            file_id=file_id,
            folder_id=folder_id,
            expires_in_seconds=expires_in_seconds,
            max_downloads=max_downloads,
        )

        result = CreatePublicLinkResponse.model_validate(link).model_dump(by_alias=True)
        result['url'] = self._generate_public_link_url(link.id)
        return result

    async def list_links_with_urls(
        self,
        actor_user_id: UUID,
        file_id: UUID | None,
        folder_id: UUID | None,
    ) -> list[dict]:
        links = await self.list_links(
            actor_user_id=actor_user_id,
            file_id=file_id,
            folder_id=folder_id,
        )

        result = PublicLinkListResponse.model_validate(links).model_dump(by_alias=True)
        for link in result:
            link['url'] = self._generate_public_link_url(link['id'])
        return result

    async def get_link_with_url(self, actor_user_id: UUID, link_id: UUID) -> dict:
        link = await self.get_link(actor_user_id=actor_user_id, link_id=link_id)

        result = PublicLinkDetailResponse.model_validate(link).model_dump(by_alias=True)
        result['url'] = self._generate_public_link_url(link.id)
        return result

    async def _check_resource_access(
        self,
        user_id: UUID,
        file_id: UUID | None = None,
        folder_id: UUID | None = None,
        required_permission: PermissionType = PermissionType.READ,
    ) -> UUID:
        bucket_id = None
        if file_id:
            file = await self._file_repository.get_by_id(file_id)
            if not file:
                raise NotFound('File not found')
            bucket_id = file.bucket_id
        elif folder_id:
            folder = await self._folder_repository.get_by_id(folder_id)
            if not folder:
                raise NotFound('Folder not found')
            bucket_id = folder.bucket_id
        else:
            raise ClientError('No resource specified')

        bucket = await self._bucket_repository.get_by_id(bucket_id)
        if not bucket:
            raise NotFound('Associated bucket not found')

        if bucket.owner_id == user_id:
            return bucket_id

        if bucket.is_public and required_permission == PermissionType.READ:
            return bucket_id

        permission = await self._bucket_permission_repository.get_by_bucket_and_user(bucket_id, user_id)
        if not permission:
            raise PermissionDenied('Access denied to this bucket')

        rank = {PermissionType.READ: 1, PermissionType.WRITE: 2, PermissionType.ADMIN: 3}
        if rank[permission.permission_type] < rank[required_permission]:
            raise PermissionDenied('Insufficient permissions for this operation')

        return bucket_id

    async def create_link(
        self,
        actor_user_id: UUID,
        file_id: UUID | None,
        folder_id: UUID | None,
        expires_in_seconds: int | None,
        max_downloads: int | None,
    ) -> PublicLink:
        await self._check_resource_access(
            user_id=actor_user_id,
            file_id=file_id,
            folder_id=folder_id,
            required_permission=PermissionType.WRITE,
        )

        expires_at = None
        if expires_in_seconds is not None:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

        link = PublicLink(
            file_id=file_id,
            folder_id=folder_id,
            expires_at=expires_at,
            max_downloads=max_downloads,
            downloads_count=0,
        )
        return await self._public_link_repository.create(link)

    async def list_links(
        self,
        actor_user_id: UUID,
        file_id: UUID | None,
        folder_id: UUID | None,
    ) -> list[PublicLink]:
        if (file_id is None) == (folder_id is None):
            raise ClientError('Exactly one of file_id or folder_id must be provided')

        await self._check_resource_access(
            user_id=actor_user_id,
            file_id=file_id,
            folder_id=folder_id,
            required_permission=PermissionType.READ,
        )

        if file_id:
            links = await self._public_link_repository.get_by_file(file_id)
        else:
            links = await self._public_link_repository.get_by_folder(folder_id)

        return links

    async def get_link(self, actor_user_id: UUID, link_id: UUID) -> PublicLink:
        link = await self._public_link_repository.get_by_id(link_id)
        if not link:
            raise NotFound('Public link not found')

        await self._check_resource_access(
            user_id=actor_user_id,
            file_id=link.file_id,
            folder_id=link.folder_id,
            required_permission=PermissionType.WRITE,
        )

        return link

    async def delete_link(self, actor_user_id: UUID, link_id: UUID) -> None:
        link = await self._public_link_repository.get_by_id(link_id)
        if not link:
            raise NotFound('Public link not found')

        await self._check_resource_access(
            user_id=actor_user_id,
            file_id=link.file_id,
            folder_id=link.folder_id,
            required_permission=PermissionType.WRITE,
        )

        await self._public_link_repository.delete(link_id)

    async def get_public_link_info(self, link_id: UUID) -> dict:
        link = await self._public_link_repository.get_by_id(link_id)
        if not link:
            raise NotFound('Public link not found')

        if link.expires_at and link.expires_at < datetime.now(UTC):
            raise ClientError('Link expired', code='link_expired')

        if link.max_downloads and link.downloads_count >= link.max_downloads:
            raise ClientError('Download limit exceeded', code='download_limit_exceeded')

        file_name = None
        if link.file_id:
            file = await self._file_repository.get_by_id(link.file_id)
            if file:
                file_name = file.original_filename

        return {
            'id': link.id,
            'fileName': file_name,
            'downloadsCount': link.downloads_count,
            'maxDownloads': link.max_downloads,
            'expiresAt': link.expires_at,
        }

    async def get_public_download_url(self, link_id: UUID) -> str:
        link = await self._public_link_repository.get_by_id(link_id)
        if not link:
            raise NotFound('Public link not found')

        if link.expires_at and link.expires_at < datetime.now(UTC):
            raise ClientError('Link expired', code='link_expired')

        if link.max_downloads and link.downloads_count >= link.max_downloads:
            raise ClientError('Download limit exceeded', code='download_limit_exceeded')

        if not link.file_id:
            raise ClientError('Folder links not supported for download', code='folder_not_supported')

        file = await self._file_repository.get_by_id(link.file_id)
        if not file:
            raise NotFound('File not found')

        bucket = await self._bucket_repository.get_by_id(file.bucket_id)
        if not bucket:
            raise NotFound('Bucket not found')

        url, _ = await self._minio_client.get_presigned_download_url(
            bucket_name=bucket.minio_bucket_name,
            object_name=file.storage_filename,
            expires_in=3600,
        )

        link.downloads_count += 1
        await self._public_link_repository.update(link)

        return url
