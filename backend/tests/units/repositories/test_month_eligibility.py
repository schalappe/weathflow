"""Unit tests for MonthRepository eligibility methods."""

from app.db.models.month import Month
from app.repositories.month import MonthRepository
from tests.conftest import DatabaseTestCase


class TestMonthRepositoryEligibility(DatabaseTestCase):
    """Test cases for MonthRepository eligibility-related methods."""

    def test_get_most_recent_returns_latest_month(self) -> None:
        """get_most_recent returns the month with highest year/month."""
        self.session.add(Month(year=2024, month=10))
        self.session.add(Month(year=2024, month=12))
        self.session.add(Month(year=2025, month=1))
        self.session.add(Month(year=2024, month=11))
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_most_recent()

        assert result is not None
        assert result.year == 2025
        assert result.month == 1

    def test_get_most_recent_returns_none_when_empty(self) -> None:
        """get_most_recent returns None when no months exist."""
        repo = MonthRepository(self.session)
        result = repo.get_most_recent()

        assert result is None
