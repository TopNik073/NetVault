from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.folders.models import (
    GetFolderInfoResponse,
    CreateFolderResponse,
    CreateFolderRequest,
    RenameFolderResponse,
    RenameFolderRequest,
    MoveFolderResponse,
    MoveFolderRequest,
    DeleteFolderResponse,
    GetFoldersResponse,
    BaseFolderResponse,
)
from src.handlers.dependencies.auth import get_current_user
from src.services.folders.service import FoldersService

folders_router = APIRouter(prefix='/folders', tags=['folders'])


@folders_router.get('/', response_model=GetFoldersResponse)
async def get_folders(
    service: Annotated[FoldersService, Depends(FoldersService)],
    user: Annotated[User, Depends(get_current_user)],
    bucket_id: UUID = Query(..., alias='bucketId'),  # noqa: B008
    parent_id: UUID | None = Query(None, alias='parentId'),  # noqa: B008
) -> GetFoldersResponse:
    folders = await service.get_folders(
        user_id=user.id,
        bucket_id=bucket_id,
        parent_id=parent_id,
    )

    return GetFoldersResponse.model_validate([BaseFolderResponse.from_folder(f) for f in folders])


@folders_router.get('/{folderId}', response_model=GetFolderInfoResponse)
async def get_folder_info(
    folderId: UUID,
    service: Annotated[FoldersService, Depends(FoldersService)],
    user: Annotated[User, Depends(get_current_user)],
) -> GetFolderInfoResponse:
    folder = await service.get_folder_info(
        folder_id=folderId,
        user_id=user.id,
    )

    return GetFolderInfoResponse.from_folder(folder)


@folders_router.post('/', response_model=CreateFolderResponse)
async def create_folder(
    payload: CreateFolderRequest,
    service: Annotated[FoldersService, Depends(FoldersService)],
    user: Annotated[User, Depends(get_current_user)],
) -> CreateFolderResponse:
    folder = await service.create_folder(
        name=payload.name, bucket_id=payload.bucketId, parent_id=payload.parentId, user_id=user.id
    )

    return CreateFolderResponse.from_folder(folder)


@folders_router.patch('/{folderId}', response_model=RenameFolderResponse)
async def rename_folder(
    folderId: UUID,
    payload: RenameFolderRequest,
    service: Annotated[FoldersService, Depends(FoldersService)],
    user: Annotated[User, Depends(get_current_user)],
) -> RenameFolderResponse:
    folder = await service.rename_folder(
        folder_id=folderId,
        new_name=payload.name,
        user_id=user.id,
    )

    return RenameFolderResponse.from_folder(folder)


@folders_router.post('/{folderId}/move', response_model=MoveFolderResponse)
async def move_folder(
    folderId: UUID,
    payload: MoveFolderRequest,
    service: Annotated[FoldersService, Depends(FoldersService)],
    user: Annotated[User, Depends(get_current_user)],
) -> MoveFolderResponse:
    folder = await service.move_folder(
        folder_id=folderId,
        new_parent_id=payload.parentId,
        user_id=user.id,
    )

    return MoveFolderResponse.from_folder(folder)


@folders_router.delete('/{folderId}', response_model=DeleteFolderResponse)
async def delete_folder(
    folderId: UUID,
    service: Annotated[FoldersService, Depends(FoldersService)],
    user: Annotated[User, Depends(get_current_user)],
) -> DeleteFolderResponse:
    await service.delete_folder(folder_id=folderId, user_id=user.id)

    return DeleteFolderResponse()
