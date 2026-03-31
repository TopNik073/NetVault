from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict

from src.database.repository.base import BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin


class PermissionType(StrEnum):
    READ = 'read'
    WRITE = 'write'
    ADMIN = 'admin'

class BucketPermission(BaseModelIdentifiable, PydanticToORMModelMixin, TimestampedModelMixin):
    model_config = ConfigDict(use_enum_values=True)

    bucket_id: UUID
    user_id: UUID
    permission_type: PermissionType
    granted_by: UUID