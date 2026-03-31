from uuid import UUID

from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin
from src.database.repository.postgres.bucket_permission.dtos import PermissionType


class File(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    original_filename: str
    storage_filename: str

    path: str

    bucket_id: UUID
    owner_id: UUID
    folder_id: UUID | None = None

    file_size_bytes: int
    mime_type: str | None
    file_hash: str | None

    permission: PermissionType | None = None
