from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, BigInteger, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import BaseORM, TimestampMixin


class MinioSessionORM(BaseORM, TimestampMixin):
    __tablename__ = "minio_sessions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    bucket_id: Mapped[UUID] = mapped_column(ForeignKey("buckets.id"))
    folder_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("folders.id"),
        nullable=True,
    )

    operation_type: Mapped[str] = mapped_column(String)
    minio_session_id: Mapped[str] = mapped_column(String)
    object_name: Mapped[str] = mapped_column(String)

    object_size_bytes: Mapped[int] = mapped_column(BigInteger)
    reserved_bytes: Mapped[int] = mapped_column(BigInteger)

    total_parts: Mapped[int | None] = mapped_column(Integer)
    completed_parts: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="active")

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))