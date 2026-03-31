from abc import ABC

from src.database.models import PublicLinkORM
from src.database.repository.postgres.base import BasePostgresRepository
from src.database.repository.postgres.public_link.dtos import PublicLink


class BasePublicLinkRepository(BasePostgresRepository[PublicLinkORM, PublicLink], ABC):
    _orm_class = PublicLinkORM
