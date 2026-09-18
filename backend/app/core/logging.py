"""Structured logging configuration for the Smart Multizone Irrigation backend."""

import logging
import sys

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Initialize root logger with formatted standard output stream."""
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """Return configured logger instance for a given module name."""
    return logging.getLogger(name)
