"""Integration test fixtures for FastAPI with database."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db

# ##>: Import all models to register them with Base.metadata before table creation.
from app.db.models.advice import Advice  # noqa: F401
from app.db.models.month import Month  # noqa: F401
from app.db.models.transaction import Transaction  # noqa: F401
from app.main import app


@pytest.fixture
def db_engine() -> Generator[Engine, None, None]:
    """
    Create in-memory SQLite engine with all tables.

    Creates a fresh SQLite database in memory for each test, with all
    application tables created. Engine is disposed after test completes.

    Yields
    ------
    Engine
        SQLAlchemy engine configured for in-memory testing.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Provide database session for direct assertions.

    Creates a session bound to the test engine, allowing tests to query
    the database directly to verify state after API operations.

    Parameters
    ----------
    db_engine : Engine
        SQLAlchemy engine from db_engine fixture.

    Yields
    ------
    Session
        SQLAlchemy session for database operations.
    """
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = testing_session_local()
    yield session
    session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Test client with database dependency override.

    Creates a FastAPI TestClient that uses the test database session
    instead of the production database. Dependency overrides are cleared
    after each test to prevent interference.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session from db_session fixture.

    Yields
    ------
    TestClient
        FastAPI test client configured for integration testing.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
