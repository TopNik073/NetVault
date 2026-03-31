from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.database.repository import (
    UserRepository,
    FolderRepository,
    BucketRepository,
    BucketPermissionRepository,
    FileRepository,
)
from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.database.repository.postgres.folder.dtos import Folder
from src.exceptions import NotFound, ClientError, Conflict
from src.integrations.minio.client import MinioClient
from src.services.access.service import AccessService


class FoldersService:
    def __init__(  # noqa: PLR0913
        self,
        users_repository: Annotated[UserRepository, Depends(UserRepository)],
        folder_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        bucket_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        bucket_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
        file_repository: Annotated[FileRepository, Depends(FileRepository)],
        minio_client: Annotated[MinioClient, Depends(MinioClient)],
        access_service: Annotated[AccessService, Depends(AccessService)],
    ):
        self._user_repository = users_repository
        self._folder_repository = folder_repository
        self._bucket_repository = bucket_repository
        self._bucket_permission_repository = bucket_permission_repository
        self._file_repository = file_repository
        self._minio_client = minio_client
        self._access_service = access_service

    async def _get_user_permission(self, user_id: UUID, bucket_id: UUID) -> PermissionType | None:
        bucket = await self._bucket_repository.get_by_id(bucket_id)
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

    async def _get_folder_and_check_access(
        self, folder_id: UUID, user_id: UUID, required_permission: PermissionType
    ) -> Folder:
        folder = await self._folder_repository.get_by_id(folder_id)
        if not folder:
            raise NotFound('Folder not found')
        await self._access_service.check_bucket_access(user_id, folder.bucket_id, required_permission)
        return folder

    async def _is_descendant(self, folder_id: UUID, ancestor_id: UUID) -> bool:
        return await self._folder_repository.is_descendant(folder_id, ancestor_id)

    # ---------- Основные методы ----------
    async def get_folder_info(self, folder_id: UUID, user_id: UUID) -> Folder:
        return await self._get_folder_and_check_access(folder_id, user_id, PermissionType.READ)

    async def create_folder(self, name: str, bucket_id: UUID, parent_id: UUID | None, user_id: UUID) -> Folder:
        await self._access_service.check_bucket_access(user_id, bucket_id, PermissionType.WRITE)

        depth = 0
        if parent_id:
            parent = await self._folder_repository.get_by_id(parent_id)
            if not parent:
                raise NotFound('Parent folder not found')
            if parent.bucket_id != bucket_id:
                raise ClientError('Parent folder must belong to the same bucket')
            depth = parent.depth + 1

        existing = await self._folder_repository.get_by_parent_and_name(bucket_id, parent_id, name)
        if existing:
            raise Conflict('Folder with this name already exists in this location')

        folder = Folder(
            name=name,
            bucket_id=bucket_id,
            parent_id=parent_id,
            depth=depth,
        )
        return await self._folder_repository.create(folder)

    async def rename_folder(self, folder_id: UUID, new_name: str, user_id: UUID) -> Folder:
        folder = await self._get_folder_and_check_access(folder_id, user_id, PermissionType.WRITE)

        existing = await self._folder_repository.get_by_parent_and_name(folder.bucket_id, folder.parent_id, new_name)
        if existing and existing.id != folder_id:
            raise Conflict('Folder with this name already exists in this location')

        folder.name = new_name
        return await self._folder_repository.update(folder)

    async def move_folder(self, folder_id: UUID, new_parent_id: UUID | None, user_id: UUID) -> Folder:
        folder = await self._get_folder_and_check_access(folder_id, user_id, PermissionType.WRITE)

        new_parent = None
        if new_parent_id:
            new_parent = await self._folder_repository.get_by_id(new_parent_id)
            if not new_parent:
                raise NotFound('Target parent folder not found')
            if new_parent.bucket_id != folder.bucket_id:
                raise ClientError('Cannot move folder to a different bucket')
            if new_parent_id == folder_id:
                raise ClientError('Cannot move folder into itself')

            if await self._is_descendant(new_parent_id, folder_id):
                raise ClientError('Cannot move folder into its own descendant')

            await self._access_service.check_bucket_access(user_id, new_parent.bucket_id, PermissionType.WRITE)

        new_depth = 0 if new_parent is None else new_parent.depth + 1
        delta_depth = new_depth - folder.depth

        existing = await self._folder_repository.get_by_parent_and_name(folder.bucket_id, new_parent_id, folder.name)
        if existing and existing.id != folder_id:
            raise Conflict('Folder with this name already exists in target location')

        folder.parent_id = new_parent_id
        folder.depth = new_depth
        await self._folder_repository.update(folder)

        if delta_depth != 0:
            await self._folder_repository.update_subtree_depth(folder_id, delta_depth)

        return folder

    async def delete_folder(self, folder_id: UUID, user_id: UUID) -> None:
        folder = await self._get_folder_and_check_access(folder_id, user_id, PermissionType.WRITE)

        subtree_ids = await self._folder_repository.get_subtree_ids(folder_id)
        if not subtree_ids:
            raise NotFound('Folder not found')

        files = await self._file_repository.get_by_folder_ids(subtree_ids)

        if files:
            bucket = await self._bucket_repository.get_by_id(folder.bucket_id)
            if not bucket:
                raise NotFound('Associated bucket not found')

            await self._minio_client.delete_objects(
                bucket_name=bucket.minio_bucket_name,
                object_names=[file.storage_filename for file in files],
            )

            file_ids = [f.id for f in files]
            await self._file_repository.delete_many(file_ids)

            total_size = sum(f.file_size_bytes for f in files)
            owner = await self._user_repository.get_by_id(folder.owner_id)
            if owner:
                owner.storage_used_bytes -= total_size
                await self._user_repository.update(owner)

        await self._folder_repository.delete_many(subtree_ids)

    async def get_folders(self, user_id: UUID, bucket_id: UUID, parent_id: UUID | None) -> list[Folder]:
        await self._access_service.check_bucket_access(user_id, bucket_id, PermissionType.READ)

        folders = await self._folder_repository.get_by_bucket_and_parent(bucket_id, parent_id)

        permission = await self._get_user_permission(user_id, bucket_id)
        for f in folders:
            f.permission = permission

        return folders
