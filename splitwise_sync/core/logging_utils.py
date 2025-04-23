"""Logging utilities for the Splitwise sync application."""

import json
import logging
import logging.handlers
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatter that converts dict/object log records to JSON."""

    def format(self, record: logging.LogRecord):
        """Format log record as JSON if it's a dict or has __dict__ attribute."""
        message = record.msg
        if isinstance(message, dict):
            return json.dumps(message)
        elif hasattr(message, "to_dict") and callable(message.to_dict):
            return json.dumps(message.to_dict())
        return super().format(record)


def create_logger(
    name: str, filename: Path, level: int = logging.INFO, propagate: bool = False
) -> logging.Logger:
    """Create a logger with a TimedRotatingFileHandler."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    handler = logging.handlers.TimedRotatingFileHandler(
        filename,
        when="midnight",
        # backupCount=90,
    )
    handler.setFormatter(JSONFormatter("%(message)s"))
    logger.addHandler(handler)
    return logger
