from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UniqueConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import BaseORM, TimestampMixin

if TYPE_CHECKING:
    from src.database.models import BucketORM
    from src.database.models import UserORM

class BucketPermissionORM(BaseORM, TimestampMixin):
    __tablename__ = "bucket_permissions"
    __table_args__ = (
        UniqueConstraint("bucket_id", "user_id", name="uq_bucket_user_permission"),
    )

    bucket_id: Mapped[UUID] = mapped_column(ForeignKey("buckets.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    permission_type: Mapped[str] = mapped_column(String) # read, write, admin
    granted_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    bucket: Mapped["BucketORM"] = relationship()
    user: Mapped["UserORM"] = relationship(foreign_keys=[user_id])