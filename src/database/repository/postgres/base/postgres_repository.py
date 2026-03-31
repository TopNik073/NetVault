from abc import ABC, abstractmethod
from typing import TypeVar, Annotated
from uuid import UUID

from fastapi.params import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models.base import BaseORM
from src.database.repository.base.models import BaseModelIdentifiable
from src.database.repository.base.repository import BaseRepository
from src.database.repository.postgres.errors import BasePostgresError

ORMType = TypeVar('ORMType', bound=BaseORM)
ModelType = TypeVar('ModelType', bound=BaseModelIdentifiable)


class BasePostgresRepository(
    BaseRepository[ORMType, ModelType],
    ABC,
):
    _orm_class: type[ORMType]

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> None:
        self._session = session

    @abstractmethod
    def orm_to_model(self, orm: ORMType) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def model_to_orm(self, model: ModelType) -> ORMType:
        raise NotImplementedError

    async def get_by_id(self, _id: UUID) -> ModelType | None:
        orm = await self._session.get(self._orm_class, _id)
        if orm is None:
            return None
        return self.orm_to_model(orm)

    async def get_many(self, limit: int | None = None) -> list[ModelType]:
        stmt = select(self._orm_class)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return [self.orm_to_model(orm) for orm in result.scalars().all() if orm is not None]

    async def create(self, entity: ModelType) -> ModelType:
        orm = self.model_to_orm(entity)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return self.orm_to_model(orm)

    async def update(self, entity: ModelType) -> ModelType:
        orm = await self._session.get(self._orm_class, entity.id)

        if orm is None:
            msg: str = f'Entity with id {entity.id} not found'
            raise BasePostgresError(msg)

        updated_orm = self.model_to_orm(entity)
        data = updated_orm.__dict__.copy()
        data.pop('id', None)
        data.pop('_sa_instance_state', None)

        for field, value in data.items():
            if not field.startswith('_'):
                setattr(orm, field, value)

        await self._session.commit()
        await self._session.refresh(orm)

        return self.orm_to_model(orm)

    async def delete(self, _id: UUID) -> bool:
        query = delete(self._orm_class).where(self._orm_class.id == _id)
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount > 0  # type: ignore[attr-defined]
