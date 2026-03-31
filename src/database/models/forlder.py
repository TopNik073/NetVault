from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UniqueConstraint, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import BaseORM, TimestampMixin

if TYPE_CHECKING:
    from src.database.models import BucketORM


class FolderORM(BaseORM, TimestampMixin):
    __tablename__ = "folders"
    __table_args__ = (
        UniqueConstraint("bucket_id", "parent_id", "name", name="uq_folder_path"),
    )

    bucket_id: Mapped[UUID] = mapped_column(ForeignKey("buckets.id", ondelete="CASCADE"))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)

    bucket: Mapped["BucketORM"] = relationship(back_populates="folders")
    parent: Mapped["FolderORM"] = relationship(remote_side="FolderORM.id", backref="subfolders")