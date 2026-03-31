from src.database.models import MinioSessionORM

from src.database.repository.postgres.minio_session.base.repository import BaseMinioSessionRepository
from src.database.repository.postgres.minio_session.dtos import MinioSession


class MinioSessionRepository(BaseMinioSessionRepository):
    def orm_to_model(self, orm: MinioSessionORM) -> MinioSession:
        return MinioSession.model_validate(orm)

    def model_to_orm(self, model: MinioSession) -> MinioSessionORM:
        return MinioSessionORM(**model.model_dump())
