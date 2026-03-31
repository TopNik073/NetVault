from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator, RootModel

SECONDS_IN_MONTH = 2_592_000


class BasePublicLinkResponse(BaseModel):
    id: UUID
    url: str | None = Field(None, alias='url')
    file_id: UUID | None = Field(None, alias='fileId')
    folder_id: UUID | None = Field(None, alias='folderId')
    expires_at: datetime | None = Field(None, alias='expiresAt')
    max_downloads: int | None = Field(None, alias='maxDownloads')
    downloads_count: int = Field(..., alias='downloadsCount')
    created_at: datetime = Field(..., alias='createdAt')
    updated_at: datetime = Field(..., alias='updatedAt')

    class Config:
        from_attributes = True
        populate_by_name = True


class CreatePublicLinkRequest(BaseModel):
    file_id: UUID | None = Field(None, alias='fileId')
    folder_id: UUID | None = Field(None, alias='folderId')
    expires_in_seconds: int | None = Field(None, alias='expiresInSeconds', ge=60, le=SECONDS_IN_MONTH)
    max_downloads: int | None = Field(None, alias='maxDownloads', ge=1, le=1000)

    @model_validator(mode='after')
    def check_one_resource(self):
        if (self.file_id is None) == (self.folder_id is None):
            raise ValueError('Exactly one of file_id or folder_id must be provided')
        return self


class CreatePublicLinkResponse(BasePublicLinkResponse):
    pass


class PublicLinkListResponse(RootModel[list[BasePublicLinkResponse]]):
    pass


class PublicLinkDetailResponse(BasePublicLinkResponse):
    pass


class DeletePublicLinkResponse(BaseModel):
    pass


class PublicDownloadInfoResponse(BaseModel):
    id: UUID
    file_name: str | None = Field(None, alias='fileName')
    downloads_count: int = Field(..., alias='downloadsCount')
    max_downloads: int | None = Field(None, alias='maxDownloads')
    expires_at: datetime | None = Field(None, alias='expiresAt')
