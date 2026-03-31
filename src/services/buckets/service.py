import uuid
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
from src.database.repository.postgres.bucket.dtos import Bucket
from src.database.repository.postgres.bucket_permission.dtos import PermissionType, BucketPermission
from src.database.repository.postgres.user.dtos import User
from src.exceptions import PermissionDenied, NotFound, Conflict, ClientError
from src.integrations.minio.client import MinioClient
from src.services.buckets.models import UserBrief
from src.services.ses import YandexSESService


class BucketsService:
    def __init__(  # noqa: PLR0913
        self,
        users_repository: Annotated[UserRepository, Depends(UserRepository)],
        buckets_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        buckets_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
        folders_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        file_repository: Annotated[FileRepository, Depends(FileRepository)],
        minio_client: Annotated[MinioClient, Depends(MinioClient)],
        email_service: Annotated[YandexSESService, Depends(YandexSESService)],
    ):
        self._users_repository = users_repository
        self._buckets_repository = buckets_repository
        self._buckets_permission_repository = buckets_permission_repository
        self._folders_repository = folders_repository
        self._file_repository = file_repository
        self._minio_client = minio_client
        self._email_service = email_service

    async def _check_bucket_access(self, user_id: UUID, bucket_id: UUID, required_permission: PermissionType) -> Bucket:
        bucket = await self._buckets_repository.get_by_id(bucket_id)
        if not bucket:
            raise NotFound(message='Bucket not found', code='bucket_not_found')

        if bucket.owner_id == user_id:
            return bucket

        if bucket.is_public and required_permission == PermissionType.READ:
            return bucket

        permission = await self._buckets_permission_repository.get_user_permission(user_id, bucket_id)
        if not permission:
            raise PermissionDenied(message='Access denied to this bucket')

        permission_rank = {
            PermissionType.READ: 1,
            PermissionType.WRITE: 2,
            PermissionType.ADMIN: 3,
        }
        required_rank = permission_rank[required_permission]
        actual_rank = permission_rank[permission.permission_type]

        if actual_rank < required_rank:
            raise PermissionDenied(message='Insufficient permissions for this operation')

        return bucket

    async def get_buckets(self, user_id: UUID) -> list[Bucket]:
        buckets = await self._buckets_repository.get_accessible_buckets(user_id)

        for bucket in buckets:
            bucket_id = bucket.id
            if bucket_id is None:
                continue

            if bucket.owner_id == user_id:
                bucket.permission = PermissionType.ADMIN
            else:
                permission = await self._buckets_permission_repository.get_user_permission(bucket_id, user_id)
                if permission:
                    bucket.permission = permission.permission_type
                elif bucket.is_public:
                    bucket.permission = PermissionType.READ
                else:
                    bucket.permission = None

            files_count, size = await self._file_repository.get_bucket_stats(bucket_id)
            bucket.files_count = files_count
            bucket.size = size

        return buckets

    async def create_bucket(self, user_id: UUID, name: str, is_public: bool) -> Bucket:
        minio_bucket_name = f'netvault-{uuid.uuid4()}'

        await self._minio_client.create_bucket(minio_bucket_name)

        bucket = Bucket(
            name=name,
            owner_id=user_id,
            is_public=is_public,
            minio_bucket_name=minio_bucket_name,
        )
        return await self._buckets_repository.create(bucket)

    async def get_bucket(self, user_id: UUID, bucket_id: UUID) -> Bucket:
        return await self._check_bucket_access(user_id, bucket_id, PermissionType.READ)

    async def update_bucket(self, user_id: UUID, bucket_id: UUID, name: str, is_public: bool) -> Bucket:
        bucket = await self._check_bucket_access(user_id, bucket_id, PermissionType.ADMIN)

        bucket.name = name
        bucket.is_public = is_public
        return await self._buckets_repository.update(bucket)

    async def delete_bucket(self, user_id: UUID, bucket_id: UUID) -> None:
        bucket = await self._check_bucket_access(user_id, bucket_id, PermissionType.ADMIN)

        files = await self._file_repository.get_by_bucket(bucket_id)
        total_size = sum(f.file_size_bytes for f in files)

        await self._minio_client.delete_bucket_objects(bucket.minio_bucket_name)

        await self._minio_client.delete_bucket(bucket.minio_bucket_name)

        await self._buckets_repository.delete(bucket_id)

        if total_size > 0:
            owner = await self._users_repository.get_by_id(bucket.owner_id)
            if owner:
                owner.storage_used_bytes -= total_size
                await self._users_repository.update(owner)

    # PERMISSIONS
    async def _get_target_user_id(self, email: str | None, target_user_id: UUID | None) -> User:
        if email and target_user_id:
            raise ClientError(message='Provide either email or user_id, not both', code='invalid_request')

        if email:
            user = await self._users_repository.get_by_email(email)
            if not user:
                raise NotFound(message='User with this email not found', code='user_not_found')
            return user

        if target_user_id:
            user = await self._users_repository.get_by_id(target_user_id)
            if not user:
                raise NotFound(message='User not found', code='user_not_found')
            return user

        raise ClientError(message='Either email or user_id must be provided', code='invalid_request')

    async def _check_target_not_owner(self, bucket: Bucket, target_user_id: UUID) -> None:
        if bucket.owner_id == target_user_id:
            raise ClientError(message='Cannot manage permissions for the bucket owner', code='target_is_owner')

    async def get_bucket_users(self, actor_user_id: UUID, bucket_id: UUID) -> list[UserBrief]:
        bucket = await self._check_bucket_access(actor_user_id, bucket_id, PermissionType.READ)

        user_ids = {bucket.owner_id}

        permission_user_ids = await self._buckets_permission_repository.get_user_ids_by_bucket(bucket_id)
        user_ids.update(permission_user_ids)

        permissions = await self._buckets_permission_repository.get_permissions_by_bucket(bucket_id)
        permissions_map = {p.user_id: p.permission_type for p in permissions}

        users = await self._users_repository.get_by_ids(list(user_ids))

        result = []
        for u in users:
            perm = PermissionType.ADMIN if u.id == bucket.owner_id else permissions_map.get(u.id)

            result.append(
                UserBrief(
                    id=u.id,
                    email=u.email,
                    created_at=u.created_at,
                    last_login_at=u.last_login_at,
                    permission=perm,
                )
            )

        return result

    async def grant_permission(
        self,
        actor_user_id: UUID,
        bucket_id: UUID,
        email: str | None,
        target_user_id: UUID | None,
        permission: PermissionType,
    ) -> BucketPermission:
        actor_user = await self._users_repository.get_by_id(actor_user_id)
        bucket = await self._check_bucket_access(actor_user.id, bucket_id, PermissionType.ADMIN)
        target_user = await self._get_target_user_id(email, target_user_id)

        await self._check_target_not_owner(bucket, target_user.id)

        existing = await self._buckets_permission_repository.get_by_bucket_and_user(bucket_id, target_user.id)
        if existing:
            raise Conflict(message='Permission already exists for this user', code='permission_exists')

        new_permission = BucketPermission(
            bucket_id=bucket_id,
            user_id=target_user.id,
            permission_type=permission,
            granted_by=actor_user.id,
        )
        created = await self._buckets_permission_repository.create(new_permission)

        await self._email_service.send_bucket_permission_changed_email(
            user_email=target_user.email,
            bucket_name=bucket.name,
            permission=permission.value,
            granted_by=actor_user.email,
        )

        return created

    async def update_permission(
        self,
        actor_user_id: UUID,
        bucket_id: UUID,
        email: str | None,
        target_user_id: UUID | None,
        permission: PermissionType,
    ) -> BucketPermission:
        actor_user = await self._users_repository.get_by_id(actor_user_id)
        bucket = await self._check_bucket_access(actor_user.id, bucket_id, PermissionType.ADMIN)
        target_user = await self._get_target_user_id(email, target_user_id)

        await self._check_target_not_owner(bucket, target_user.id)

        existing = await self._buckets_permission_repository.get_by_bucket_and_user(bucket_id, target_user.id)
        if not existing:
            raise NotFound(message='Permission not found for this user', code='permission_not_found')

        existing.permission_type = permission
        updated = await self._buckets_permission_repository.update(existing)

        await self._email_service.send_bucket_permission_changed_email(
            user_email=target_user.email,
            bucket_name=bucket.name,
            permission=permission.value,
            granted_by=actor_user.email,
        )

        return updated

    async def delete_permission(
        self,
        actor_user_id: UUID,
        bucket_id: UUID,
        email: str | None,
        target_user_id: UUID | None,
    ) -> None:
        actor_user = await self._users_repository.get_by_id(actor_user_id)
        bucket = await self._check_bucket_access(actor_user.id, bucket_id, PermissionType.ADMIN)
        target_user = await self._get_target_user_id(email, target_user_id)

        await self._check_target_not_owner(bucket, target_user.id)

        existing = await self._buckets_permission_repository.get_by_bucket_and_user(bucket_id, target_user.id)
        if not existing:
            raise NotFound(message='Permission not found for this user', code='permission_not_found')

        await self._email_service.send_bucket_permission_changed_email(
            user_email=target_user.email,
            bucket_name=bucket.name,
            permission="You haven't permissions now",
            granted_by=actor_user.email,
        )

        await self._buckets_permission_repository.delete(existing.id)
