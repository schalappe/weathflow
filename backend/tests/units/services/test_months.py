"""Tests for months service query functions."""

from datetime import date

import pytest

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.month_repository import MonthRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services import months as months_service
from app.services.exceptions import InvalidCategoryTypeError
from tests.conftest import DatabaseTestCase


class TestEscapeLikePattern:
    """Tests for _escape_like_pattern SQL LIKE escape function (now in TransactionRepository)."""

    def test_escapes_percent_wildcard(self) -> None:
        """Should escape % to prevent SQL wildcard matching."""
        result = TransactionRepository._escape_like_pattern("100%")
        assert result == "100\\%"

    def test_escapes_underscore_wildcard(self) -> None:
        """Should escape _ to prevent single-char wildcard matching."""
        result = TransactionRepository._escape_like_pattern("test_user")
        assert result == "test\\_user"

    def test_escapes_backslash(self) -> None:
        """Should escape backslash before escaping wildcards."""
        result = TransactionRepository._escape_like_pattern("path\\file")
        assert result == "path\\\\file"

    def test_preserves_normal_characters(self) -> None:
        """Should not modify strings without special characters."""
        result = TransactionRepository._escape_like_pattern("normal search")
        assert result == "normal search"

    def test_handles_mixed_special_characters(self) -> None:
        """Should escape all special chars in correct order."""
        result = TransactionRepository._escape_like_pattern("50%_discount\\sale")
        # ##>: Backslash escaped first, then % and _.
        assert result == "50\\%\\_discount\\\\sale"

    def test_handles_empty_string(self) -> None:
        """Should return empty string unchanged."""
        result = TransactionRepository._escape_like_pattern("")
        assert result == ""

    def test_handles_multiple_consecutive_wildcards(self) -> None:
        """Should escape multiple consecutive wildcard characters."""
        result = TransactionRepository._escape_like_pattern("%%__")
        assert result == "\\%\\%\\_\\_"


class TestGetAllMonthsWithCounts(DatabaseTestCase):
    """Tests for get_all_months_with_counts function."""

    def test_returns_months_ordered_by_date_desc(self) -> None:
        """Should return months ordered by year desc, month desc."""
        # ##>: Create months in non-chronological order.
        month_jan = Month(year=2025, month=1, score=2, score_label="Okay")
        month_oct = Month(year=2025, month=10, score=3, score_label="Great")
        month_dec_2024 = Month(year=2024, month=12, score=1, score_label="Need Improvement")
        self.session.add_all([month_jan, month_oct, month_dec_2024])
        self.session.commit()

        month_repo = MonthRepository(self.session)
        result = months_service.get_all_months_with_counts(month_repo)

        self.assertEqual(len(result), 3)
        # ##>: Order should be: 2025-10, 2025-01, 2024-12.
        self.assertEqual(result[0][0].year, 2025)
        self.assertEqual(result[0][0].month, 10)
        self.assertEqual(result[1][0].year, 2025)
        self.assertEqual(result[1][0].month, 1)
        self.assertEqual(result[2][0].year, 2024)
        self.assertEqual(result[2][0].month, 12)

    def test_returns_correct_transaction_counts(self) -> None:
        """Should return correct transaction count for each month."""
        month1 = Month(year=2025, month=10, score=3, score_label="Great")
        month2 = Month(year=2025, month=9, score=2, score_label="Okay")
        self.session.add_all([month1, month2])
        self.session.commit()

        # ##>: Add 3 transactions to month1, 1 to month2.
        tx1 = Transaction(month_id=month1.id, date=date(2025, 10, 1), description="Tx1", amount=100.0)
        tx2 = Transaction(month_id=month1.id, date=date(2025, 10, 2), description="Tx2", amount=200.0)
        tx3 = Transaction(month_id=month1.id, date=date(2025, 10, 3), description="Tx3", amount=300.0)
        tx4 = Transaction(month_id=month2.id, date=date(2025, 9, 1), description="Tx4", amount=400.0)
        self.session.add_all([tx1, tx2, tx3, tx4])
        self.session.commit()

        month_repo = MonthRepository(self.session)
        result = months_service.get_all_months_with_counts(month_repo)

        # ##>: Ordered by date desc: 2025-10 (3 tx), 2025-09 (1 tx).
        self.assertEqual(result[0][1], 3)  # month1 has 3 transactions
        self.assertEqual(result[1][1], 1)  # month2 has 1 transaction


