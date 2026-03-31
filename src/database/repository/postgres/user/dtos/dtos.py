from datetime import datetime

from src.core.config import config
from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin


class User(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    email: str
    password_hash: str | None = None
    storage_quota_bytes: int = config.DEFAULT_STORAGE_QUOTA
    storage_used_bytes: int = 0
    storage_reserved_bytes: int = 0

    last_login_at: datetime | None = None
