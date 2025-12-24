"""Unit tests for AdviceRepository eligibility methods."""

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice import AdviceRepository
from tests.conftest import DatabaseTestCase


class TestHasAnyAdvice(DatabaseTestCase):
    """Tests for has_any_advice method."""

    def test_returns_true_when_advice_exists(self) -> None:
        """has_any_advice returns True when at least one advice record exists."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()

        advice = Advice(month_id=month.id, advice_text='{"summary": "Test"}')
        self.session.add(advice)
        self.session.commit()

        repo = AdviceRepository(self.session)
        result = repo.has_any_advice()

        assert result is True

    def test_returns_false_when_no_advice_exists(self) -> None:
        """has_any_advice returns False when advice table is empty."""
        repo = AdviceRepository(self.session)
        result = repo.has_any_advice()

        assert result is False
