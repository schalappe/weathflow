"""Unit tests for UploadService."""

import os
from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from app.db.enums import MoneyMapType
from app.services.dto.categorization import CategorizationResult
from app.services.dto.parsing import MonthData, ParsedMonthSummary, ParsedTransaction, ParseResult
from app.services.exceptions import InvalidMonthFormatError, NoTransactionsFoundError
from app.services.upload import UploadService
from tests.conftest import DatabaseTestCase

# ##>: Fixture to mock the API key environment variable for categorization tests.
MOCK_API_KEY_ENV = {"ANTHROPIC_API_KEY": "test-key"}


class TestUploadServicePreview(TestCase):
    """Tests for UploadService.get_upload_preview()."""

    @patch("app.services.upload.BankinCSVParser")
    def test_get_upload_preview_returns_correct_month_summaries(self, mock_parser_class: MagicMock) -> None:
        """Preview returns correct structure with month summaries."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=2,
            months={
                "2025-01": MonthData(
                    year=2025,
                    month=1,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 1, 15),
                            description="Salary",
                            account="Main Account",
                            amount=Decimal("3000.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Salaire",
                        ),
                        ParsedTransaction(
                            date=date(2025, 1, 20),
                            description="Groceries",
                            account="Main Account",
                            amount=Decimal("-50.00"),
                            bankin_category="Alimentation",
                            bankin_subcategory="Supermarché",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=1,
                        transaction_count=2,
                        total_income=Decimal("3000.00"),
                        total_expenses=Decimal("50.00"),
                    ),
                ),
            },
        )

        service = UploadService()
        result = service.get_upload_preview(b"csv content")

        self.assertTrue(result["success"])
        self.assertEqual(result["total_transactions"], 2)
        self.assertEqual(len(result["months_detected"]), 1)

        month_summary = result["months_detected"][0]
        self.assertEqual(month_summary["year"], 2025)
        self.assertEqual(month_summary["month"], 1)
        self.assertEqual(month_summary["transaction_count"], 2)
        self.assertEqual(month_summary["total_income"], 3000.00)
        self.assertEqual(month_summary["total_expenses"], 50.00)

    @patch("app.services.upload.BankinCSVParser")
    def test_get_upload_preview_includes_transaction_previews(self, mock_parser_class: MagicMock) -> None:
        """Preview includes transaction details per month."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=1,
            months={
                "2025-02": MonthData(
                    year=2025,
                    month=2,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 2, 10),
                            description="Coffee Shop",
                            account="Card",
                            amount=Decimal("-5.50"),
                            bankin_category="Restauration",
                            bankin_subcategory="Café",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=2,
                        transaction_count=1,
                        total_income=Decimal("0.00"),
                        total_expenses=Decimal("5.50"),
                    ),
                ),
            },
        )

        service = UploadService()
        result = service.get_upload_preview(b"csv content")

        self.assertIn("2025-02", result["preview_by_month"])
        transactions = result["preview_by_month"]["2025-02"]
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["date"], "2025-02-10")
        self.assertEqual(transactions[0]["description"], "Coffee Shop")
        self.assertEqual(transactions[0]["amount"], -5.50)

    @patch("app.services.upload.BankinCSVParser")
    def test_get_upload_preview_raises_on_empty_file(self, mock_parser_class: MagicMock) -> None:
        """Preview raises NoTransactionsFoundError for empty CSV."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(total_transactions=0, months={})

        service = UploadService()
        with self.assertRaises(NoTransactionsFoundError):
            service.get_upload_preview(b"empty csv")


@patch.dict(os.environ, MOCK_API_KEY_ENV)
class TestUploadServiceCategorization(DatabaseTestCase):
    """Tests for UploadService.process_categorization()."""

    @patch("app.services.upload.TransactionCategorizer")
    @patch("app.services.upload.BankinCSVParser")
    def test_process_categorization_categorizes_transactions(
        self, mock_parser_class: MagicMock, mock_categorizer_class: MagicMock
    ) -> None:
        """Categorization correctly processes transactions."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=1,
            months={
                "2025-03": MonthData(
                    year=2025,
                    month=3,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 3, 5),
                            description="Salary",
                            account="Main",
                            amount=Decimal("2500.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Salaire",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=3,
                        transaction_count=1,
                        total_income=Decimal("2500.00"),
                        total_expenses=Decimal("0.00"),
                    ),
                ),
            },
        )

        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        # ##>: Return tuple (results, api_call_count) matching new signature.
        mock_categorizer.categorize.return_value = (
            [
                CategorizationResult(
                    id=1,
                    money_map_type=MoneyMapType.INCOME,
                    money_map_subcategory="Salary",
                    confidence=0.95,
                ),
            ],
            1,
        )

        service = UploadService()
        result = service.process_categorization(
            file_content=b"csv",
            months_to_process=["2025-03"],
            import_mode="replace",
            db=self.session,
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["months_processed"]), 1)
        self.assertEqual(result["months_processed"][0]["year"], 2025)
        self.assertEqual(result["months_processed"][0]["month"], 3)
        self.assertEqual(result["months_processed"][0]["transactions_categorized"], 1)

    @patch("app.services.upload.TransactionCategorizer")
    @patch("app.services.upload.BankinCSVParser")
    def test_process_categorization_handles_all_months(
        self, mock_parser_class: MagicMock, mock_categorizer_class: MagicMock
    ) -> None:
        """Categorization handles 'all' months selection."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=2,
            months={
                "2025-01": MonthData(
                    year=2025,
                    month=1,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 1, 10),
                            description="Income",
                            account="Main",
                            amount=Decimal("1000.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Salaire",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=1,
                        transaction_count=1,
                        total_income=Decimal("1000.00"),
                        total_expenses=Decimal("0.00"),
                    ),
                ),
                "2025-02": MonthData(
                    year=2025,
                    month=2,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 2, 15),
                            description="Expense",
                            account="Main",
                            amount=Decimal("-200.00"),
                            bankin_category="Alimentation",
                            bankin_subcategory="Supermarché",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=2,
                        transaction_count=1,
                        total_income=Decimal("0.00"),
                        total_expenses=Decimal("200.00"),
                    ),
                ),
            },
        )

        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        # ##>: Return tuple (results, api_call_count) matching new signature.
        mock_categorizer.categorize.return_value = (
            [CategorizationResult(id=1, money_map_type=MoneyMapType.INCOME, money_map_subcategory="", confidence=1.0)],
            1,
        )

        service = UploadService()
        result = service.process_categorization(
            file_content=b"csv",
            months_to_process=["all"],
            import_mode="replace",
            db=self.session,
        )

        self.assertEqual(len(result["months_processed"]), 2)

    @patch("app.services.upload.TransactionCategorizer")
    @patch("app.services.upload.BankinCSVParser")
    def test_process_categorization_tracks_api_calls(
        self, mock_parser_class: MagicMock, mock_categorizer_class: MagicMock
    ) -> None:
        """Categorization tracks API call count."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=1,
            months={
                "2025-04": MonthData(
                    year=2025,
                    month=4,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 4, 1),
                            description="Test",
                            account="Main",
                            amount=Decimal("100.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Autre",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=4,
                        transaction_count=1,
                        total_income=Decimal("100.00"),
                        total_expenses=Decimal("0.00"),
                    ),
                ),
            },
        )

        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        # ##>: Return tuple (results, api_call_count) matching new signature.
        mock_categorizer.categorize.return_value = (
            [CategorizationResult(id=1, money_map_type=MoneyMapType.INCOME, money_map_subcategory="", confidence=1.0)],
            2,  # Simulate 2 API calls
        )

        service = UploadService()
        result = service.process_categorization(
            file_content=b"csv",
            months_to_process=["2025-04"],
            import_mode="replace",
            db=self.session,
        )

        self.assertIn("total_api_calls", result)
        self.assertEqual(result["total_api_calls"], 2)


