from fastapi import APIRouter

from src.handlers.api import api_router
from src.handlers.public import public_router

app_router = APIRouter()
app_router.include_router(public_router)
app_router.include_router(api_router)

ROUTERS: list[APIRouter] = [
    app_router,
]

__all__ = [
    'ROUTERS',
]
