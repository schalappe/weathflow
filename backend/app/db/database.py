"""Database configuration and session management for Money Map Manager."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ##>: Navigate from backend/app/db/ up to project root, then into data/.
DATABASE_PATH = Path(__file__).parent.parent.parent.parent / 'data' / 'moneymap.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
