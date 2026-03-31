from fastapi import APIRouter

health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("")
async def health():
    return {"status": "ok"}