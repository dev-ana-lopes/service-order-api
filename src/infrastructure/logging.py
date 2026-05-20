from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.config import dictConfig

from .config.settings import Settings


class JsonLogFormatter(logging.Formatter):
    RESERVED_KEYS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in self.RESERVED_KEYS or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, default=str)


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key in ("authorization", "token", "password", "database_url"):
            if hasattr(record, key):
                setattr(record, key, "[REDACTED]")
        return True



def mask_cpf(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    return "***.***.***-**"



def configure_logging(settings: Settings) -> None:
    formatter_name = "json" if settings.LOG_JSON or settings.ENVIRONMENT in {"staging", "production"} else "standard"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"sensitive": {"()": SensitiveDataFilter}},
            "formatters": {
                "standard": {
                    "format": ("%(asctime)s %(levelname)s [%(name)s] %(message)s")
                },
                "json": {"()": JsonLogFormatter},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_name,
                    "filters": ["sensitive"],
                }
            },
            "root": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
            },
        }
    )
