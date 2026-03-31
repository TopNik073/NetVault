from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BaseBucketsResponse(BaseModel):
    id: UUID
    name: str
    is_public: bool = Field(..., alias='isPublic')
    files_count: int = Field(0, alias='filesCount')
    size: int = Field(0, alias='size')


class BaseFolderResponse(BaseModel):
    id: UUID
    name: str
    depth: int
    bucket_id: UUID = Field(..., alias='bucketId')
    parent_id: UUID | None = Field(..., alias='parentId')


class BaseFilesResponse(BaseModel):
    id: UUID
    name: str

    bucket_id: str = Field(..., alias='bucketId')
    folder_id: str = Field(..., alias='folderId')

    size: int
    mime_type: str = Field(..., alias='mimeType')
    uploaded_at: datetime = Field(..., alias='uploadedAt')


class SearchResponse(BaseModel):
    buckets: list[BaseBucketsResponse]
    folders: list[BaseFolderResponse]
    files: list[BaseFilesResponse]
