from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UniqueConstraint, ForeignKey, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import BaseORM, TimestampMixin

if TYPE_CHECKING:
    from src.database.models import BucketORM
    from src.database.models import FolderORM
    from src.database.models import UserORM

class FileORM(BaseORM, TimestampMixin):
    __tablename__ = "files"
    __table_args__ = (
        UniqueConstraint("bucket_id", "storage_filename", name="uq_file_storage_name"),
    )

    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    storage_filename: Mapped[str] = mapped_column(String, nullable=False)

    path: Mapped[str] = mapped_column(String, nullable=False)

    bucket_id: Mapped[UUID] = mapped_column(ForeignKey("buckets.id"))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    folder_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("folders.id"),
        nullable=True,
    )

    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String)
    file_hash: Mapped[str | None] = mapped_column(String)

    bucket: Mapped["BucketORM"] = relationship(back_populates="files")
    folder: Mapped["FolderORM"] = relationship()
    owner: Mapped["UserORM"] = relationship()