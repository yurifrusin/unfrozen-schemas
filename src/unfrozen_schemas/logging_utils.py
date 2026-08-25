"""Structured local JSONL logging with a readable console companion."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

_RESERVED_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__)


class JsonLineFormatter(logging.Formatter):
    """Render each log record as one deterministic-key JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_FIELDS and key not in {"message", "asctime"}:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def configure_logging(path: Path, level: str) -> logging.Logger:
    """Create isolated file and console handlers for one smoke run."""

    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("unfrozen_schemas")
    close_logging(logger)
    logger.setLevel(level)
    logger.propagate = False

    file_handler = logging.FileHandler(path, mode="a", encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(console_handler)
    return logger


def close_logging(logger: logging.Logger) -> None:
    """Flush and detach handlers so Windows can release run files between tests."""

    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
