"""Loguru logging configuration for the application."""

import sys

from loguru import logger


def configure_logging() -> None:
    """
    Configure loguru logger with application defaults.

    Removes default handler and adds a custom one with consistent formatting.
    Called once during application startup in main.py.
    """
    # ##>: Remove default handler to prevent duplicate logs.
    logger.remove()

    # ##>: Add console handler with colored output for development.
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )
