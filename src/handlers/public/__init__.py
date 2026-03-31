from fastapi import APIRouter

from src.handlers.public.download import download_router

public_router = APIRouter(prefix='/public', tags=['Public'])

public_router.include_router(download_router)