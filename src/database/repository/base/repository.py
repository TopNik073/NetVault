from abc import ABC, abstractmethod
from uuid import UUID


class BaseRepository[ORMType, ModelType](ABC):
    @abstractmethod
    async def get_by_id(self, _id: UUID) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def get_many(self, limit: int | None = None) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, entity: ModelType) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: ModelType) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, _id: UUID) -> bool:
        raise NotImplementedError
