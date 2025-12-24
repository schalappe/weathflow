"""Unit tests for MonthRepository eligibility methods."""

from app.db.models.month import Month
from app.repositories.month import MonthRepository
from tests.conftest import DatabaseTestCase


class TestGetMostRecentMonth(DatabaseTestCase):
    """Tests for get_most_recent_month method."""

    def test_returns_newest_month_by_year_month(self) -> None:
        """get_most_recent_month returns month with highest year/month."""
        self.session.add(Month(year=2024, month=10))
        self.session.add(Month(year=2024, month=12))
        self.session.add(Month(year=2025, month=1))
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_most_recent_month()

        assert result is not None
        assert result.year == 2025
        assert result.month == 1

    def test_returns_none_when_no_months_exist(self) -> None:
        """get_most_recent_month returns None when database is empty."""
        repo = MonthRepository(self.session)
        result = repo.get_most_recent_month()

        assert result is None
