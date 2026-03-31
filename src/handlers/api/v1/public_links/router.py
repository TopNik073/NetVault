from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError

from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.public_links.models import (
    CreatePublicLinkResponse,
    CreatePublicLinkRequest,
    PublicLinkListResponse,
    PublicLinkDetailResponse,
    DeletePublicLinkResponse,
    PublicDownloadInfoResponse,
)
from src.handlers.dependencies.auth import get_current_user
from src.services.public_link.service import PublicLinkService

public_links_router = APIRouter(prefix='/public-links', tags=['public-links'])


@public_links_router.post('', response_model=CreatePublicLinkResponse)
async def create_public_link(
    payload: CreatePublicLinkRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PublicLinkService, Depends(PublicLinkService)],
) -> CreatePublicLinkResponse:
    link = await service.create_link_with_url(
        actor_user_id=user.id,
        file_id=payload.file_id,
        folder_id=payload.folder_id,
        expires_in_seconds=payload.expires_in_seconds,
        max_downloads=payload.max_downloads,
    )
    return CreatePublicLinkResponse(**link)


@public_links_router.get('', response_model=PublicLinkListResponse)
async def list_public_links(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PublicLinkService, Depends(PublicLinkService)],
    file_id: UUID | None = Query(None, alias='fileId'),  # noqa: B008
    folder_id: UUID | None = Query(None, alias='folderId'),  # noqa: B008
) -> PublicLinkListResponse:
    if (file_id is None) == (folder_id is None):
        raise ValidationError('Exactly one of file_id or folder_id must be provided')

    links = await service.list_links_with_urls(
        actor_user_id=user.id,
        file_id=file_id,
        folder_id=folder_id,
    )
    return PublicLinkListResponse(links)


@public_links_router.get('/{link_id}', response_model=PublicLinkDetailResponse)
async def get_public_link(
    link_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PublicLinkService, Depends(PublicLinkService)],
) -> PublicLinkDetailResponse:
    link = await service.get_link_with_url(actor_user_id=user.id, link_id=link_id)
    return PublicLinkDetailResponse(**link)


@public_links_router.delete('/{link_id}', response_model=DeletePublicLinkResponse)
async def delete_public_link(
    link_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PublicLinkService, Depends(PublicLinkService)],
) -> DeletePublicLinkResponse:
    await service.delete_link(actor_user_id=user.id, link_id=link_id)
    return DeletePublicLinkResponse()


@public_links_router.get('/{link_id}/info', response_model=PublicDownloadInfoResponse)
async def get_public_link_info(
    link_id: UUID,
    service: Annotated[PublicLinkService, Depends(PublicLinkService)],
):
    return await service.get_public_link_info(link_id)


@public_links_router.get('/{link_id}/download')
async def get_public_download_url(
    link_id: UUID,
    service: Annotated[PublicLinkService, Depends(PublicLinkService)],
):
    url = await service.get_public_download_url(link_id)
    return {'url': url}
