from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, RootModel

from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.database.repository.postgres.file.dtos import File


class BaseFilesResponse(BaseModel):
    id: UUID
    name: str
    bucketId: UUID
    folderId: UUID | None
    size: int
    mimeType: str
    uploadedAt: datetime
    permission: PermissionType | None = None

    @classmethod
    def from_file(cls, file: File) -> 'BaseFilesResponse':
        return cls(
            id=file.id,
            name=file.original_filename,
            bucketId=file.bucket_id,
            folderId=file.folder_id,
            size=file.file_size_bytes,
            mimeType=file.mime_type or 'application/octet-stream',
            uploadedAt=file.created_at,
            permission=file.permission,
        )


class GetFilesResponse(RootModel[list[BaseFilesResponse]]):
    pass


class GetFileMetadataResponse(BaseFilesResponse):
    pass


class RenameOrMoveFileRequest(BaseModel):
    name: str | None = None
    folderId: str | None = None

    @property
    def folder_id(self) -> UUID | None:
        if self.folderId is not None and self.folderId != '':
            return UUID(self.folderId)
        return None

    @property
    def move_to_root(self) -> bool:
        return self.folderId == ''


class RenameOrMoveFileResponse(BaseFilesResponse):
    pass


class DeleteFileResponse(BaseModel):
    pass


class GetRecentFilesResponse(RootModel[list[BaseFilesResponse]]):
    pass


class GetDownloadFileResponse(BaseModel):
    downloadUrl: str
    expiresAt: datetime
