from uuid import UUID

from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin
from src.database.repository.postgres.bucket_permission.dtos import PermissionType


class Folder(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    bucket_id: UUID
    parent_id: UUID | None
    name: str
    depth: int

    permission: PermissionType | None = None
