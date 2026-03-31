from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.database.repository import (
    BucketRepository,
    FolderRepository,
    FileRepository,
    BucketPermissionRepository,
)
from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.exceptions import NotFound, PermissionDenied


class AccessService:
    def __init__(
        self,
        bucket_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        folder_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        file_repository: Annotated[FileRepository, Depends(FileRepository)],
        bucket_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
    ):
        self._bucket_repository = bucket_repository
        self._folder_repository = folder_repository
        self._file_repository = file_repository
        self._bucket_permission_repository = bucket_permission_repository

    async def check_file_access(
        self,
        user_id: UUID,
        file_id: UUID,
        required_permission: PermissionType = PermissionType.READ,
    ) -> tuple[UUID, UUID]:
        file = await self._file_repository.get_by_id(file_id)
        if not file:
            raise NotFound('File not found')

        await self.check_bucket_access(user_id, file.bucket_id, required_permission)
        return file.bucket_id, file.owner_id

    async def check_folder_access(
        self,
        user_id: UUID,
        folder_id: UUID,
        required_permission: PermissionType = PermissionType.READ,
    ) -> tuple[UUID, UUID]:
        folder = await self._folder_repository.get_by_id(folder_id)
        if not folder:
            raise NotFound('Folder not found')

        await self.check_bucket_access(user_id, folder.bucket_id, required_permission)
        return folder.bucket_id, folder.owner_id

    async def check_bucket_access(
        self,
        user_id: UUID,
        bucket_id: UUID,
        required_permission: PermissionType = PermissionType.READ,
    ) -> None:
        bucket = await self._bucket_repository.get_by_id(bucket_id)
        if not bucket:
            raise NotFound('Bucket not found')

        if bucket.owner_id == user_id:
            return

        if bucket.is_public and required_permission == PermissionType.READ:
            return

        permission = await self._bucket_permission_repository.get_by_bucket_and_user(bucket_id, user_id)
        if not permission:
            raise PermissionDenied('Access denied to this bucket')

        rank = {PermissionType.READ: 1, PermissionType.WRITE: 2, PermissionType.ADMIN: 3}
        if rank[permission.permission_type] < rank[required_permission]:
            raise PermissionDenied('Insufficient permissions for this operation')
