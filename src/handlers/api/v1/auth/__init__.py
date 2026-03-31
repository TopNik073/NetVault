from fastapi import APIRouter

from src.handlers.api.v1.auth.login.router import login_router
from src.handlers.api.v1.auth.refresh.router import refresh_router
from src.handlers.api.v1.auth.register.router import register_router
from src.handlers.api.v1.auth.reset_password.router import reset_password_router
from src.handlers.api.v1.auth.two_fa_auth.router import two_fa_router

auth_router = APIRouter(prefix="/auth", tags=["auth"])

auth_router.include_router(login_router)
auth_router.include_router(register_router)
auth_router.include_router(reset_password_router)
auth_router.include_router(two_fa_router)
auth_router.include_router(refresh_router)
