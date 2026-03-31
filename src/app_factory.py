from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import Any

from fastapi import FastAPI, APIRouter
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import config
from src.core.logger import get_logger
from src.database.connection import engine
from src.integrations.redis.connection import init_redis_pool, close_redis_pool

logger = get_logger('app_factory')

class AppFactory:
    def __init__(  # noqa: PLR0913
            self,
            *,
            title: str,
            version: str,
            debug: bool = False,
            lifespan: AsyncGenerator[None, Any] | None = None,
            routers: list[APIRouter] | None = None,
            middlewares: list[type[BaseHTTPMiddleware]] | None = None,
    ):
        self._app = FastAPI(
            title=title,
            version=version,
            debug=debug,
            lifespan=lifespan or self.lifespan,
        )
        self._middlewares = middlewares
        self._routers = routers

        self.setup_app()

    @property
    def app(self) -> FastAPI:
        return self._app

    @property
    def routers(self) -> list[APIRouter]:
        return self._routers

    @property
    def middlewares(self) -> list[type[BaseHTTPMiddleware]]:
        return self._middlewares

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        # Startup
        logger.info('Initializing application dependencies')

        app.state.redis = await init_redis_pool()
        app.state.start_time = datetime.now(UTC)


        docs_route = f'http://{config.APP_HOST}:{config.APP_PORT}/docs'
        logger.info(
            f'Application {config.APP_NAME}_{config.APP_VERSION} started successfully. See docs here {docs_route}'  # noqa: G004
        )
        yield

        # Shutdown
        logger.info('Shutting down application')

        await close_redis_pool(app.state.redis)
        await engine.dispose()

        logger.info('Application shutdown complete')

    def setup_app(self):
        if self._routers:
            self.setup_routers(self._app, self._routers)

        if self._middlewares:
            self.setup_middlewares(self._app, self._middlewares)

    @staticmethod
    def setup_routers(app: FastAPI, routers: list[APIRouter]) -> None:
        for router in routers:
            app.include_router(router)

    @staticmethod
    def setup_middlewares(app: FastAPI, middlewares: list[type[BaseHTTPMiddleware]]) -> None:
        for middleware in middlewares:
            app.add_middleware(middleware)