"""Unit tests for TransactionRepository."""

from datetime import date

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from tests.conftest import DatabaseTestCase


class TestTransactionRepository(DatabaseTestCase):
    """Test cases for TransactionRepository data access operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        self.month = Month(year=2025, month=1)
        self.session.add(self.month)
        self.session.commit()

    def test_get_by_id_returns_transaction(self) -> None:
        """get_by_id returns transaction when it exists."""
        tx = Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="Test", amount=100.0)
        self.session.add(tx)
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.get_by_id(tx.id)

        assert result is not None
        assert result.description == "Test"

    def test_get_by_id_returns_none_for_missing(self) -> None:
        """get_by_id returns None when transaction does not exist."""
        repo = TransactionRepository(self.session)
        result = repo.get_by_id(999)

        assert result is None

    def test_get_filtered_returns_transactions_for_month(self) -> None:
        """get_filtered returns all transactions for specified month."""
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="Tx1", amount=100.0))
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 2), description="Tx2", amount=200.0))
        self.session.commit()

        repo = TransactionRepository(self.session)
        transactions, total = repo.get_filtered(self.month.id)

        assert len(transactions) == 2
        assert total == 2

    def test_get_filtered_filters_by_category_types(self) -> None:
        """get_filtered filters by money_map_type when provided."""
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 1),
                description="Income",
                amount=1000.0,
                money_map_type=MoneyMapType.INCOME.value,
            )
        )
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 2),
                description="Rent",
                amount=-500.0,
                money_map_type=MoneyMapType.CORE.value,
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        transactions, total = repo.get_filtered(self.month.id, category_types=[MoneyMapType.INCOME.value])

        assert len(transactions) == 1
        assert transactions[0].description == "Income"
        assert total == 1

    def test_get_filtered_filters_by_search(self) -> None:
        """get_filtered filters by description search."""
        self.session.add(
            Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="Grocery store", amount=-50.0)
        )
        self.session.add(
            Transaction(month_id=self.month.id, date=date(2025, 1, 2), description="Gas station", amount=-40.0)
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        transactions, total = repo.get_filtered(self.month.id, search="grocery")

        assert len(transactions) == 1
        assert "Grocery" in transactions[0].description
        assert total == 1

    def test_get_filtered_filters_by_date_range(self) -> None:
        """get_filtered filters by date range."""
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="Early", amount=100.0))
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 15), description="Mid", amount=200.0))
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 31), description="Late", amount=300.0))
        self.session.commit()

        repo = TransactionRepository(self.session)
        transactions, total = repo.get_filtered(
            self.month.id, start_date=date(2025, 1, 10), end_date=date(2025, 1, 20)
        )

        assert len(transactions) == 1
        assert transactions[0].description == "Mid"
        assert total == 1

    def test_get_filtered_paginates_correctly(self) -> None:
        """get_filtered respects page and page_size."""
        for i in range(10):
            self.session.add(
                Transaction(month_id=self.month.id, date=date(2025, 1, i + 1), description=f"Tx{i}", amount=100.0)
            )
        self.session.commit()

        repo = TransactionRepository(self.session)
        transactions, total = repo.get_filtered(self.month.id, page=2, page_size=3)

        assert len(transactions) == 3
        assert total == 10

    def test_get_filtered_orders_by_date_asc(self) -> None:
        """get_filtered orders transactions by date ascending."""
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="First", amount=100.0))
        self.session.add(
            Transaction(month_id=self.month.id, date=date(2025, 1, 15), description="Second", amount=200.0)
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        transactions, _ = repo.get_filtered(self.month.id)

        assert transactions[0].description == "First"  # Oldest first
        assert transactions[1].description == "Second"

    def test_get_all_for_month_returns_all_transactions(self) -> None:
        """get_all_for_month returns all transactions without pagination."""
        for i in range(5):
            self.session.add(
                Transaction(month_id=self.month.id, date=date(2025, 1, i + 1), description=f"Tx{i}", amount=100.0)
            )
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.get_all_for_month(self.month.id)

        assert len(result) == 5

    def test_aggregate_totals_calculates_income_core_choice(self) -> None:
        """aggregate_totals returns correct income, core, choice totals."""
        # Income (positive)
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 1),
                description="Salary",
                amount=5000.0,
                money_map_type=MoneyMapType.INCOME.value,
            )
        )
        # Core (negative)
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 2),
                description="Rent",
                amount=-1500.0,
                money_map_type=MoneyMapType.CORE.value,
            )
        )
        # Choice (negative)
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 3),
                description="Restaurant",
                amount=-200.0,
                money_map_type=MoneyMapType.CHOICE.value,
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        income, core, choice = repo.aggregate_totals(self.month.id)

        assert income == 5000.0
        assert core == 1500.0  # Absolute value
        assert choice == 200.0  # Absolute value

    def test_aggregate_totals_returns_zeros_for_empty_month(self) -> None:
        """aggregate_totals returns zeros when month has no transactions."""
        repo = TransactionRepository(self.session)
        income, core, choice = repo.aggregate_totals(self.month.id)

        assert income == 0.0
        assert core == 0.0
        assert choice == 0.0

    def test_add_bulk_adds_multiple_transactions(self) -> None:
        """add_bulk adds multiple transactions at once."""
        transactions = [
            Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="Tx1", amount=100.0),
            Transaction(month_id=self.month.id, date=date(2025, 1, 2), description="Tx2", amount=200.0),
            Transaction(month_id=self.month.id, date=date(2025, 1, 3), description="Tx3", amount=300.0),
        ]

        repo = TransactionRepository(self.session)
        repo.add_bulk(transactions)
        repo.flush()
        self.session.commit()

        all_tx = repo.get_all_for_month(self.month.id)
        assert len(all_tx) == 3

    def test_delete_for_month_removes_all_transactions(self) -> None:
        """delete_for_month removes all transactions for specified month."""
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 1), description="Tx1", amount=100.0))
        self.session.add(Transaction(month_id=self.month.id, date=date(2025, 1, 2), description="Tx2", amount=200.0))
        self.session.commit()

        repo = TransactionRepository(self.session)
        count = repo.delete_for_month(self.month.id)
        self.session.commit()

        assert count == 2
        assert len(repo.get_all_for_month(self.month.id)) == 0

    def test_get_keys_for_month_returns_unique_keys(self) -> None:
        """get_keys_for_month returns transaction keys for deduplication."""
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 1),
                description="Tx1",
                amount=100.0,
                account="Account1",
            )
        )
        self.session.add(
            Transaction(
                month_id=self.month.id,
                date=date(2025, 1, 2),
                description="Tx2",
                amount=200.0,
                account="Account2",
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        keys = repo.get_keys_for_month(self.month.id)

        assert len(keys) == 2
        assert "2025-01-01_Tx1_100.0_Account1" in keys
        assert "2025-01-02_Tx2_200.0_Account2" in keys

    def test_escape_like_pattern_escapes_wildcards(self) -> None:
        """_escape_like_pattern escapes SQL LIKE wildcards."""
        assert TransactionRepository._escape_like_pattern("test%value") == "test\\%value"
        assert TransactionRepository._escape_like_pattern("test_value") == "test\\_value"
        assert TransactionRepository._escape_like_pattern("test\\value") == "test\\\\value"


class TestAggregateBySubcategory(DatabaseTestCase):
    """Test cases for aggregate_by_subcategory repository method."""

    def setUp(self) -> None:
        """Set up test fixtures with multiple months."""
        super().setUp()
        self.month1 = Month(year=2025, month=1)
        self.month2 = Month(year=2025, month=2)
        self.session.add_all([self.month1, self.month2])
        self.session.commit()

    def test_returns_grouped_data_by_type_and_subcategory(self) -> None:
        """aggregate_by_subcategory returns data grouped by type and subcategory."""
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 1),
                description="Rent",
                amount=-1200.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Housing",
            )
        )
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 5),
                description="Carrefour",
                amount=-150.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Groceries",
            )
        )
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 10),
                description="Restaurant",
                amount=-50.0,
                money_map_type=MoneyMapType.CHOICE.value,
                money_map_subcategory="Dining out",
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.aggregate_by_subcategory([self.month1.id])

        assert len(result) == 3
        result_dict = {(r[0], r[1]): r[2] for r in result}
        assert result_dict[(MoneyMapType.CORE.value, "Housing")] == 1200.0
        assert result_dict[(MoneyMapType.CORE.value, "Groceries")] == 150.0
        assert result_dict[(MoneyMapType.CHOICE.value, "Dining out")] == 50.0

    def test_returns_empty_list_for_empty_month_ids(self) -> None:
        """aggregate_by_subcategory returns empty list when month_ids is empty."""
        repo = TransactionRepository(self.session)
        result = repo.aggregate_by_subcategory([])

        assert result == []

    def test_excludes_excluded_transactions(self) -> None:
        """aggregate_by_subcategory filters out EXCLUDED transactions."""
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 1),
                description="Internal transfer",
                amount=-500.0,
                money_map_type=MoneyMapType.EXCLUDED.value,
                money_map_subcategory="Transfer",
            )
        )
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 5),
                description="Rent",
                amount=-1000.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Housing",
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.aggregate_by_subcategory([self.month1.id])

        assert len(result) == 1
        assert result[0][0] == MoneyMapType.CORE.value

    def test_returns_absolute_values_for_expenses(self) -> None:
        """aggregate_by_subcategory returns absolute values for negative amounts."""
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 1),
                description="Rent",
                amount=-1500.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Housing",
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.aggregate_by_subcategory([self.month1.id])

        assert result[0][2] == 1500.0

    def test_aggregates_across_multiple_months(self) -> None:
        """aggregate_by_subcategory sums across multiple months."""
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 1),
                description="Rent Jan",
                amount=-1200.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Housing",
            )
        )
        self.session.add(
            Transaction(
                month_id=self.month2.id,
                date=date(2025, 2, 1),
                description="Rent Feb",
                amount=-1200.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Housing",
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.aggregate_by_subcategory([self.month1.id, self.month2.id])

        assert len(result) == 1
        assert result[0][2] == 2400.0

    def test_includes_income_with_positive_amounts(self) -> None:
        """aggregate_by_subcategory includes INCOME type with positive amounts."""
        self.session.add(
            Transaction(
                month_id=self.month1.id,
                date=date(2025, 1, 1),
                description="Salary",
                amount=5000.0,
                money_map_type=MoneyMapType.INCOME.value,
                money_map_subcategory="Job",
            )
        )
        self.session.commit()

        repo = TransactionRepository(self.session)
        result = repo.aggregate_by_subcategory([self.month1.id])

        assert len(result) == 1
        assert result[0][0] == MoneyMapType.INCOME.value
        assert result[0][2] == 5000.0
