"""Database configuration and session management for Money Map Manager."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Connection, create_engine, inspect, text
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


def _ensure_income_fact_label(connection: Connection) -> None:
    """Add the nullable one-off pairing label to legacy SQLite data.

    Parameters
    ----------
    connection : Connection
        Active database connection.
    """
    inspector = inspect(connection)
    if "income_fact" not in inspector.get_table_names():
        return
    if "label" not in {column["name"] for column in inspector.get_columns("income_fact")}:
        connection.execute(text("ALTER TABLE income_fact ADD COLUMN label VARCHAR(200)"))


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Creates the data directory if it does not exist, then creates all tables
    defined in the SQLAlchemy models. Safe to call multiple times.
    """
    # ##>: Import all models to register them with SQLAlchemy before creating tables.
    # This ensures relationships like Month.advice_records can resolve the Advice class.
    from app.db.models import (  # noqa: F401
        active_priority,
        advice,
        commitment_fact,
        constraint_fact,
        emergency_fund_fact,
        income_fact,
        month,
        observation_fact,
        transaction,
    )

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        _ensure_income_fact_label(connection)
