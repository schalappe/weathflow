"""Tests for CSV parsing Pydantic schemas."""

import unittest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from app.services.schemas import MonthData, MonthSummary, ParsedTransaction, ParseResult


class TestParsedTransaction(unittest.TestCase):
    """Tests for ParsedTransaction model."""

    def test_create_with_all_required_fields(self) -> None:
        """Should create a transaction with all required fields."""
        transaction = ParsedTransaction(
            date=date(2025, 10, 15),
            description="Grocery shopping",
            account="Checking",
            amount=Decimal("-50.00"),
            bankin_category="Food",
            bankin_subcategory="Groceries",
        )

        self.assertEqual(transaction.date, date(2025, 10, 15))
        self.assertEqual(transaction.description, "Grocery shopping")
        self.assertEqual(transaction.amount, Decimal("-50.00"))

    def test_note_defaults_to_none(self) -> None:
        """Should default note to None when not provided."""
        transaction = ParsedTransaction(
            date=date(2025, 10, 15),
            description="Test",
            account="Test",
            amount=Decimal("100.00"),
            bankin_category="Test",
            bankin_subcategory="Test",
        )

        self.assertIsNone(transaction.note)

    def test_is_pointed_defaults_to_false(self) -> None:
        """Should default is_pointed to False when not provided."""
        transaction = ParsedTransaction(
            date=date(2025, 10, 15),
            description="Test",
            account="Test",
            amount=Decimal("100.00"),
            bankin_category="Test",
            bankin_subcategory="Test",
        )

        self.assertFalse(transaction.is_pointed)

    def test_immutable_raises_on_modification(self) -> None:
        """Should raise error when attempting to modify frozen model."""
        transaction = ParsedTransaction(
            date=date(2025, 10, 15),
            description="Test",
            account="Test",
            amount=Decimal("100.00"),
            bankin_category="Test",
            bankin_subcategory="Test",
        )

        with self.assertRaises(ValidationError):
            transaction.amount = Decimal("200.00")

    def test_accepts_optional_note(self) -> None:
        """Should accept a note when provided."""
        transaction = ParsedTransaction(
            date=date(2025, 10, 15),
            description="Test",
            account="Test",
            amount=Decimal("100.00"),
            bankin_category="Test",
            bankin_subcategory="Test",
            note="Important transaction",
        )

        self.assertEqual(transaction.note, "Important transaction")


class TestMonthSummary(unittest.TestCase):
    """Tests for MonthSummary model."""

    def test_create_with_all_fields(self) -> None:
        """Should create a summary with all required fields."""
        summary = MonthSummary(
            year=2025,
            month=10,
            transaction_count=15,
            total_income=Decimal("3000.00"),
            total_expenses=Decimal("2500.00"),
        )

        self.assertEqual(summary.year, 2025)
        self.assertEqual(summary.month, 10)
        self.assertEqual(summary.transaction_count, 15)
        self.assertEqual(summary.total_income, Decimal("3000.00"))
        self.assertEqual(summary.total_expenses, Decimal("2500.00"))

    def test_immutable_raises_on_modification(self) -> None:
        """Should raise error when attempting to modify frozen model."""
        summary = MonthSummary(
            year=2025,
            month=10,
            transaction_count=15,
            total_income=Decimal("3000.00"),
            total_expenses=Decimal("2500.00"),
        )

        with self.assertRaises(ValidationError):
            summary.total_income = Decimal("5000.00")


class TestMonthData(unittest.TestCase):
    """Tests for MonthData model."""

    def test_create_with_transactions_and_summary(self) -> None:
        """Should create month data with transactions and summary."""
        transaction = ParsedTransaction(
            date=date(2025, 10, 15),
            description="Test",
            account="Test",
            amount=Decimal("-50.00"),
            bankin_category="Test",
            bankin_subcategory="Test",
        )
        summary = MonthSummary(
            year=2025,
            month=10,
            transaction_count=1,
            total_income=Decimal("0.00"),
            total_expenses=Decimal("50.00"),
        )

        month_data = MonthData(
            year=2025,
            month=10,
            transactions=[transaction],
            summary=summary,
        )

        self.assertEqual(month_data.year, 2025)
        self.assertEqual(len(month_data.transactions), 1)
        self.assertEqual(month_data.summary.total_expenses, Decimal("50.00"))

    def test_immutable_raises_on_modification(self) -> None:
        """Should raise error when attempting to modify frozen model."""
        summary = MonthSummary(
            year=2025,
            month=10,
            transaction_count=0,
            total_income=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
        )
        month_data = MonthData(
            year=2025,
            month=10,
            transactions=[],
            summary=summary,
        )

        with self.assertRaises(ValidationError):
            month_data.year = 2024


class TestParseResult(unittest.TestCase):
    """Tests for ParseResult model."""

    def test_create_with_months_dict(self) -> None:
        """Should create parse result with months dictionary."""
        summary = MonthSummary(
            year=2025,
            month=10,
            transaction_count=0,
            total_income=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
        )
        month_data = MonthData(
            year=2025,
            month=10,
            transactions=[],
            summary=summary,
        )

        result = ParseResult(
            total_transactions=0,
            months={"2025-10": month_data},
        )

        self.assertEqual(result.total_transactions, 0)
        self.assertIn("2025-10", result.months)
        self.assertEqual(result.months["2025-10"].year, 2025)

    def test_immutable_raises_on_modification(self) -> None:
        """Should raise error when attempting to modify frozen model."""
        result = ParseResult(
            total_transactions=0,
            months={},
        )

        with self.assertRaises(ValidationError):
            result.total_transactions = 10
