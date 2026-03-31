from typing import Annotated

from fastapi import APIRouter, Depends

from src.handlers.api.v1.auth.login.models import LoginRequest, LoginResponse
from src.services.auth.service import AuthService

login_router = APIRouter(prefix='/login')

@login_router.post('/', response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends()],
) -> LoginResponse:
    await service.start_login(
        email=str(payload.email),
        password=payload.password,
    )

    return LoginResponse()