from uuid import UUID

from sqlalchemy import select, delete, func

from src.database.models import FileORM

from src.database.repository.postgres.file.base.repository import BaseFileRepository
from src.database.repository.postgres.file.dtos import File


class FileRepository(BaseFileRepository):
    def orm_to_model(self, orm: FileORM) -> File:
        return File.model_validate(orm)

    def model_to_orm(self, model: File) -> FileORM:
        return FileORM(**model.model_dump(exclude={'permission'}))

    async def get_by_bucket_and_parent_and_name(
        self, bucket_id: UUID, folder_id: UUID | None, name: str
    ) -> File | None:
        stmt = select(self._orm_class).where(
            self._orm_class.bucket_id == bucket_id,
            self._orm_class.folder_id == folder_id,
            self._orm_class.original_filename == name,
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self.orm_to_model(orm) if orm else None

    async def get_recent_by_owner(self, owner_id: UUID, limit: int) -> list[File]:
        stmt = (
            select(self._orm_class)
            .where(self._orm_class.owner_id == owner_id)
            .order_by(self._orm_class.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def search_by_name(self, bucket_ids: list[UUID], query: str) -> list[File]:
        stmt = select(self._orm_class).where(
            self._orm_class.bucket_id.in_(bucket_ids), self._orm_class.original_filename.ilike(f'%{query}%')
        )
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def get_by_bucket_and_folder(self, bucket_id: UUID, folder_id: UUID | None) -> list[File]:
        stmt = (
            select(self._orm_class)
            .where(self._orm_class.bucket_id == bucket_id, self._orm_class.folder_id == folder_id)
            .order_by(self._orm_class.original_filename)
        )
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def get_by_folder_ids(self, folder_ids: list[UUID]) -> list[File]:
        stmt = select(self._orm_class).where(self._orm_class.folder_id.in_(folder_ids))
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def delete_many(self, file_ids: list[UUID]) -> None:
        if not file_ids:
            return
        stmt = delete(self._orm_class).where(self._orm_class.id.in_(file_ids))
        await self._session.execute(stmt)

    async def get_bucket_stats(self, bucket_id: UUID) -> tuple[int, int]:
        stmt = select(
            func.count(self._orm_class.id), func.coalesce(func.sum(self._orm_class.file_size_bytes), 0)
        ).where(self._orm_class.bucket_id == bucket_id)
        result = await self._session.execute(stmt)
        row = result.one()
        return int(row[0]), int(row[1] or 0)

    async def get_buckets_stats(self, bucket_ids: list[UUID]) -> dict[UUID, tuple[int, int]]:
        if not bucket_ids:
            return {}
        stmt = (
            select(
                self._orm_class.bucket_id,
                func.count(self._orm_class.id),
                func.coalesce(func.sum(self._orm_class.file_size_bytes), 0),
            )
            .where(self._orm_class.bucket_id.in_(bucket_ids))
            .group_by(self._orm_class.bucket_id)
        )
        result = await self._session.execute(stmt)
        return {row[0]: (int(row[1]), int(row[2] or 0)) for row in result}
