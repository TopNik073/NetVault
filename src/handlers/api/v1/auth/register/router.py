from typing import Annotated

from fastapi import APIRouter, Depends

from src.handlers.api.v1.auth.register.models import RegisterResponse, RegisterRequest
from src.services.auth.service import AuthService

register_router = APIRouter(prefix='/register')

@register_router.post('/', response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends()]
) -> RegisterResponse:
    await service.start_registration(
        email=str(payload.email),
        password=payload.password,
    )

    return RegisterResponse()