class TestGetMonthByYearMonth(DatabaseTestCase):
    """Tests for get_month_by_year_month function."""

    def test_returns_none_when_not_found(self) -> None:
        """Should return None when month does not exist."""
        month_repo = MonthRepository(self.session)
        result = months_service.get_month_by_year_month(month_repo, year=2025, month=10)

        self.assertIsNone(result)

    def test_returns_month_when_found(self) -> None:
        """Should return Month when it exists."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        self.session.add(month)
        self.session.commit()

        month_repo = MonthRepository(self.session)
        result = months_service.get_month_by_year_month(month_repo, year=2025, month=10)

        self.assertIsNotNone(result)
        assert result is not None  # ##>: Type narrowing for mypy.
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.score, 3)


class TestGetTransactionsFiltered(DatabaseTestCase):
    """Tests for get_transactions_filtered function."""

    def setUp(self) -> None:
        """Set up test data with a month and multiple transactions."""
        super().setUp()
        self.month = Month(year=2025, month=10, score=3, score_label="Great")
        self.session.add(self.month)
        self.session.commit()

        # ##>: Create diverse transactions for filtering tests.
        self.transactions = [
            Transaction(
                month_id=self.month.id,
                date=date(2025, 10, 1),
                description="SALARY COMPANY",
                amount=5000.0,
                money_map_type=MoneyMapType.INCOME.value,
            ),
            Transaction(
                month_id=self.month.id,
                date=date(2025, 10, 5),
                description="CARREFOUR GROCERIES",
                amount=-150.0,
                money_map_type=MoneyMapType.CORE.value,
            ),
            Transaction(
                month_id=self.month.id,
                date=date(2025, 10, 10),
                description="RENT PAYMENT",
                amount=-1500.0,
                money_map_type=MoneyMapType.CORE.value,
            ),
            Transaction(
                month_id=self.month.id,
                date=date(2025, 10, 15),
                description="RESTAURANT MCDONALDS",
                amount=-25.0,
                money_map_type=MoneyMapType.CHOICE.value,
            ),
            Transaction(
                month_id=self.month.id,
                date=date(2025, 10, 20),
                description="NETFLIX SUBSCRIPTION",
                amount=-15.0,
                money_map_type=MoneyMapType.CHOICE.value,
            ),
        ]
        self.session.add_all(self.transactions)
        self.session.commit()

    def test_applies_category_filter_correctly(self) -> None:
        """Should filter transactions by category_types (single category)."""
        transaction_repo = TransactionRepository(self.session)
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            category_types=[MoneyMapType.CORE.value],
        )

        self.assertEqual(total_count, 2)
        self.assertEqual(len(transactions), 2)
        for tx in transactions:
            self.assertEqual(tx.money_map_type, MoneyMapType.CORE.value)

    def test_returns_correct_pagination_tuple(self) -> None:
        """Should return correct transactions and total count for pagination."""
        transaction_repo = TransactionRepository(self.session)

        # ##>: Request page 1 with page_size 2.
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            page=1,
            page_size=2,
        )

        # ##>: Total count should reflect all transactions, not just current page.
        self.assertEqual(total_count, 5)
        self.assertEqual(len(transactions), 2)

        # ##>: Page 2 should have next 2 transactions.
        transactions_p2, total_count_p2 = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            page=2,
            page_size=2,
        )

        self.assertEqual(total_count_p2, 5)
        self.assertEqual(len(transactions_p2), 2)

        # ##>: Page 3 should have the last transaction.
        transactions_p3, total_count_p3 = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            page=3,
            page_size=2,
        )

        self.assertEqual(total_count_p3, 5)
        self.assertEqual(len(transactions_p3), 1)

    def test_search_filter_case_insensitive(self) -> None:
        """Should filter by description using case-insensitive search."""
        transaction_repo = TransactionRepository(self.session)

        # ##>: Search for "carrefour" (lowercase) should match "CARREFOUR GROCERIES".
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            search="carrefour",
        )

        self.assertEqual(total_count, 1)
        self.assertIn("CARREFOUR", transactions[0].description)

    def test_date_range_filter(self) -> None:
        """Should filter transactions by date range."""
        transaction_repo = TransactionRepository(self.session)
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            start_date=date(2025, 10, 5),
            end_date=date(2025, 10, 15),
        )

        # ##>: Should include transactions on 5th, 10th, and 15th.
        self.assertEqual(total_count, 3)

    def test_combined_filters(self) -> None:
        """Should apply multiple filters with AND logic."""
        transaction_repo = TransactionRepository(self.session)
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            category_types=[MoneyMapType.CHOICE.value],
            search="netflix",
        )

        self.assertEqual(total_count, 1)
        self.assertIn("NETFLIX", transactions[0].description)

    def test_returns_transactions_ordered_by_date_desc(self) -> None:
        """Should return transactions ordered by date descending."""
        transaction_repo = TransactionRepository(self.session)
        transactions, _ = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
        )

        # ##>: Latest transaction (20th) should be first.
        self.assertEqual(transactions[0].date, date(2025, 10, 20))
        self.assertEqual(transactions[-1].date, date(2025, 10, 1))

    def test_multi_category_filter_returns_union(self) -> None:
        """Should return transactions matching any of the specified categories (union)."""
        transaction_repo = TransactionRepository(self.session)
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            category_types=[MoneyMapType.CORE.value, MoneyMapType.CHOICE.value],
        )

        # ##>: Should return 2 CORE + 2 CHOICE = 4 transactions.
        self.assertEqual(total_count, 4)
        self.assertEqual(len(transactions), 4)
        category_types = {tx.money_map_type for tx in transactions}
        self.assertEqual(category_types, {MoneyMapType.CORE.value, MoneyMapType.CHOICE.value})

    def test_empty_category_list_returns_all(self) -> None:
        """Should return all transactions when category_types is empty list."""
        transaction_repo = TransactionRepository(self.session)
        transactions, total_count = months_service.get_transactions_filtered(
            transaction_repo,
            month_id=self.month.id,
            category_types=[],
        )

        # ##>: Empty list means no filter, should return all 5 transactions.
        self.assertEqual(total_count, 5)
        self.assertEqual(len(transactions), 5)

    def test_invalid_category_values_raise_error(self) -> None:
        """Should raise InvalidCategoryTypeError when invalid category values provided."""
        transaction_repo = TransactionRepository(self.session)
        with pytest.raises(InvalidCategoryTypeError) as exc_info:
            months_service.get_transactions_filtered(
                transaction_repo,
                month_id=self.month.id,
                category_types=["INVALID_TYPE", MoneyMapType.CORE.value],
            )

        # ##>: Error should contain the invalid type and list valid types.
        error = exc_info.value
        self.assertEqual(error.invalid_types, ["INVALID_TYPE"])
        self.assertIn("CORE", error.valid_types)
        self.assertIn("INCOME", error.valid_types)

    def test_all_invalid_categories_raise_error(self) -> None:
        """Should raise InvalidCategoryTypeError when all category values are invalid."""
        transaction_repo = TransactionRepository(self.session)
        with pytest.raises(InvalidCategoryTypeError) as exc_info:
            months_service.get_transactions_filtered(
                transaction_repo,
                month_id=self.month.id,
                category_types=["INVALID1", "INVALID2"],
            )

        # ##>: Error should list all invalid types.
        error = exc_info.value
        self.assertEqual(set(error.invalid_types), {"INVALID1", "INVALID2"})
