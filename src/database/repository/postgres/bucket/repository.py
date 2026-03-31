from uuid import UUID

from sqlalchemy import select, or_

from src.database.models import BucketORM, BucketPermissionORM

from src.database.repository.postgres.bucket.base.repository import BaseBucketRepository
from src.database.repository.postgres.bucket.dtos import Bucket


class BucketRepository(BaseBucketRepository):
    def orm_to_model(self, orm: BucketORM) -> Bucket:
        return Bucket.model_validate(orm)

    def model_to_orm(self, model: Bucket) -> BucketORM:
        return BucketORM(**model.model_dump(exclude={'permission', 'files_count', 'size'}))

    async def update(self, entity: Bucket) -> Bucket:
        orm = await self._session.get(self._orm_class, entity.id)

        if orm is None:
            raise ValueError(f'Entity with id {entity.id} not found')

        orm.name = entity.name
        orm.is_public = entity.is_public
        orm.minio_bucket_name = entity.minio_bucket_name

        await self._session.commit()
        await self._session.refresh(orm)

        return self.orm_to_model(orm)

    async def get_accessible_buckets(self, user_id: UUID) -> list[Bucket]:
        stmt = (
            select(BucketORM)
            .outerjoin(
                BucketPermissionORM,
                (BucketPermissionORM.bucket_id == BucketORM.id) & (BucketPermissionORM.user_id == user_id),
            )
            .where(
                or_(BucketORM.owner_id == user_id, BucketPermissionORM.user_id == user_id, BucketORM.is_public == True)
            )
            .distinct()
        )

        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def search_by_name(self, bucket_ids: list[UUID], query: str) -> list[Bucket]:
        stmt = select(self._orm_class).where(
            self._orm_class.id.in_(bucket_ids), self._orm_class.name.ilike(f'%{query}%')
        )
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]
