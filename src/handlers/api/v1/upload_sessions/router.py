from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends


from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.upload_sessions.models import (
    InitUploadRequest,
    InitUploadResponse,
    PartCompleteRequest,
    UploadStatusResponse,
    CompleteUploadResponse,
    AbortUploadResponse, PartCompleteResponse,
)
from src.handlers.dependencies.auth import get_current_user
from src.services.upload_sessions.service import UploadSessionsService

upload_sessions_router = APIRouter(prefix="/upload-sessions", tags=["upload"])


@upload_sessions_router.post("/init", response_model=InitUploadResponse)
async def init_upload(
    payload: InitUploadRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UploadSessionsService, Depends(UploadSessionsService)],
) -> InitUploadResponse:
    return await service.init_upload(
        actor_user_id=user.id,
        bucket_id=payload.bucket_id,
        folder_id=payload.folder_id,
        name=payload.name,
        size=payload.size,
        mime_type=payload.mime_type,
    )


@upload_sessions_router.post("/{session_id}/parts", response_model=PartCompleteResponse)
async def complete_part(
    session_id: UUID,
    payload: PartCompleteRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UploadSessionsService, Depends(UploadSessionsService)],
) -> PartCompleteResponse:
    await service.complete_part(
        actor_user_id=user.id,
        session_id=session_id,
        part_number=payload.part_number,
        etag=payload.etag,
    )
    return PartCompleteResponse()


@upload_sessions_router.get("/{session_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    session_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UploadSessionsService, Depends(UploadSessionsService)],
) -> UploadStatusResponse:
    return await service.get_upload_status(actor_user_id=user.id, session_id=session_id)


@upload_sessions_router.post("/{session_id}/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    session_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UploadSessionsService, Depends(UploadSessionsService)],
) -> CompleteUploadResponse:
    return await service.complete_upload(actor_user_id=user.id, session_id=session_id)


@upload_sessions_router.delete("/{session_id}", response_model=AbortUploadResponse)
async def abort_upload(
    session_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UploadSessionsService, Depends(UploadSessionsService)],
) -> AbortUploadResponse:
    await service.abort_upload(actor_user_id=user.id, session_id=session_id)
    return AbortUploadResponse()