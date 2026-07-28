"""Structured JSON logging to stderr for LexML MCP operations.

ponytail: stdlib logging with JSON format, no external deps.
Upgrade to structlog or OpenTelemetry when multi-service tracing is needed.
"""

import json
import logging
import sys
import uuid
from typing import Any

from lexml_mcp import config


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "operation", "duration_ms", "status",
                     "error_code", "cache_status", "challenge_detected",
                     "record_count"):
            val = getattr(record, key, None)
            if val is not None:
                obj[key] = val
        if record.exc_info and record.exc_info[0]:
            obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False, default=str)


_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(JsonFormatter())

_logger = logging.getLogger("lexml_mcp")
_logger.setLevel(getattr(logging, config.LEXML_LOG_LEVEL.upper(), logging.INFO))
_logger.handlers.clear()
_logger.addHandler(_handler)
_logger.propagate = False


def get_logger(name: str = "lexml_mcp") -> logging.Logger:
    return logging.getLogger(name)


def make_request_id() -> str:
    return uuid.uuid4().hex[:12]