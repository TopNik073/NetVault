from datetime import datetime
from uuid import UUID

from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin


class PublicLink(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    file_id: UUID | None
    folder_id: UUID | None
    expires_at: datetime | None = None
    max_downloads: int | None = None
    downloads_count: int = 0
