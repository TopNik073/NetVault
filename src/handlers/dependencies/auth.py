from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database.repository.postgres.user.dtos import User
from src.exceptions import InvalidToken
from src.services.auth.service import AuthService

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    service: Annotated[AuthService, Depends(AuthService)],
) -> User:
    user, _, token_type = await service.verify_token(credentials.credentials)
    if token_type != 'access':
        raise InvalidToken

    return user
