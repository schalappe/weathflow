"""Tests for Score Calculation Service."""

import unittest
from datetime import date

from pydantic import ValidationError

from app.db.enums import MoneyMapType, ScoreLabel
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.exceptions import (
    MonthNotFoundError,
    ScoreCalculationError,
    ScorePersistenceError,
    TransactionAggregationError,
)
from app.services.schemas.calculation import MonthStats
from tests.conftest import DatabaseTestCase

# =============================================================================
# Task Group 1: MonthStats Schema and Custom Exception Tests
# =============================================================================


class TestMonthStatsSchema(unittest.TestCase):
    """Tests for MonthStats Pydantic schema."""

    def test_create_month_stats_with_valid_data(self) -> None:
        """Should create MonthStats with all valid fields."""
        stats = MonthStats(
            total_income=5000.0,
            total_core=2000.0,
            total_choice=1000.0,
            total_compound=2000.0,
            core_percentage=40.0,
            choice_percentage=20.0,
            compound_percentage=40.0,
            score=3,
            score_label=ScoreLabel.GREAT,
        )

        self.assertEqual(stats.total_income, 5000.0)
        self.assertEqual(stats.total_core, 2000.0)
        self.assertEqual(stats.total_choice, 1000.0)
        self.assertEqual(stats.total_compound, 2000.0)
        self.assertEqual(stats.core_percentage, 40.0)
        self.assertEqual(stats.choice_percentage, 20.0)
        self.assertEqual(stats.compound_percentage, 40.0)
        self.assertEqual(stats.score, 3)
        self.assertEqual(stats.score_label, ScoreLabel.GREAT)

    def test_month_stats_is_immutable(self) -> None:
        """Should raise ValidationError when attempting to modify frozen model."""
        stats = MonthStats(
            total_income=5000.0,
            total_core=2000.0,
            total_choice=1000.0,
            total_compound=2000.0,
            core_percentage=40.0,
            choice_percentage=20.0,
            compound_percentage=40.0,
            score=3,
            score_label=ScoreLabel.GREAT,
        )

        with self.assertRaises(ValidationError):
            stats.score = 2

    def test_month_stats_field_constraints(self) -> None:
        """Should enforce score range 0-3."""
        # ##>: Score must be between 0 and 3 inclusive.
        with self.assertRaises(ValidationError):
            MonthStats(
                total_income=5000.0,
                total_core=2000.0,
                total_choice=1000.0,
                total_compound=2000.0,
                core_percentage=40.0,
                choice_percentage=20.0,
                compound_percentage=40.0,
                score=4,  # Invalid: exceeds max of 3
                score_label=ScoreLabel.GREAT,
            )

        with self.assertRaises(ValidationError):
            MonthStats(
                total_income=5000.0,
                total_core=2000.0,
                total_choice=1000.0,
                total_compound=2000.0,
                core_percentage=40.0,
                choice_percentage=20.0,
                compound_percentage=40.0,
                score=-1,  # Invalid: below min of 0
                score_label=ScoreLabel.GREAT,
            )

    def test_month_stats_rejects_score_label_mismatch(self) -> None:
        """Should raise ValidationError when score and score_label don't match."""
        # ##>: Score 3 should have GREAT label, not POOR.
        with self.assertRaises(ValidationError) as context:
            MonthStats(
                total_income=5000.0,
                total_core=2000.0,
                total_choice=1000.0,
                total_compound=2000.0,
                core_percentage=40.0,
                choice_percentage=20.0,
                compound_percentage=40.0,
                score=3,
                score_label=ScoreLabel.POOR,  # Mismatch!
            )

        self.assertIn("does not match", str(context.exception))


class TestMonthNotFoundError(unittest.TestCase):
    """Tests for MonthNotFoundError exception."""

    def test_exception_stores_month_id(self) -> None:
        """Should store month_id attribute for programmatic access."""
        error = MonthNotFoundError(month_id=42)

        self.assertEqual(error.month_id, 42)

    def test_exception_provides_readable_message(self) -> None:
        """Should provide human-readable error message."""
        error = MonthNotFoundError(month_id=42)

        self.assertIn("42", str(error))
        self.assertIn("not found", str(error).lower())

    def test_exception_inherits_from_score_calculation_error(self) -> None:
        """Should inherit from ScoreCalculationError for catch-all handling."""
        error = MonthNotFoundError(month_id=42)

        self.assertIsInstance(error, ScoreCalculationError)


