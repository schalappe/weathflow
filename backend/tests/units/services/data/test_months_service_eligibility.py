"""Unit tests for months service eligibility methods."""

from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError

from app.db.models.month import Month
from app.repositories.month import MonthRepository
from app.services.data import months as months_service
from app.services.exceptions import MonthQueryError
from tests.conftest import DatabaseTestCase


class TestGetMostRecentMonth(DatabaseTestCase):
    """Tests for get_most_recent_month service function."""

    def test_returns_month_from_repository(self) -> None:
        """get_most_recent_month returns month from repository."""
        self.session.add(Month(year=2025, month=9))
        month2 = Month(year=2025, month=10)
        self.session.add(month2)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        result = months_service.get_most_recent_month(month_repo)

        assert result is not None
        assert result.year == 2025
        assert result.month == 10

    def test_handles_repository_errors(self) -> None:
        """get_most_recent_month raises MonthQueryError on database error."""
        month_repo = MagicMock(spec=MonthRepository)
        month_repo.get_most_recent_month.side_effect = SQLAlchemyError("DB connection failed")

        with self.assertRaises(MonthQueryError) as context:
            months_service.get_most_recent_month(month_repo)

        assert "DB connection failed" in str(context.exception)
