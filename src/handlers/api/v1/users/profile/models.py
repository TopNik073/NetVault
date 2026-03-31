from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ProfileResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    email: EmailStr

    storage_quota_bytes: int = Field(..., alias='storageQuotaBytes')
    storage_used_bytes: int = Field(..., alias='storageUsedBytes')
    storage_reserved_bytes: int = Field(..., alias='storageReservedBytes')

    created_at: datetime = Field(..., alias='createdAt')
    last_login_at: datetime = Field(..., alias='lastLoginAt')
