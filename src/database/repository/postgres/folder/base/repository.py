from abc import ABC, abstractmethod
from uuid import UUID

from src.database.models import FolderORM
from src.database.repository.postgres.base import BasePostgresRepository
from src.database.repository.postgres.folder.dtos import Folder


class BaseFolderRepository(BasePostgresRepository[FolderORM, Folder], ABC):
    _orm_class = FolderORM

    @abstractmethod
    async def get_by_parent_and_name(self, bucket_id: UUID, parent_id: UUID | None, name: str) -> Folder | None:
        raise NotImplementedError

    @abstractmethod
    async def update_subtree_depth(self, root_id: UUID, delta: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_descendant(self, folder_id: UUID, ancestor_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_subtree_ids(self, root_id: UUID) -> list[UUID]:
        raise NotImplementedError

    @abstractmethod
    async def delete_many(self, ids: list[UUID]) -> None:
        raise NotImplementedError
