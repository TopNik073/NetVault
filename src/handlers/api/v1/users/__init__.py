from fastapi import APIRouter

from src.handlers.api.v1.users.profile.router import profile_router

users_router = APIRouter(prefix='/users', tags=['users'])

users_router.include_router(profile_router)