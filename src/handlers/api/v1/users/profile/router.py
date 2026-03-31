from typing import Annotated

from fastapi import APIRouter, Depends

from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.users.profile.models import ProfileResponse
from src.handlers.dependencies.auth import get_current_user

profile_router = APIRouter(prefix='/profile')

@profile_router.get('/', response_model=ProfileResponse)
async def get_profile(
    user: Annotated[User, Depends(get_current_user)],
) -> ProfileResponse:
    return ProfileResponse.model_validate(user)