class TestTransactionAggregationError(unittest.TestCase):
    """Tests for TransactionAggregationError exception."""

    def test_exception_stores_attributes(self) -> None:
        """Should store month_id and reason for programmatic access."""
        error = TransactionAggregationError(month_id=42, reason="database timeout")

        self.assertEqual(error.month_id, 42)
        self.assertEqual(error.reason, "database timeout")

    def test_exception_provides_readable_message(self) -> None:
        """Should provide human-readable error message."""
        error = TransactionAggregationError(month_id=42, reason="connection lost")

        self.assertIn("42", str(error))
        self.assertIn("connection lost", str(error))

    def test_exception_inherits_from_score_calculation_error(self) -> None:
        """Should inherit from ScoreCalculationError for catch-all handling."""
        error = TransactionAggregationError(month_id=42, reason="test")

        self.assertIsInstance(error, ScoreCalculationError)


class TestScorePersistenceError(unittest.TestCase):
    """Tests for ScorePersistenceError exception."""

    def test_exception_stores_month_id(self) -> None:
        """Should store month_id attribute for programmatic access."""
        error = ScorePersistenceError(month_id=42)

        self.assertEqual(error.month_id, 42)

    def test_exception_provides_readable_message(self) -> None:
        """Should provide human-readable error message."""
        error = ScorePersistenceError(month_id=42)

        self.assertIn("42", str(error))
        self.assertIn("persist", str(error).lower())

    def test_exception_inherits_from_score_calculation_error(self) -> None:
        """Should inherit from ScoreCalculationError for catch-all handling."""
        error = ScorePersistenceError(month_id=42)

        self.assertIsInstance(error, ScoreCalculationError)


# =============================================================================
# Task Group 2: Score and Stats Calculation Function Tests
# =============================================================================


class TestCalculateScore(unittest.TestCase):
    """Tests for calculate_score pure function."""

    def test_perfect_score_all_thresholds_met(self) -> None:
        """Should return score 3 and 'Great' when all thresholds are met."""
        from app.services.calculator import calculate_score

        # ##>: 45% core (<=50), 25% choice (<=30), 30% compound (>=20).
        score, label = calculate_score(core_pct=45.0, choice_pct=25.0, compound_pct=30.0)

        self.assertEqual(score, 3)
        self.assertEqual(label, ScoreLabel.GREAT)

    def test_score_at_exact_thresholds(self) -> None:
        """Should return score 3 when percentages are exactly at thresholds."""
        from app.services.calculator import calculate_score

        # ##>: Exactly 50%, 30%, 20% should still pass all thresholds.
        score, label = calculate_score(core_pct=50.0, choice_pct=30.0, compound_pct=20.0)

        self.assertEqual(score, 3)
        self.assertEqual(label, ScoreLabel.GREAT)

    def test_score_one_threshold_exceeded(self) -> None:
        """Should return score 2 when one threshold is exceeded."""
        from app.services.calculator import calculate_score

        # ##>: Core at 55% (exceeds 50%), others within limits.
        score, label = calculate_score(core_pct=55.0, choice_pct=25.0, compound_pct=20.0)

        self.assertEqual(score, 2)
        self.assertEqual(label, ScoreLabel.OKAY)

    def test_score_two_thresholds_exceeded(self) -> None:
        """Should return score 1 when two thresholds are exceeded."""
        from app.services.calculator import calculate_score

        # ##>: Core at 55% (exceeds 50%), compound at 15% (below 20%).
        score, label = calculate_score(core_pct=55.0, choice_pct=25.0, compound_pct=15.0)

        self.assertEqual(score, 1)
        self.assertEqual(label, ScoreLabel.NEED_IMPROVEMENT)

    def test_score_zero_no_thresholds_met(self) -> None:
        """Should return score 0 when no thresholds are met."""
        from app.services.calculator import calculate_score

        # ##>: All thresholds exceeded.
        score, label = calculate_score(core_pct=60.0, choice_pct=35.0, compound_pct=5.0)

        self.assertEqual(score, 0)
        self.assertEqual(label, ScoreLabel.POOR)


