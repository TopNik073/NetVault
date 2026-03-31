from typing import Annotated

from fastapi import APIRouter, Depends

from src.handlers.api.v1.auth.reset_password.models import RestorePasswordResponse, RestorePasswordRequest
from src.services.auth.service import AuthService

reset_password_router = APIRouter(prefix='/restore')

@reset_password_router.post('/', response_model=RestorePasswordResponse)
async def restore(
    payload: RestorePasswordRequest,
    service: Annotated[AuthService, Depends()]
) -> RestorePasswordResponse:
    await service.start_password_reset(
        email=str(payload.email),
        new_password=payload.new_password,
    )

    return RestorePasswordResponse()