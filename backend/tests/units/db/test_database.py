"""Tests for database configuration."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy import text

from app.db.database import DATABASE_PATH, engine, init_db


class TestDatabaseConfiguration(unittest.TestCase):
    """Tests for database path resolution and initialization."""

    def test_database_path_resolves_to_correct_location(self) -> None:
        """DATABASE_PATH should point to data/moneymap.db relative to project root."""
        self.assertEqual(DATABASE_PATH.name, "moneymap.db")
        self.assertEqual(DATABASE_PATH.parent.name, "data")

    def test_engine_can_connect_to_sqlite(self) -> None:
        """Engine should be able to establish a connection to SQLite."""
        # ##>: Create the data directory if it does not exist so the test can connect.
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            self.assertEqual(result.scalar(), 1)

    @patch("app.db.database.Base.metadata.create_all")
    @patch("app.db.database.DATABASE_PATH")
    def test_init_db_creates_data_directory(self, mock_db_path: MagicMock, _mock_create_all: MagicMock) -> None:
        """init_db should create the data directory if it does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = Path(tmpdir) / "data" / "test.db"
            mock_db_path.parent = test_db_path.parent

            init_db()

            self.assertTrue(test_db_path.parent.exists())

    @patch("app.db.database.Base.metadata.create_all")
    @patch("app.db.database.DATABASE_PATH")
    def test_init_db_is_idempotent(self, mock_db_path: MagicMock, _mock_create_all: MagicMock) -> None:
        """init_db should be safe to call multiple times without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = Path(tmpdir) / "data" / "test.db"
            mock_db_path.parent = test_db_path.parent

            init_db()
            init_db()

            self.assertTrue(test_db_path.parent.exists())


if __name__ == "__main__":
    unittest.main()
