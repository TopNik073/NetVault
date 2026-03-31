from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from src.handlers.api.v1.auth.two_fa_auth.models import TwoFaRequest, TwoFaResponse
from src.services.auth.service import AuthService

two_fa_router = APIRouter(prefix='/2fa')

@two_fa_router.post('/{operation}', response_model=TwoFaResponse)
async def two_fa(
        payload: TwoFaRequest,
        operation: Literal['register', 'login', 'reset_password'],
        service: Annotated[AuthService, Depends()],
) -> TwoFaResponse:
    tokens = await service.complete_operation(
        operation=operation,
        email=str(payload.email),
        password=payload.password,
        code=payload.code
    )
    return TwoFaResponse(
        accessToken=tokens.access.token,
        refreshToken=tokens.refresh.token
    )