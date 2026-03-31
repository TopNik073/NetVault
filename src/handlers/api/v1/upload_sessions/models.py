from typing import Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class InitUploadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    bucket_id: UUID = Field(..., alias="bucketId")
    folder_id: UUID | None = Field(None, alias="folderId")
    name: str = Field(..., min_length=1, max_length=255)
    size: int = Field(..., ge=1, description="File size in bytes")
    mime_type: str = Field(..., alias="mimeType")


class SimpleUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    session_id: UUID = Field(..., alias="sessionId")
    upload_type: Literal["simple"] = Field(..., alias="uploadType")
    upload_url: str = Field(..., alias="uploadUrl")
    expires_at: datetime = Field(..., alias="expiresAt")


class MultipartUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    session_id: UUID = Field(..., alias="sessionId")
    upload_type: Literal["multipart"] = Field(..., alias="uploadType")
    part_urls: dict[int, str] = Field(..., alias="partUrls")
    chunk_size: int = Field(..., alias="chunkSize")
    total_parts: int = Field(..., alias="totalParts")
    expires_at: datetime = Field(..., alias="expiresAt")


InitUploadResponse = SimpleUploadResponse | MultipartUploadResponse


class PartCompleteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    part_number: int = Field(..., alias="partNumber", ge=1)
    etag: str = Field(..., min_length=1)

class PartCompleteResponse(BaseModel):
    status: Literal['ok'] = 'ok'

class UploadStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    session_id: UUID = Field(..., alias="sessionId")
    upload_type: Literal["simple", "multipart"] = Field(..., alias="uploadType")
    status: Literal["pending", "active", "completed", "aborted"]
    completed_parts: int | None = Field(None, alias="completedParts")
    total_parts: int | None = Field(None, alias="totalParts")
    expires_at: datetime = Field(..., alias="expiresAt")


class CompleteUploadResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=False,
        from_attributes=True,
    )

    file_id: UUID = Field(..., alias="fileId")
    name: str
    size: int
    mime_type: str = Field(..., alias="mimeType")
    bucket_id: UUID = Field(..., alias="bucketId")
    folder_id: UUID | None = Field(None, alias="folderId")
    uploaded_at: datetime = Field(..., alias="uploadedAt")


class AbortUploadResponse(BaseModel):
    pass