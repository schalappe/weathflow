"""Base test class providing database fixtures for unit tests."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base

# ##>: Import all models to register them with Base.metadata before table creation.
from app.db.models.advice import Advice  # noqa: F401
from app.db.models.month import Month  # noqa: F401
from app.db.models.transaction import Transaction  # noqa: F401


class DatabaseTestCase(unittest.TestCase):
    """
    Base test class providing an in-memory SQLite database for testing.

    Each test gets a fresh database with all tables recreated for isolation.
    """

    engine = None
    session: Session

    def setUp(self) -> None:
        """Create a fresh in-memory database and session for each test."""
        # ##>: Create a new engine for each test to ensure complete isolation.
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)

        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = session_factory()

    def tearDown(self) -> None:
        """Close the session and drop all tables after each test."""
        self.session.close()
        if self.engine:
            Base.metadata.drop_all(bind=self.engine)
            self.engine.dispose()
