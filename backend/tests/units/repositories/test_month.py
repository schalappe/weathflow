"""Unit tests for MonthRepository."""

from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.month import MonthRepository
from tests.conftest import DatabaseTestCase


class TestMonthRepository(DatabaseTestCase):
    """Test cases for MonthRepository data access operations."""

    def test_get_by_id_returns_month(self) -> None:
        """get_by_id returns month when it exists."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_by_id(month.id)

        assert result is not None
        assert result.id == month.id
        assert result.year == 2025
        assert result.month == 1

    def test_get_by_id_returns_none_for_missing(self) -> None:
        """get_by_id returns None when month does not exist."""
        repo = MonthRepository(self.session)
        result = repo.get_by_id(999)

        assert result is None

    def test_get_by_year_month_returns_month(self) -> None:
        """get_by_year_month finds month by year and month."""
        month = Month(year=2025, month=3)
        self.session.add(month)
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_by_year_month(2025, 3)

        assert result is not None
        assert result.year == 2025
        assert result.month == 3

    def test_get_by_year_month_returns_none_for_missing(self) -> None:
        """get_by_year_month returns None when month does not exist."""
        repo = MonthRepository(self.session)
        result = repo.get_by_year_month(2025, 12)

        assert result is None

    def test_get_all_with_transaction_counts_returns_empty_list(self) -> None:
        """get_all_with_transaction_counts returns empty list when no months."""
        repo = MonthRepository(self.session)
        result = repo.get_all_with_transaction_counts()

        assert result == []

    def test_get_all_with_transaction_counts_orders_by_date_desc(self) -> None:
        """get_all_with_transaction_counts orders by year desc, month desc."""
        self.session.add(Month(year=2024, month=12))
        self.session.add(Month(year=2025, month=1))
        self.session.add(Month(year=2025, month=2))
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_all_with_transaction_counts()

        assert len(result) == 3
        assert result[0][0].year == 2025 and result[0][0].month == 2
        assert result[1][0].year == 2025 and result[1][0].month == 1
        assert result[2][0].year == 2024 and result[2][0].month == 12

    def test_get_all_with_transaction_counts_includes_transaction_count(self) -> None:
        """get_all_with_transaction_counts includes transaction count per month."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()

        from datetime import date

        self.session.add(Transaction(month_id=month.id, date=date(2025, 1, 1), description="Test 1", amount=100.0))
        self.session.add(Transaction(month_id=month.id, date=date(2025, 1, 2), description="Test 2", amount=200.0))
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_all_with_transaction_counts()

        assert len(result) == 1
        assert result[0][1] == 2  # tx_count

    def test_get_recent_returns_chronological_order(self) -> None:
        """get_recent returns months in chronological order (oldest first)."""
        self.session.add(Month(year=2024, month=11))
        self.session.add(Month(year=2024, month=12))
        self.session.add(Month(year=2025, month=1))
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_recent(limit=3)

        assert len(result) == 3
        # Oldest first
        assert result[0].year == 2024 and result[0].month == 11
        assert result[1].year == 2024 and result[1].month == 12
        assert result[2].year == 2025 and result[2].month == 1

    def test_get_recent_respects_limit(self) -> None:
        """get_recent respects the limit parameter."""
        self.session.add(Month(year=2024, month=10))
        self.session.add(Month(year=2024, month=11))
        self.session.add(Month(year=2024, month=12))
        self.session.add(Month(year=2025, month=1))
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.get_recent(limit=2)

        assert len(result) == 2
        # Most recent 2, reversed to chronological
        assert result[0].year == 2024 and result[0].month == 12
        assert result[1].year == 2025 and result[1].month == 1

    def test_create_returns_month_with_id(self) -> None:
        """create returns month with populated ID."""
        repo = MonthRepository(self.session)
        result = repo.create(2025, 6)

        assert result.id is not None
        assert result.year == 2025
        assert result.month == 6

    def test_create_flushes_without_commit(self) -> None:
        """create uses flush so ID is available but transaction is not committed."""
        repo = MonthRepository(self.session)
        month = repo.create(2025, 7)

        # Verify month is in session but not committed
        assert month in self.session
        assert month.id is not None

    def test_update_modifies_fields(self) -> None:
        """update modifies specified fields on month."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()

        repo = MonthRepository(self.session)
        result = repo.update(month, score=3, total_income=5000.0)

        assert result.score == 3
        assert result.total_income == 5000.0

    def test_delete_removes_month(self) -> None:
        """delete removes month from database."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()
        month_id = month.id

        repo = MonthRepository(self.session)
        repo.delete(month)
        repo.commit()

        assert repo.get_by_id(month_id) is None

    def test_delete_cascades_to_transactions(self) -> None:
        """delete cascades to related transactions."""
        month = Month(year=2025, month=1)
        self.session.add(month)
        self.session.commit()

        from datetime import date

        tx = Transaction(month_id=month.id, date=date(2025, 1, 1), description="Test", amount=100.0)
        self.session.add(tx)
        self.session.commit()
        tx_id = tx.id

        repo = MonthRepository(self.session)
        repo.delete(month)
        repo.commit()

        # Transaction should be deleted due to cascade
        assert self.session.get(Transaction, tx_id) is None
