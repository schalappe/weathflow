"""Database configuration and session management for Money Map Manager."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings

# ##>: Get database URL from settings. Fallback to local path for default.
settings = get_settings()
DATABASE_URL = settings.database_url
DATABASE_PATH = Path(DATABASE_URL.replace("sqlite:///", ""))

# ##&: SQLite requires check_same_thread=False for FastAPI's multi-threaded request handling.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for FastAPI dependency injection.

    Yields
    ------
    Session
        A SQLAlchemy session that is automatically closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Creates the data directory if it does not exist, then creates all tables
    defined in the SQLAlchemy models. Safe to call multiple times.
    """
    # ##>: Import all models to register them with SQLAlchemy before creating tables.
    # This ensures relationships like Month.advice_records can resolve the Advice class.
    from app.db.models import advice, month, transaction  # noqa: F401

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
