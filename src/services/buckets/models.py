from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.database.repository.postgres.bucket_permission.dtos import PermissionType


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime
    last_login_at: datetime | None = None
    permission: PermissionType | None = None
