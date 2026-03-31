from abc import ABC

from src.database.models import MinioSessionORM
from src.database.repository.postgres.base import BasePostgresRepository
from src.database.repository.postgres.minio_session.dtos import MinioSession


class BaseMinioSessionRepository(BasePostgresRepository[MinioSessionORM, MinioSession], ABC):
    _orm_class = MinioSessionORM
