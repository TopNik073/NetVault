from uuid import UUID

from sqlalchemy import select

from src.database.models import PublicLinkORM

from src.database.repository.postgres.public_link.base.repository import BasePublicLinkRepository
from src.database.repository.postgres.public_link.dtos import PublicLink


class PublicLinkRepository(BasePublicLinkRepository):
    def orm_to_model(self, orm: PublicLinkORM) -> PublicLink:
        return PublicLink.model_validate(orm)

    def model_to_orm(self, model: PublicLink) -> PublicLinkORM:
        return PublicLinkORM(**model.model_dump())

    async def get_by_file(self, file_id: UUID) -> list[PublicLink]:
        stmt = select(self._orm_class).where(self._orm_class.file_id == file_id)
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]

    async def get_by_folder(self, folder_id: UUID) -> list[PublicLink]:
        stmt = select(self._orm_class).where(self._orm_class.folder_id == folder_id)
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]
