"""Structured logging configuration for the users-service."""
import json
import logging
import os
from logging.config import dictConfig


def setup_logging(default_level: str = "INFO") -> None:
    log_level = os.getenv("LOG_LEVEL", default_level).upper()
    dictConfig(
        {
            "version": 1,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "json",
                }
            },
            "root": {"level": log_level, "handlers": ["console"]},
        }
    )


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - helper
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