@patch.dict(os.environ, MOCK_API_KEY_ENV)
class TestUploadServiceImportModes(DatabaseTestCase):
    """Tests for import mode functionality."""

    @patch("app.services.upload.TransactionCategorizer")
    @patch("app.services.upload.BankinCSVParser")
    def test_replace_mode_deletes_existing_month(
        self, mock_parser_class: MagicMock, mock_categorizer_class: MagicMock
    ) -> None:
        """Replace mode deletes existing month before insert."""
        from app.db.models.month import Month
        from app.db.models.transaction import Transaction

        # ##>: Create existing month with a transaction.
        existing_month = Month(year=2025, month=5)
        self.session.add(existing_month)
        self.session.commit()

        existing_tx = Transaction(
            month_id=existing_month.id,
            date=date(2025, 5, 1),
            description="Old transaction",
            amount=-100.0,
        )
        self.session.add(existing_tx)
        self.session.commit()

        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=1,
            months={
                "2025-05": MonthData(
                    year=2025,
                    month=5,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 5, 15),
                            description="New transaction",
                            account="Main",
                            amount=Decimal("500.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Autre",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=5,
                        transaction_count=1,
                        total_income=Decimal("500.00"),
                        total_expenses=Decimal("0.00"),
                    ),
                ),
            },
        )

        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        # ##>: Return tuple (results, api_call_count) matching new signature.
        mock_categorizer.categorize.return_value = (
            [CategorizationResult(id=1, money_map_type=MoneyMapType.INCOME, money_map_subcategory="", confidence=1.0)],
            1,
        )

        service = UploadService()
        service.process_categorization(
            file_content=b"csv",
            months_to_process=["2025-05"],
            import_mode="replace",
            db=self.session,
        )

        # ##>: Expire session cache to get fresh data from database.
        self.session.expire_all()

        # ##>: Verify new month exists with only the new transaction (old was replaced).
        new_month = self.session.query(Month).filter(Month.year == 2025, Month.month == 5).first()
        self.assertIsNotNone(new_month)
        # ##>: The key verification: only 1 transaction (the new one), not 2.
        assert new_month is not None
        self.assertEqual(len(new_month.transactions), 1)
        self.assertEqual(new_month.transactions[0].description, "New transaction")
        # ##>: The old transaction should no longer exist.
        old_tx_exists = self.session.query(Transaction).filter(Transaction.description == "Old transaction").first()
        self.assertIsNone(old_tx_exists)

    @patch("app.services.upload.TransactionCategorizer")
    @patch("app.services.upload.BankinCSVParser")
    def test_merge_mode_skips_duplicate_transactions(
        self, mock_parser_class: MagicMock, mock_categorizer_class: MagicMock
    ) -> None:
        """Merge mode skips transactions that already exist."""
        from app.db.models.month import Month
        from app.db.models.transaction import Transaction

        # ##>: Create existing month with a transaction.
        existing_month = Month(year=2025, month=6)
        self.session.add(existing_month)
        self.session.commit()

        existing_tx = Transaction(
            month_id=existing_month.id,
            date=date(2025, 6, 10),
            description="Existing expense",
            amount=-75.0,
            account="Main",
        )
        self.session.add(existing_tx)
        self.session.commit()

        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=2,
            months={
                "2025-06": MonthData(
                    year=2025,
                    month=6,
                    transactions=[
                        # ##>: Duplicate of existing.
                        ParsedTransaction(
                            date=date(2025, 6, 10),
                            description="Existing expense",
                            account="Main",
                            amount=Decimal("-75.00"),
                            bankin_category="Alimentation",
                            bankin_subcategory="Supermarché",
                        ),
                        # ##>: New transaction.
                        ParsedTransaction(
                            date=date(2025, 6, 20),
                            description="New expense",
                            account="Main",
                            amount=Decimal("-50.00"),
                            bankin_category="Alimentation",
                            bankin_subcategory="Supermarché",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=6,
                        transaction_count=2,
                        total_income=Decimal("0.00"),
                        total_expenses=Decimal("125.00"),
                    ),
                ),
            },
        )

        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        # ##>: Return tuple (results, api_call_count) matching new signature.
        mock_categorizer.categorize.return_value = (
            [
                CategorizationResult(id=1, money_map_type=MoneyMapType.CORE, money_map_subcategory="", confidence=1.0),
                CategorizationResult(id=2, money_map_type=MoneyMapType.CORE, money_map_subcategory="", confidence=1.0),
            ],
            1,
        )

        service = UploadService()
        result = service.process_categorization(
            file_content=b"csv",
            months_to_process=["2025-06"],
            import_mode="merge",
            db=self.session,
        )

        # ##>: Should only insert 1 new transaction (skip duplicate).
        self.assertEqual(result["months_processed"][0]["transactions_categorized"], 1)

        # ##>: Month should have 2 total transactions.
        month = self.session.query(Month).filter(Month.year == 2025, Month.month == 6).first()
        assert month is not None
        self.assertEqual(len(month.transactions), 2)

    @patch("app.services.upload.TransactionCategorizer")
    @patch("app.services.upload.BankinCSVParser")
    def test_merge_mode_inserts_only_new_transactions(
        self, mock_parser_class: MagicMock, mock_categorizer_class: MagicMock
    ) -> None:
        """Merge mode inserts new transactions when no duplicates."""
        from app.db.models.month import Month

        # ##>: Create empty existing month.
        existing_month = Month(year=2025, month=7)
        self.session.add(existing_month)
        self.session.commit()

        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=1,
            months={
                "2025-07": MonthData(
                    year=2025,
                    month=7,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 7, 5),
                            description="Brand new transaction",
                            account="Main",
                            amount=Decimal("200.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Autre",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=7,
                        transaction_count=1,
                        total_income=Decimal("200.00"),
                        total_expenses=Decimal("0.00"),
                    ),
                ),
            },
        )

        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        # ##>: Return tuple (results, api_call_count) matching new signature.
        mock_categorizer.categorize.return_value = (
            [CategorizationResult(id=1, money_map_type=MoneyMapType.INCOME, money_map_subcategory="", confidence=1.0)],
            1,
        )

        service = UploadService()
        result = service.process_categorization(
            file_content=b"csv",
            months_to_process=["2025-07"],
            import_mode="merge",
            db=self.session,
        )

        self.assertEqual(result["months_processed"][0]["transactions_categorized"], 1)


