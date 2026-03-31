from uuid import UUID

from sqlalchemy import select

from src.database.models import UserORM
from src.database.repository.postgres.user.base import BaseUserRepository
from src.database.repository.postgres.user.dtos import User


class UserRepository(BaseUserRepository):
    def orm_to_model(self, orm: UserORM) -> User:
        return User.model_validate(orm)

    def model_to_orm(self, model: User) -> UserORM:
        return UserORM(**model.model_dump())

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(self._orm_class).where(UserORM.email == email)

        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None

        return self.orm_to_model(user)

    async def get_by_ids(self, user_ids: list[UUID]) -> list[User]:
        stmt = select(self._orm_class).where(self._orm_class.id.in_(user_ids))
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self.orm_to_model(orm) for orm in orms]