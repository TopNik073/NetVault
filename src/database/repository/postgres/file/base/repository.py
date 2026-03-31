from abc import ABC

from src.database.models import FileORM
from src.database.repository.postgres.base import BasePostgresRepository
from src.database.repository.postgres.file.dtos import File


class BaseFileRepository(BasePostgresRepository[FileORM, File], ABC):
    _orm_class = FileORM