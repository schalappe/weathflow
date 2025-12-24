"""Unit tests for advice eligibility service."""

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice import AdviceRepository
from app.repositories.month import MonthRepository
from app.services.advice.eligibility import (
    ELIGIBLE_MONTH_WINDOW,
    EXTENDED_HISTORY_LIMIT,
    MIN_MONTHS_REQUIRED,
    REGULAR_HISTORY_LIMIT,
    check_eligibility,
)
from tests.conftest import DatabaseTestCase


class TestCheckEligibility(DatabaseTestCase):
    """Tests for check_eligibility function."""

    def test_most_recent_month_is_eligible(self) -> None:
        """Most recent month returns is_eligible=True."""
        self.session.add(Month(year=2025, month=9))
        month2 = Month(year=2025, month=10)
        self.session.add(month2)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=10,
            target_month_id=month2.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        assert result.is_eligible is True

    def test_second_most_recent_month_is_eligible(self) -> None:
        """Second most recent month returns is_eligible=True."""
        month1 = Month(year=2025, month=9)
        self.session.add(month1)
        self.session.add(Month(year=2025, month=10))
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=9,
            target_month_id=month1.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        assert result.is_eligible is True

    def test_old_month_is_ineligible_with_reason(self) -> None:
        """Month older than 2 most recent returns is_eligible=False with reason."""
        month1 = Month(year=2025, month=8)
        self.session.add(month1)
        self.session.add(Month(year=2025, month=9))
        self.session.add(Month(year=2025, month=10))
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=8,
            target_month_id=month1.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        assert result.is_eligible is False
        assert result.reason is not None
        assert "2025-10" in result.reason

    def test_first_advice_returns_extended_history_limit(self) -> None:
        """First advice scenario returns history_limit=12."""
        self.session.add(Month(year=2025, month=9))
        month2 = Month(year=2025, month=10)
        self.session.add(month2)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=10,
            target_month_id=month2.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        assert result.is_first_advice is True
        assert result.history_limit == EXTENDED_HISTORY_LIMIT

    def test_subsequent_advice_returns_regular_history_limit(self) -> None:
        """Subsequent advice returns history_limit=3."""
        month1 = Month(year=2025, month=9)
        month2 = Month(year=2025, month=10)
        self.session.add(month1)
        self.session.add(month2)
        self.session.commit()

        # Add existing advice for month 9.
        advice = Advice(month_id=month1.id, advice_text='{"summary": "Old advice"}')
        self.session.add(advice)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=10,
            target_month_id=month2.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        assert result.is_first_advice is False
        assert result.history_limit == REGULAR_HISTORY_LIMIT

    def test_regenerating_first_advice_returns_extended_limit(self) -> None:
        """Regenerating the only/first advice month uses extended limit."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        # Add advice for the month we're regenerating (but it's the first/only).
        advice = Advice(month_id=month.id, advice_text='{"summary": "First advice"}')
        self.session.add(advice)
        self.session.commit()

        # Add another month so we have 2 months for eligibility.
        self.session.add(Month(year=2025, month=9))
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=10,
            target_month_id=month.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        # Since it's the only advice and we're regenerating it, treat as first advice.
        assert result.is_first_advice is True
        assert result.history_limit == EXTENDED_HISTORY_LIMIT

    def test_insufficient_data_with_one_month(self) -> None:
        """Single month returns is_eligible=False due to insufficient data."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        result = check_eligibility(
            target_year=2025,
            target_month=10,
            target_month_id=month.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )

        assert result.is_eligible is False
        assert result.reason is not None
        assert "at least" in result.reason.lower()

    def test_year_boundary_eligibility(self) -> None:
        """Dec 2024 and Jan 2025 are both eligible when Jan 2025 is most recent."""
        month_dec = Month(year=2024, month=12)
        month_jan = Month(year=2025, month=1)
        self.session.add(month_dec)
        self.session.add(month_jan)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        advice_repo = AdviceRepository(self.session)

        # Check December 2024 is eligible.
        dec_result = check_eligibility(
            target_year=2024,
            target_month=12,
            target_month_id=month_dec.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )
        assert dec_result.is_eligible is True

        # Check January 2025 is eligible.
        jan_result = check_eligibility(
            target_year=2025,
            target_month=1,
            target_month_id=month_jan.id,
            month_repo=month_repo,
            advice_repo=advice_repo,
        )
        assert jan_result.is_eligible is True


class TestEligibilityConstants(DatabaseTestCase):
    """Tests for eligibility constants."""

    def test_constants_have_expected_values(self) -> None:
        """Verify constants match spec requirements."""
        assert REGULAR_HISTORY_LIMIT == 3
        assert EXTENDED_HISTORY_LIMIT == 12
        assert MIN_MONTHS_REQUIRED == 2
        assert ELIGIBLE_MONTH_WINDOW == 2
