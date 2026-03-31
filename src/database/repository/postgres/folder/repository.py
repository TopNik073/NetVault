from uuid import UUID

from sqlalchemy import select, text, delete

from src.database.models import FolderORM
from src.database.repository.postgres.folder.base.repository import BaseFolderRepository
from src.database.repository.postgres.folder.dtos import Folder


class FolderRepository(BaseFolderRepository):
    def orm_to_model(self, orm: FolderORM) -> Folder:
        return Folder.model_validate(orm)

    def model_to_orm(self, model: Folder) -> FolderORM:
        return FolderORM(**model.model_dump(exclude={'permission'}))

    async def get_by_parent_and_name(self, bucket_id: UUID, parent_id: UUID | None, name: str) -> Folder | None:
        stmt = select(self._orm_class).where(
            self._orm_class.bucket_id == bucket_id,
            self._orm_class.parent_id == parent_id,
            self._orm_class.name == name
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self.orm_to_model(orm) if orm else None

    async def update_subtree_depth(self, root_id: UUID, delta: int) -> None:
        query = text("""
            WITH RECURSIVE subtree AS (
                SELECT id, depth FROM folders WHERE id = :root_id
                UNION ALL
                SELECT f.id, f.depth FROM folders f
                JOIN subtree s ON f.parent_id = s.id
            )
            UPDATE folders SET depth = depth + :delta
            WHERE id IN (SELECT id FROM subtree WHERE id != :root_id)
        """)
        await self._session.execute(query, {"root_id": root_id, "delta": delta})
        await self._session.commit()

    async def is_descendant(self, folder_id: UUID, ancestor_id: UUID) -> bool:
        """Возвращает True, если folder_id является потомком ancestor_id."""
        query = text("""
            WITH RECURSIVE ancestors AS (
                SELECT id, parent_id FROM folders WHERE id = :folder_id
                UNION ALL
                SELECT f.id, f.parent_id FROM folders f
                JOIN ancestors a ON f.id = a.parent_id
            )
            SELECT id FROM ancestors WHERE id = :ancestor_id
        """)
        result = await self._session.execute(query, {"folder_id": folder_id, "ancestor_id": ancestor_id})
        return result.scalar_one_or_none() is not None

    async def get_subtree_ids(self, root_id: UUID) -> list[UUID]:
        query = text("""
            WITH RECURSIVE subtree AS (
                SELECT id FROM folders WHERE id = :root_id
                UNION ALL
                SELECT f.id FROM folders f
                INNER JOIN subtree s ON f.parent_id = s.id
            )
            SELECT id FROM subtree
        """)
        result = await self._session.execute(query, {"root_id": root_id})
        rows = result.fetchall()
        return [row[0] for row in rows]

    async def delete_many(self, ids: list[UUID]) -> None:
        if not ids:
            return
        stmt = delete(self._orm_class).where(self._orm_class.id.in_(ids))
        await self._session.execute(stmt)

    async def search_by_name(self, bucket_ids: list[UUID], query: str) -> list[Folder]:
        stmt = select(self._orm_class).where(
            self._orm_class.bucket_id.in_(bucket_ids),
            self._orm_class.name.ilike(f"%{query}%")
        )
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def get_by_bucket_and_parent(
            self, bucket_id: UUID, parent_id: UUID | None
    ) -> list[Folder]:
        stmt = select(self._orm_class).where(
            self._orm_class.bucket_id == bucket_id,
            self._orm_class.parent_id == parent_id
        ).order_by(self._orm_class.name)
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]