class TestCalculateMonthStats(unittest.TestCase):
    """Tests for calculate_month_stats pure function."""

    def test_happy_path_with_valid_totals(self) -> None:
        """Should calculate correct stats from valid totals."""
        from app.services.calculator import calculate_month_stats

        stats = calculate_month_stats(income=5000.0, core=2000.0, choice=1000.0)

        self.assertEqual(stats.total_income, 5000.0)
        self.assertEqual(stats.total_core, 2000.0)
        self.assertEqual(stats.total_choice, 1000.0)
        self.assertEqual(stats.total_compound, 2000.0)  # 5000 - 2000 - 1000
        self.assertEqual(stats.core_percentage, 40.0)
        self.assertEqual(stats.choice_percentage, 20.0)
        self.assertEqual(stats.compound_percentage, 40.0)
        self.assertEqual(stats.score, 3)
        self.assertEqual(stats.score_label, ScoreLabel.GREAT)

    def test_zero_income_edge_case(self) -> None:
        """Should return score 0 and 'Poor' when income is zero."""
        from app.services.calculator import calculate_month_stats

        stats = calculate_month_stats(income=0.0, core=0.0, choice=0.0)

        self.assertEqual(stats.total_income, 0.0)
        self.assertEqual(stats.core_percentage, 0.0)
        self.assertEqual(stats.choice_percentage, 0.0)
        self.assertEqual(stats.compound_percentage, 0.0)
        self.assertEqual(stats.score, 0)
        self.assertEqual(stats.score_label, ScoreLabel.POOR)

    def test_negative_income_edge_case(self) -> None:
        """Should return score 0 and 'Poor' when income is negative."""
        from app.services.calculator import calculate_month_stats

        # ##>: Negative income (data error or refund-only month) handled like zero.
        stats = calculate_month_stats(income=-500.0, core=0.0, choice=0.0)

        self.assertEqual(stats.total_income, -500.0)
        self.assertEqual(stats.core_percentage, 0.0)
        self.assertEqual(stats.choice_percentage, 0.0)
        self.assertEqual(stats.compound_percentage, 0.0)
        self.assertEqual(stats.score, 0)
        self.assertEqual(stats.score_label, ScoreLabel.POOR)

    def test_negative_compound_overspent(self) -> None:
        """Should calculate correctly when compound is negative (overspent)."""
        from app.services.calculator import calculate_month_stats

        # ##>: Spending exceeds income: 3000 + 2500 = 5500 > 5000.
        stats = calculate_month_stats(income=5000.0, core=3000.0, choice=2500.0)

        self.assertEqual(stats.total_compound, -500.0)  # 5000 - 3000 - 2500
        self.assertEqual(stats.compound_percentage, -10.0)  # (-500 / 5000) * 100
        # ##>: Score should reflect failed compound threshold.
        self.assertLess(stats.score, 3)


# =============================================================================
# Task Group 3: Database Integration Tests
# =============================================================================