class TestUploadServiceValidation(TestCase):
    """Tests for input validation."""

    @patch("app.services.upload.BankinCSVParser")
    def test_invalid_month_format_raises_error(self, mock_parser_class: MagicMock) -> None:
        """Invalid month format raises InvalidMonthFormatError."""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParseResult(
            total_transactions=1,
            months={
                "2025-01": MonthData(
                    year=2025,
                    month=1,
                    transactions=[
                        ParsedTransaction(
                            date=date(2025, 1, 1),
                            description="Test",
                            account="Main",
                            amount=Decimal("100.00"),
                            bankin_category="Revenus",
                            bankin_subcategory="Autre",
                        ),
                    ],
                    summary=ParsedMonthSummary(
                        year=2025,
                        month=1,
                        transaction_count=1,
                        total_income=Decimal("100.00"),
                        total_expenses=Decimal("0.00"),
                    ),
                ),
            },
        )

        service = UploadService()
        with self.assertRaises(InvalidMonthFormatError) as context:
            service.process_categorization(
                file_content=b"csv",
                months_to_process=["invalid-format"],
                import_mode="replace",
                db=MagicMock(),
            )

        self.assertEqual(context.exception.value, "invalid-format")


class TestLowConfidenceTracking(TestCase):
    """Tests for low confidence count tracking."""

    def test_count_low_confidence(self) -> None:
        """Correctly counts results below confidence threshold."""
        service = UploadService()
        results = [
            CategorizationResult(id=1, money_map_type=MoneyMapType.INCOME, money_map_subcategory="", confidence=0.95),
            CategorizationResult(id=2, money_map_type=MoneyMapType.CORE, money_map_subcategory="", confidence=0.75),
            CategorizationResult(id=3, money_map_type=MoneyMapType.CHOICE, money_map_subcategory="", confidence=0.60),
            CategorizationResult(id=4, money_map_type=MoneyMapType.INCOME, money_map_subcategory="", confidence=0.85),
        ]

        count = service._count_low_confidence(results)

        # ##>: 0.75, 0.60 are below 0.8 threshold.
        self.assertEqual(count, 2)
