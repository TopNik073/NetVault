from abc import ABC, abstractmethod
from uuid import UUID

from src.database.models import UserORM
from src.database.repository.postgres.base.postgres_repository import BasePostgresRepository
from src.database.repository.postgres.user.dtos.dtos import User


class BaseUserRepository(BasePostgresRepository[UserORM, User], ABC):
    _orm_class = UserORM

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(self, user_ids: list[UUID]) -> list[User]:
        raise NotImplementedError
