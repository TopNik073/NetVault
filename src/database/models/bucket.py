from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint, String, UUID, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import BaseORM, TimestampMixin

if TYPE_CHECKING:
    from src.database.models import UserORM
    from src.database.models import FolderORM
    from src.database.models import FileORM

class BucketORM(BaseORM, TimestampMixin):
    __tablename__ = "buckets"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_bucket_owner_name"),
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    minio_bucket_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    owner: Mapped["UserORM"] = relationship(back_populates="owned_buckets")
    folders: Mapped[list["FolderORM"]] = relationship(back_populates="bucket")
    files: Mapped[list["FileORM"]] = relationship(back_populates="bucket")