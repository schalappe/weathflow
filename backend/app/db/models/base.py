"""Base model utilities for SQLAlchemy models."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC timestamp for database defaults."""
    return datetime.now(UTC)
