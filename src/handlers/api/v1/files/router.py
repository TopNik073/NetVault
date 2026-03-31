from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.files.models import (
    GetFileMetadataResponse,
    RenameOrMoveFileRequest,
    RenameOrMoveFileResponse,
    DeleteFileResponse,
    GetDownloadFileResponse,
    GetRecentFilesResponse,
    GetFilesResponse,
    BaseFilesResponse,
)
from src.handlers.dependencies.auth import get_current_user
from src.services.files.service import FilesService

files_router = APIRouter(prefix='/files', tags=['files'])


@files_router.get('/', response_model=GetFilesResponse)
async def get_files(
    service: Annotated[FilesService, Depends(FilesService)],
    user: Annotated[User, Depends(get_current_user)],
    bucket_id: UUID = Query(..., alias='bucketId'),  # noqa: B008
    parent_id: UUID | None = Query(None, alias='parentId'),  # noqa: B008
) -> GetFilesResponse:
    files = await service.get_files(
        user_id=user.id,
        bucket_id=bucket_id,
        folder_id=parent_id,
    )

    return GetFilesResponse.model_validate([BaseFilesResponse.from_file(f) for f in files])


@files_router.get('/recent', response_model=GetRecentFilesResponse)
async def get_recent_files(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FilesService, Depends(FilesService)],
    limit: int = Query(20, ge=1, le=50),
) -> GetRecentFilesResponse:
    files = await service.get_recent_files(
        user_id=user.id,
        limit=limit,
    )
    return GetRecentFilesResponse.model_validate([BaseFilesResponse.from_file(f) for f in files])


@files_router.get('/{fileId}', response_model=GetFileMetadataResponse)
async def get_file_metadata(
    fileId: UUID,
    service: Annotated[FilesService, Depends(FilesService)],
    user: Annotated[User, Depends(get_current_user)],
) -> GetFileMetadataResponse:
    file = await service.get_file_metadata(
        file_id=fileId,
        user_id=user.id,
    )

    return GetFileMetadataResponse.from_file(file)


@files_router.patch('/{fileId}', response_model=RenameOrMoveFileResponse)
async def rename_or_move_file(
    fileId: UUID,
    payload: RenameOrMoveFileRequest,
    service: Annotated[FilesService, Depends(FilesService)],
    user: Annotated[User, Depends(get_current_user)],
) -> RenameOrMoveFileResponse:
    file = await service.rename_or_move_file(
        file_id=fileId,
        user_id=user.id,
        new_name=payload.name,
        new_folder_id=payload.folder_id,
        move_to_root=payload.move_to_root,
    )

    return RenameOrMoveFileResponse.from_file(file)


@files_router.delete('/{fileId}', response_model=DeleteFileResponse)
async def delete_file_metadata(
    fileId: UUID,
    service: Annotated[FilesService, Depends(FilesService)],
    user: Annotated[User, Depends(get_current_user)],
) -> DeleteFileResponse:
    await service.delete_file(file_id=fileId, user_id=user.id)
    return DeleteFileResponse()


@files_router.get('/{fileId}/download', response_model=GetDownloadFileResponse)
async def get_download_link(
    fileId: UUID,
    service: Annotated[FilesService, Depends(FilesService)],
    user: Annotated[User, Depends(get_current_user)],
) -> GetDownloadFileResponse:
    url, expires_at = await service.get_download_link(
        file_id=fileId,
        user_id=user.id,
    )

    return GetDownloadFileResponse(
        downloadUrl=url,
        expiresAt=expires_at,
    )
