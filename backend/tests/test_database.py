"""Tests for database configuration."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import text

from app.db.database import DATABASE_PATH, engine, init_db


def test_database_path_resolves_to_correct_location() -> None:
    """DATABASE_PATH should point to data/moneymap.db relative to project root."""
    assert DATABASE_PATH.name == 'moneymap.db'
    assert DATABASE_PATH.parent.name == 'data'


def test_engine_can_connect_to_sqlite() -> None:
    """Engine should be able to establish a connection to SQLite."""
    # ##>: Create the data directory if it does not exist so the test can connect.
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        assert result.scalar() == 1


def test_init_db_creates_data_directory() -> None:
    """init_db should create the data directory if it does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / 'data' / 'test.db'

        with (
            patch('app.db.database.DATABASE_PATH', test_db_path),
            patch('app.db.database.Base.metadata.create_all'),
        ):
            init_db()

        assert test_db_path.parent.exists()


def test_init_db_is_idempotent() -> None:
    """init_db should be safe to call multiple times without error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / 'data' / 'test.db'

        with (
            patch('app.db.database.DATABASE_PATH', test_db_path),
            patch('app.db.database.Base.metadata.create_all'),
        ):
            init_db()
            init_db()

        assert test_db_path.parent.exists()
