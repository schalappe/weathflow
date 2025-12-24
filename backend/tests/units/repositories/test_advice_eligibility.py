"""Unit tests for AdviceRepository eligibility methods."""

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice import AdviceRepository
from tests.conftest import DatabaseTestCase


class TestAdviceRepositoryEligibility(DatabaseTestCase):
    """Test cases for AdviceRepository eligibility-related methods."""

    def test_has_any_returns_true_when_advice_exists(self) -> None:
        """has_any returns True when at least one advice record exists."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()

        advice = Advice(month_id=month.id, advice_text='{"test": "data"}')
        self.session.add(advice)
        self.session.commit()

        repo = AdviceRepository(self.session)
        result = repo.has_any()

        assert result is True

    def test_has_any_returns_false_when_empty(self) -> None:
        """has_any returns False when no advice records exist."""
        repo = AdviceRepository(self.session)
        result = repo.has_any()

        assert result is False

    def test_count_returns_correct_count(self) -> None:
        """count returns the total number of advice records."""
        month1 = Month(year=2025, month=1)
        month2 = Month(year=2025, month=2)
        month3 = Month(year=2025, month=3)
        self.session.add_all([month1, month2, month3])
        self.session.commit()

        self.session.add(Advice(month_id=month1.id, advice_text='{"test": "1"}'))
        self.session.add(Advice(month_id=month2.id, advice_text='{"test": "2"}'))
        self.session.commit()

        repo = AdviceRepository(self.session)
        result = repo.count()

        assert result == 2

    def test_count_returns_zero_when_empty(self) -> None:
        """count returns 0 when no advice records exist."""
        repo = AdviceRepository(self.session)
        result = repo.count()

        assert result == 0
