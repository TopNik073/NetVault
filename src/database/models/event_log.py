from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import BaseORM, TimestampMixin


class EventLogORM(BaseORM, TimestampMixin):
    __tablename__ = "event_log"

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[UUID | None] = mapped_column(PG_UUID)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
