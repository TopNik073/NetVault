from starlette.middleware.base import BaseHTTPMiddleware

from src.middlewares.logging_middleware import RequestLoggingMiddleware

MIDDLEWARES: list[type[BaseHTTPMiddleware]] = [
    RequestLoggingMiddleware,
]

__all__ = [
    'MIDDLEWARES',
]