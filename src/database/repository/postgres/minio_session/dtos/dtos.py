from datetime import datetime
from uuid import UUID

from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin


class MinioSession(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    user_id: UUID
    bucket_id: UUID
    folder_id: UUID

    operation_type: str
    minio_session_id: str
    object_name: str

    object_size_bytes: int
    reserved_bytes: int

    total_parts: int | None
    completed_parts: int
    status: str

    expires_at: datetime