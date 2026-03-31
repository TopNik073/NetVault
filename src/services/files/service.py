from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.database.repository import (
    UserRepository,
    BucketRepository,
    BucketPermissionRepository,
    FolderRepository,
    FileRepository,
)
from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.database.repository.postgres.file.dtos import File
from src.exceptions import NotFound, ClientError, Conflict
from src.integrations.minio.client import MinioClient
from src.services.access.service import AccessService


class FilesService:
    def __init__(  # noqa: PLR0913
        self,
        users_repository: Annotated[UserRepository, Depends(UserRepository)],
        buckets_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        bucket_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
        folders_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        files_repository: Annotated[FileRepository, Depends(FileRepository)],
        minio_client: Annotated[MinioClient, Depends(MinioClient)],
        access_service: Annotated[AccessService, Depends(AccessService)],
    ):
        self._users_repository = users_repository
        self._buckets_repository = buckets_repository
        self._bucket_permission_repository = bucket_permission_repository
        self._folders_repository = folders_repository
        self._files_repository = files_repository
        self._minio_client = minio_client
        self._access_service = access_service

    async def _get_user_permission(self, user_id: UUID, bucket_id: UUID) -> PermissionType | None:
        bucket = await self._buckets_repository.get_by_id(bucket_id)
        if not bucket:
            return None

        if bucket.owner_id == user_id:
            return PermissionType.ADMIN

        permission = await self._bucket_permission_repository.get_by_bucket_and_user(bucket_id, user_id)
        if permission:
            return permission.permission_type

        if bucket.is_public:
            return PermissionType.READ

        return None

    async def _get_file_and_check_access(
        self, file_id: UUID, user_id: UUID, required_permission: PermissionType
    ) -> File:
        file = await self._files_repository.get_by_id(file_id)
        if not file:
            raise NotFound('File not found')
        await self._access_service.check_bucket_access(user_id, file.bucket_id, required_permission)
        return file

    async def get_file_metadata(self, file_id: UUID, user_id: UUID) -> File:
        return await self._get_file_and_check_access(file_id, user_id, PermissionType.READ)

    async def rename_or_move_file(
        self,
        file_id: UUID,
        user_id: UUID,
        new_name: str | None = None,
        new_folder_id: UUID | None = None,
        move_to_root: bool = False,
    ) -> File:
        file = await self._get_file_and_check_access(file_id, user_id, PermissionType.WRITE)

        target_name = new_name if new_name is not None else file.name

        if move_to_root:
            target_folder_id = None
        elif new_folder_id is not None:
            target_folder_id = new_folder_id
        else:
            target_folder_id = file.folder_id

        if target_folder_id and target_folder_id != file.folder_id:
            folder = await self._folders_repository.get_by_id(target_folder_id)
            if not folder:
                raise NotFound('Target folder not found')

            if folder.bucket_id != file.bucket_id:
                raise ClientError('Cannot move file to a folder in a different bucket')

        if target_name != file.original_filename or target_folder_id != file.folder_id:
            existing = await self._files_repository.get_by_bucket_and_parent_and_name(
                file.bucket_id, target_folder_id, target_name
            )
            if existing and existing.id != file_id:
                raise Conflict('File with this name already exists in the target location')

        file.original_filename = target_name
        file.folder_id = target_folder_id

        return await self._files_repository.update(file)

    async def delete_file(self, file_id: UUID, user_id: UUID) -> None:
        file = await self._get_file_and_check_access(file_id, user_id, PermissionType.WRITE)

        bucket = await self._buckets_repository.get_by_id(file.bucket_id)
        if not bucket:
            raise NotFound('Associated bucket not found')

        await self._minio_client.delete_object(bucket.minio_bucket_name, file.storage_filename)

        await self._files_repository.delete(file_id)

        owner = await self._users_repository.get_by_id(file.owner_id)
        if owner:
            owner.storage_used_bytes -= file.file_size_bytes
            await self._users_repository.update(owner)

    async def get_download_link(self, file_id: UUID, user_id: UUID, expires_in: int = 3600) -> tuple[str, datetime]:
        file = await self._get_file_and_check_access(file_id, user_id, PermissionType.READ)

        bucket = await self._buckets_repository.get_by_id(file.bucket_id)
        if not bucket:
            raise NotFound('Associated bucket not found')

        url, expires_at = await self._minio_client.get_presigned_download_url(
            bucket.minio_bucket_name, file.storage_filename, expires_in=expires_in
        )
        return url, expires_at

    async def get_recent_files(self, user_id: UUID, limit: int = 10) -> list[File]:
        files = await self._files_repository.get_recent_by_owner(user_id, limit)

        bucket_ids = {f.bucket_id for f in files}
        permission_map = {}
        for bucket_id in bucket_ids:
            permission_map[bucket_id] = await self._get_user_permission(user_id, bucket_id)

        for f in files:
            f.permission = permission_map.get(f.bucket_id)

        return files

    async def get_files(self, user_id: UUID, bucket_id: UUID, folder_id: UUID | None) -> list[File]:
        await self._access_service.check_bucket_access(user_id, bucket_id, PermissionType.READ)

        files = await self._files_repository.get_by_bucket_and_folder(bucket_id, folder_id)

        permission = await self._get_user_permission(user_id, bucket_id)
        for f in files:
            f.permission = permission

        return files
