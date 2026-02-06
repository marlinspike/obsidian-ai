"""Logging configuration for the application."""

import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(level: LogLevel = "INFO") -> logging.Logger:
    """Configure application logging.

    Args:
        level: Logging level

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger("obsidian_ai")
    logger.setLevel(getattr(logging, level))

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level))

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler if not already added
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


# Default logger instance
logger = setup_logging()
