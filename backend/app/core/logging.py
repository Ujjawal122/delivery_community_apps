

import logging
import logging.config
import sys
from typing import Any

from app.config import settings



class _JsonFormatter(logging.Formatter):
    """
    Emits one JSON object per log line.
    Keeps it lightweight — no external deps (no python-json-logger needed).
    """

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Merge any extra= fields the caller passed
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for k, v in record.__dict__.items():
            if k not in skip:
                payload[k] = v

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)



_DEV_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"




def setup_logging() -> None:
    """
    Call once at application startup (in main.py lifespan).
    - Development (LOG_FORMAT=text):  human-readable coloured output
    - Production  (LOG_FORMAT=json):  structured JSON, one line per record
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    use_json = settings.LOG_FORMAT.lower() == "json"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _JsonFormatter() if use_json else logging.Formatter(_DEV_FORMAT)
    )

    # Root logger — catches everything
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    for noisy in ("sqlalchemy.engine", "uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Import this instead of `logging.getLogger`."""
    return logging.getLogger(name)