class TestAggregateTransactionTotals(DatabaseTestCase):
    """Tests for _aggregate_transaction_totals database function."""

    def test_aggregate_with_sample_transactions(self) -> None:
        """Should correctly aggregate totals by money_map_type."""
        from app.services.calculator import _aggregate_transaction_totals

        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        # ##>: Create sample transactions with different types.
        transactions = [
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 1),
                description="Salary",
                amount=5000.0,
                money_map_type=MoneyMapType.INCOME.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 5),
                description="Rent",
                amount=-1500.0,
                money_map_type=MoneyMapType.CORE.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 10),
                description="Groceries",
                amount=-500.0,
                money_map_type=MoneyMapType.CORE.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 15),
                description="Restaurant",
                amount=-200.0,
                money_map_type=MoneyMapType.CHOICE.value,
            ),
        ]
        self.session.add_all(transactions)
        self.session.commit()

        income, core, choice = _aggregate_transaction_totals(self.session, month.id)

        self.assertEqual(income, 5000.0)
        self.assertEqual(core, 2000.0)  # |1500| + |500|
        self.assertEqual(choice, 200.0)

    def test_aggregate_with_no_transactions(self) -> None:
        """Should return (0, 0, 0) when month has no transactions."""
        from app.services.calculator import _aggregate_transaction_totals

        month = Month(year=2025, month=11)
        self.session.add(month)
        self.session.commit()

        income, core, choice = _aggregate_transaction_totals(self.session, month.id)

        self.assertEqual(income, 0.0)
        self.assertEqual(core, 0.0)
        self.assertEqual(choice, 0.0)

    def test_aggregate_ignores_excluded_transactions(self) -> None:
        """Should not include EXCLUDED transactions in totals."""
        from app.services.calculator import _aggregate_transaction_totals

        month = Month(year=2025, month=12)
        self.session.add(month)
        self.session.commit()

        # ##>: EXCLUDED transactions (internal transfers) should be ignored.
        transactions = [
            Transaction(
                month_id=month.id,
                date=date(2025, 12, 1),
                description="Salary",
                amount=5000.0,
                money_map_type=MoneyMapType.INCOME.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 12, 5),
                description="Transfer to savings",
                amount=-1000.0,
                money_map_type=MoneyMapType.EXCLUDED.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 12, 10),
                description="Internal transfer",
                amount=1000.0,
                money_map_type=MoneyMapType.EXCLUDED.value,
            ),
        ]
        self.session.add_all(transactions)
        self.session.commit()

        income, core, choice = _aggregate_transaction_totals(self.session, month.id)

        # ##>: EXCLUDED transactions should not appear in any total.
        self.assertEqual(income, 5000.0)
        self.assertEqual(core, 0.0)
        self.assertEqual(choice, 0.0)


class TestCalculateAndUpdateMonth(DatabaseTestCase):
    """Tests for calculate_and_update_month integration function."""

    def test_updates_month_record_correctly(self) -> None:
        """Should update all Month fields with calculated stats."""
        from app.services.calculator import calculate_and_update_month

        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        # ##>: Create transactions for a good score.
        transactions = [
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 1),
                description="Salary",
                amount=10000.0,
                money_map_type=MoneyMapType.INCOME.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 5),
                description="Rent",
                amount=-4000.0,
                money_map_type=MoneyMapType.CORE.value,
            ),
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 10),
                description="Entertainment",
                amount=-2000.0,
                money_map_type=MoneyMapType.CHOICE.value,
            ),
        ]
        self.session.add_all(transactions)
        self.session.commit()

        updated_month = calculate_and_update_month(self.session, month.id)

        self.assertEqual(updated_month.total_income, 10000.0)
        self.assertEqual(updated_month.total_core, 4000.0)
        self.assertEqual(updated_month.total_choice, 2000.0)
        self.assertEqual(updated_month.total_compound, 4000.0)
        self.assertEqual(updated_month.core_percentage, 40.0)
        self.assertEqual(updated_month.choice_percentage, 20.0)
        self.assertEqual(updated_month.compound_percentage, 40.0)
        self.assertEqual(updated_month.score, 3)
        self.assertEqual(updated_month.score_label, ScoreLabel.GREAT.value)

    def test_raises_month_not_found_error(self) -> None:
        """Should raise MonthNotFoundError for non-existent month_id."""
        from app.services.calculator import calculate_and_update_month

        with self.assertRaises(MonthNotFoundError) as context:
            calculate_and_update_month(self.session, month_id=99999)

        self.assertEqual(context.exception.month_id, 99999)

    def test_recalculation_after_category_change(self) -> None:
        """Should recalculate correctly after transaction category is changed."""
        from app.services.calculator import calculate_and_update_month

        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        income_tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 1),
            description="Salary",
            amount=5000.0,
            money_map_type=MoneyMapType.INCOME.value,
        )
        expense_tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 5),
            description="Expense",
            amount=-3000.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        self.session.add_all([income_tx, expense_tx])
        self.session.commit()

        # ##>: First calculation.
        first_result = calculate_and_update_month(self.session, month.id)
        self.assertEqual(first_result.total_core, 3000.0)
        self.assertEqual(first_result.total_choice, 0.0)

        # ##>: Simulate user correcting category from CORE to CHOICE.
        expense_tx.money_map_type = MoneyMapType.CHOICE.value
        self.session.commit()

        # ##>: Recalculate after category change.
        second_result = calculate_and_update_month(self.session, month.id)
        self.assertEqual(second_result.total_core, 0.0)
        self.assertEqual(second_result.total_choice, 3000.0)


if __name__ == "__main__":
    unittest.main()
