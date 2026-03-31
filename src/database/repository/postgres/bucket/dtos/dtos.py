from uuid import UUID

from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin
from src.database.repository.postgres.bucket_permission.dtos import PermissionType


class Bucket(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    name: str
    owner_id: UUID
    is_public: bool
    minio_bucket_name: str
    permission: PermissionType | None = None
    files_count: int = 0
    size: int = 0
