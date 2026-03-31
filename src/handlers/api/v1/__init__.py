from fastapi import APIRouter

from src.handlers.api.v1.auth import auth_router
from src.handlers.api.v1.buckets import buckets_router
from src.handlers.api.v1.files import files_router
from src.handlers.api.v1.folders import folders_router
from src.handlers.api.v1.health import health_router
from src.handlers.api.v1.public_links import public_links_router
from src.handlers.api.v1.search import search_router
from src.handlers.api.v1.upload_sessions import upload_sessions_router
from src.handlers.api.v1.users import users_router

v1_router = APIRouter(prefix='/v1')

v1_router.include_router(auth_router)
v1_router.include_router(buckets_router)
v1_router.include_router(files_router)
v1_router.include_router(folders_router)
v1_router.include_router(health_router)
v1_router.include_router(public_links_router)
v1_router.include_router(search_router)
v1_router.include_router(upload_sessions_router)
v1_router.include_router(users_router)
