from abc import ABC

from src.database.models import BucketORM
from src.database.repository.postgres.base import BasePostgresRepository
from src.database.repository.postgres.bucket.dtos import Bucket


class BaseBucketRepository(BasePostgresRepository[BucketORM, Bucket], ABC):
    _orm_class = BucketORM