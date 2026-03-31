from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, DateTime, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import BaseORM, TimestampMixin


class PublicLinkORM(BaseORM, TimestampMixin):
    __tablename__ = "public_links"

    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
    )
    folder_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_downloads: Mapped[int | None] = mapped_column(Integer)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        CheckConstraint(
            "(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)",
            name="ck_public_links_one_target"
        ),
    )