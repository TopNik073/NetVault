from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlalchemy import String, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import BaseORM, TimestampMixin

if TYPE_CHECKING:
    from src.database.models import BucketORM

class UserORM(BaseORM, TimestampMixin):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    storage_quota_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_reserved_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    owned_buckets: Mapped[list["BucketORM"]] = relationship(back_populates="owner")