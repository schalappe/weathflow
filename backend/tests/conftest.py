"""Pytest fixtures for database testing."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base


@pytest.fixture
def test_db_engine():
    """
    Create an in-memory SQLite engine for testing.

    Uses StaticPool to keep the in-memory database alive across connections.
    """
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a database session for testing with transaction rollback.

    Each test gets a fresh session that is rolled back after the test,
    ensuring test isolation.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
