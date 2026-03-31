import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Any

import structlog

from src.core.config import config


def setup_logging(level: int | str) -> None:
    handlers = []

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    handlers.append(console_handler)

    if config.LOG_TO_FILE:
        file_handler = RotatingFileHandler(
            config.LOGS_DIR / f"{config.APP_NAME}_{config.APP_VERSION}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setLevel(level)
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",
        handlers=handlers,
        level=level,
    )


def get_logger(name: str, level: int | str = config.LOG_LEVEL) -> structlog.BoundLogger:
    setup_logging(level)
    render_method = (
        structlog.dev.ConsoleRenderer()
        if config.DEBUG
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt=config.LOG_DATE_FORMAT, utc=True),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            mask_sensitive_data,
            render_method,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(name)


def mask_sensitive_data(logger, method_name, event_dict: dict[str, Any]) -> dict[str, Any]:
    def _mask(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                key: _mask(value) if key not in config.SENSITIVE_DATA else "***MASKED***"
                for key, value in obj.items()
            }
        if isinstance(obj, list):
            return [_mask(item) for item in obj]
        if isinstance(obj, str) and obj.startswith("{") and obj.endswith("}"):
            try:
                return _mask(json.loads(obj))
            except json.JSONDecodeError:
                return obj
        return obj

    return _mask(event_dict)
