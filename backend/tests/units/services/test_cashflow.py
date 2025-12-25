"""Unit tests for cashflow service functions."""

from unittest import TestCase

from app.db.enums import MoneyMapType
from app.services.data.cashflow import _build_cashflow_data


class TestBuildCashflowData(TestCase):
    """Test cases for _build_cashflow_data service function."""

    def test_empty_aggregated_returns_zeros(self) -> None:
        """_build_cashflow_data returns zeros when aggregated list is empty."""
        result = _build_cashflow_data([])

        assert result.income_total == 0.0
        assert result.core_total == 0.0
        assert result.choice_total == 0.0
        assert result.compound_total == 0.0
        assert result.deficit == 0.0
        assert result.core_breakdown == []
        assert result.choice_breakdown == []
        assert result.compound_breakdown == []

    def test_calculates_category_totals(self) -> None:
        """_build_cashflow_data correctly sums totals by category."""
        aggregated: list[tuple[str, str | None, float]] = [
            (MoneyMapType.INCOME.value, "Job", 5000.0),
            (MoneyMapType.CORE.value, "Housing", 1200.0),
            (MoneyMapType.CORE.value, "Groceries", 300.0),
            (MoneyMapType.CHOICE.value, "Dining out", 150.0),
            (MoneyMapType.COMPOUND.value, "Investments", 1000.0),
        ]

        result = _build_cashflow_data(aggregated)

        assert result.income_total == 5000.0
        assert result.core_total == 1500.0
        assert result.choice_total == 150.0
        # [>]: compound_total is calculated as INCOME - (CORE + CHOICE), not from transactions.
        assert result.compound_total == 5000.0 - (1500.0 + 150.0)  # 3350.0
        assert result.deficit == 0.0
        # [>]: compound_breakdown retains actual savings transactions for subcategory display.
        assert len(result.compound_breakdown) == 1
        assert result.compound_breakdown[0].subcategory == "Investments"
        assert result.compound_breakdown[0].amount == 1000.0

    def test_builds_breakdowns(self) -> None:
        """_build_cashflow_data correctly builds subcategory breakdowns."""
        aggregated: list[tuple[str, str | None, float]] = [
            (MoneyMapType.INCOME.value, "Job", 5000.0),
            (MoneyMapType.CORE.value, "Housing", 1200.0),
            (MoneyMapType.CORE.value, "Groceries", 300.0),
            (MoneyMapType.CHOICE.value, "Dining out", 150.0),
            (MoneyMapType.COMPOUND.value, "Investments", 1000.0),
        ]

        result = _build_cashflow_data(aggregated)

        assert len(result.core_breakdown) == 2
        assert len(result.choice_breakdown) == 1
        assert len(result.compound_breakdown) == 1

        core_subcats = {b.subcategory: b.amount for b in result.core_breakdown}
        assert core_subcats["Housing"] == 1200.0
        assert core_subcats["Groceries"] == 300.0

    def test_calculates_deficit_when_spending_exceeds_income(self) -> None:
        """_build_cashflow_data calculates deficit when Core + Choice > Income."""
        aggregated: list[tuple[str, str | None, float]] = [
            (MoneyMapType.INCOME.value, "Job", 3000.0),
            (MoneyMapType.CORE.value, "Housing", 2500.0),
            (MoneyMapType.CHOICE.value, "Dining out", 1000.0),
        ]

        result = _build_cashflow_data(aggregated)

        assert result.income_total == 3000.0
        assert result.core_total == 2500.0
        assert result.choice_total == 1000.0
        assert result.compound_total == 0.0
        assert result.deficit == 500.0
        assert result.compound_breakdown == []

    def test_clears_compound_when_deficit_exists(self) -> None:
        """_build_cashflow_data clears compound breakdown when deficit exists."""
        aggregated: list[tuple[str, str | None, float]] = [
            (MoneyMapType.INCOME.value, "Job", 2000.0),
            (MoneyMapType.CORE.value, "Housing", 2500.0),
            (MoneyMapType.COMPOUND.value, "Investments", 500.0),
        ]

        result = _build_cashflow_data(aggregated)

        # [>]: Even though compound was provided, it should be cleared due to deficit.
        assert result.deficit == 500.0
        assert result.compound_total == 0.0
        assert result.compound_breakdown == []

    def test_handles_null_subcategory(self) -> None:
        """_build_cashflow_data treats None subcategory as 'Other'."""
        aggregated = [
            (MoneyMapType.INCOME.value, "Job", 5000.0),
            (MoneyMapType.CORE.value, None, 1000.0),
        ]

        result = _build_cashflow_data(aggregated)

        assert len(result.core_breakdown) == 1
        assert result.core_breakdown[0].subcategory == "Other"
        assert result.core_breakdown[0].amount == 1000.0
