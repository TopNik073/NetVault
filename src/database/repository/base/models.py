from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseModelIdentifiable(BaseModel):
    id: UUID | None = None

class PydanticToORMModelMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampedModelMixin(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
