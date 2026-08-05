"""Tests for database configuration."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, inspect, text

from app.db.database import DATABASE_PATH, _ensure_income_fact_label, engine, init_db


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

    def test_legacy_income_fact_gains_pairing_label(self) -> None:
        """Existing SQLite income facts gain the nullable label column."""
        legacy_engine = create_engine("sqlite://")
        with legacy_engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE income_fact (fact_type VARCHAR(40) PRIMARY KEY, amount FLOAT NOT NULL)")
            )
            _ensure_income_fact_label(connection)
            _ensure_income_fact_label(connection)
            columns = {column["name"] for column in inspect(connection).get_columns("income_fact")}

        self.assertEqual(columns, {"fact_type", "amount", "label"})


if __name__ == "__main__":
    unittest.main()
