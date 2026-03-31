from uuid import UUID

from sqlalchemy import select

from src.database.models import BucketPermissionORM

from src.database.repository.postgres.bucket_permission.base.repository import BaseBucketPermissionRepository
from src.database.repository.postgres.bucket_permission.dtos import BucketPermission


class BucketPermissionRepository(BaseBucketPermissionRepository):
    def orm_to_model(self, orm: BucketPermissionORM) -> BucketPermission:
        return BucketPermission.model_validate(orm)

    def model_to_orm(self, model: BucketPermission) -> BucketPermissionORM:
        return BucketPermissionORM(**model.model_dump())

    async def get_user_permission(self, bucket_id: UUID, user_id: UUID) -> BucketPermission | None:
        stmt = select(self._orm_class).where(
            BucketPermissionORM.bucket_id == bucket_id, BucketPermissionORM.user_id == user_id
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm:
            return self.orm_to_model(orm)
        return None

    async def get_by_bucket_and_user(self, bucket_id: UUID, user_id: UUID) -> BucketPermission | None:
        stmt = select(self._orm_class).where(self._orm_class.bucket_id == bucket_id, self._orm_class.user_id == user_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm:
            return self.orm_to_model(orm)
        return None

    async def get_user_ids_by_bucket(self, bucket_id: UUID) -> list[UUID]:
        stmt = select(self._orm_class.user_id).where(self._orm_class.bucket_id == bucket_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_permissions_by_bucket(self, bucket_id: UUID) -> list[BucketPermission]:
        stmt = select(self._orm_class).where(self._orm_class.bucket_id == bucket_id)
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]
