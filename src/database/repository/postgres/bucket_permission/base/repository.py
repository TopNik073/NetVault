from abc import ABC, abstractmethod
from uuid import UUID

from src.database.models import BucketPermissionORM
from src.database.repository.postgres.base import BasePostgresRepository
from src.database.repository.postgres.bucket_permission.dtos import BucketPermission


class BaseBucketPermissionRepository(BasePostgresRepository[BucketPermissionORM, BucketPermission], ABC):
    _orm_class = BucketPermissionORM

    @abstractmethod
    async def get_user_permission(self, bucket_id: UUID, user_id: UUID) -> BucketPermission | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_bucket_and_user(self, bucket_id: UUID, user_id: UUID) -> BucketPermission | None:
        raise NotImplementedError

    @abstractmethod
    async def get_user_ids_by_bucket(self, bucket_id: UUID) -> list[UUID]:
        raise NotImplementedError