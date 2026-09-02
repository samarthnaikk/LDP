"""Shared logging setup for LDP runtime entrypoints."""

from __future__ import annotations

import logging
import os
from pathlib import Path


DEFAULT_LOG_DIR = "logs"


def configure_logging(role: str) -> Path:
    """Configure console and file logging for a runtime role."""
    log_dir = Path(os.getenv("LDP_LOG_DIR", DEFAULT_LOG_DIR))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{role}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
    root_logger.info("Logging configured for role=%s log_path=%s", role, log_path)
    return log_path
