"""Unit tests for advice eligibility service."""

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice import AdviceRepository
from app.repositories.month import MonthRepository
from app.services.advice.eligibility import (
    EXTENDED_HISTORY_LIMIT,
    REGULAR_HISTORY_LIMIT,
    check_eligibility,
)
from tests.conftest import DatabaseTestCase


class TestCheckEligibility(DatabaseTestCase):
    """Test cases for check_eligibility function."""

    def test_eligible_when_target_is_most_recent_month(self) -> None:
        """Returns eligible when target is the most recent month."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 10, month.id, month_repo, advice_repo)

        assert result.is_eligible is True
        assert result.reason is None

    def test_eligible_when_target_is_previous_month(self) -> None:
        """Returns eligible when target is one month before most recent."""
        month_sep = Month(year=2025, month=9)
        month_oct = Month(year=2025, month=10)
        self.session.add_all([month_sep, month_oct])
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 9, month_sep.id, month_repo, advice_repo)

        assert result.is_eligible is True
        assert result.reason is None

    def test_not_eligible_when_target_too_old(self) -> None:
        """Returns not eligible when target is older than previous month."""
        month_aug = Month(year=2025, month=8)
        month_oct = Month(year=2025, month=10)
        self.session.add_all([month_aug, month_oct])
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 8, month_aug.id, month_repo, advice_repo)

        assert result.is_eligible is False
        assert result.reason is not None
        assert "2025-10" in result.reason
        assert "Les conseils ne peuvent être générés" in result.reason

    def test_not_eligible_but_first_advice_reflects_true_for_new_user(self) -> None:
        """Returns is_first_advice=True when user has no advice even if month ineligible."""
        month_aug = Month(year=2025, month=8)
        month_oct = Month(year=2025, month=10)
        self.session.add_all([month_aug, month_oct])
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 8, month_aug.id, month_repo, advice_repo)

        assert result.is_eligible is False
        assert result.is_first_advice is True

    def test_not_eligible_and_first_advice_false_for_existing_user(self) -> None:
        """Returns is_first_advice=False when user has advice even if month ineligible."""
        month_aug = Month(year=2025, month=8)
        month_oct = Month(year=2025, month=10)
        self.session.add_all([month_aug, month_oct])
        self.session.commit()

        # ##>: User already has advice for October.
        advice = Advice(month_id=month_oct.id, advice_text='{"test": "data"}')
        self.session.add(advice)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 8, month_aug.id, month_repo, advice_repo)

        assert result.is_eligible is False
        assert result.is_first_advice is False

    def test_first_advice_returns_12_month_limit(self) -> None:
        """Returns 12 month history limit when no advice exists."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 10, month.id, month_repo, advice_repo)

        assert result.is_eligible is True
        assert result.is_first_advice is True
        assert result.history_limit == EXTENDED_HISTORY_LIMIT

    def test_regenerating_only_advice_returns_12_month_limit(self) -> None:
        """Returns 12 month history limit when regenerating the only advice."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        advice = Advice(month_id=month.id, advice_text='{"test": "data"}')
        self.session.add(advice)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 10, month.id, month_repo, advice_repo)

        assert result.is_eligible is True
        # ##>: Not first advice since one already exists, but still uses extended history.
        assert result.is_first_advice is False
        assert result.history_limit == EXTENDED_HISTORY_LIMIT

    def test_normal_advice_returns_3_month_limit(self) -> None:
        """Returns 3 month history limit when other advice already exists."""
        month_sep = Month(year=2025, month=9)
        month_oct = Month(year=2025, month=10)
        self.session.add_all([month_sep, month_oct])
        self.session.commit()

        # ##>: Add advice for a different month.
        advice = Advice(month_id=month_sep.id, advice_text='{"test": "data"}')
        self.session.add(advice)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(2025, 10, month_oct.id, month_repo, advice_repo)

        assert result.is_eligible is True
        assert result.is_first_advice is False
        assert result.history_limit == REGULAR_HISTORY_LIMIT
