"""
Structured JSON logger.
Every run gets a unique run_id for log grouping.
Writes to both stdout and a rotating file in logs/.
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def __init__(self, run_id: str):
        super().__init__()
        self.run_id = run_id

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "run_id":  self.run_id,
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logger(
    name:    str = "portfolio",
    log_dir: str = "logs",
    level:   int = logging.INFO,
) -> tuple[logging.Logger, str]:
    """
    Configure structured logging for a run.

    Returns
    -------
    (logger, run_id)
    """
    run_id = str(uuid.uuid4())[:8]
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()
    logger.propagate = False

    formatter = JsonFormatter(run_id=run_id)

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # File handler
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / f"{name}.log",
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logger initialized", extra={"run_id": run_id})
    return logger, run_id
