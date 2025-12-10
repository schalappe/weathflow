"""Tests for transaction service functions."""

from datetime import date

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.exceptions import InvalidSubcategoryError, TransactionNotFoundError
from tests.conftest import DatabaseTestCase


class TestUpdateTransactionCategory(DatabaseTestCase):
    """Tests for update_transaction_category service function."""

    def _create_month_with_transactions(self) -> tuple[Month, Transaction]:
        """Create a month with a test transaction for testing."""
        month = Month(
            year=2025,
            month=1,
            total_income=1000.0,
            total_core=500.0,
            total_choice=300.0,
            total_compound=200.0,
            core_percentage=50.0,
            choice_percentage=30.0,
            compound_percentage=20.0,
            score=3,
            score_label="Great",
        )
        self.session.add(month)
        self.session.flush()

        transaction = Transaction(
            month_id=month.id,
            date=date(2025, 1, 15),
            description="Test Transaction",
            amount=-50.0,
            money_map_type=MoneyMapType.CHOICE.value,
            money_map_subcategory="Dining out",
            is_manually_corrected=False,
        )
        self.session.add(transaction)
        self.session.commit()

        return month, transaction

    def test_update_sets_is_manually_corrected_true(self) -> None:
        """Update sets is_manually_corrected to True."""
        from app.services.transactions import update_transaction_category

        _, transaction = self._create_month_with_transactions()
        assert transaction.is_manually_corrected is False

        updated_tx, _ = update_transaction_category(
            db=self.session,
            transaction_id=transaction.id,
            money_map_type=MoneyMapType.CORE,
            money_map_subcategory="Groceries",
        )

        assert updated_tx.is_manually_corrected is True

    def test_update_changes_money_map_type_and_subcategory(self) -> None:
        """Update changes money_map_type and money_map_subcategory fields."""
        from app.services.transactions import update_transaction_category

        _, transaction = self._create_month_with_transactions()
        assert transaction.money_map_type == MoneyMapType.CHOICE.value
        assert transaction.money_map_subcategory == "Dining out"

        updated_tx, _ = update_transaction_category(
            db=self.session,
            transaction_id=transaction.id,
            money_map_type=MoneyMapType.CORE,
            money_map_subcategory="Groceries",
        )

        assert updated_tx.money_map_type == MoneyMapType.CORE.value
        assert updated_tx.money_map_subcategory == "Groceries"

    def test_update_triggers_month_stats_recalculation(self) -> None:
        """Update triggers recalculation of month statistics."""
        from app.services.transactions import update_transaction_category

        month, transaction = self._create_month_with_transactions()
        original_choice_pct = month.choice_percentage
        original_core_pct = month.core_percentage

        _, updated_month = update_transaction_category(
            db=self.session,
            transaction_id=transaction.id,
            money_map_type=MoneyMapType.CORE,
            money_map_subcategory="Groceries",
        )

        # ##>: Moving a CHOICE expense to CORE should change both percentages.
        assert updated_month.choice_percentage != original_choice_pct
        assert updated_month.core_percentage != original_core_pct

    def test_update_raises_transaction_not_found_error_for_invalid_id(self) -> None:
        """Update raises TransactionNotFoundError for non-existent transaction."""
        from app.services.transactions import update_transaction_category

        self._create_month_with_transactions()

        with self.assertRaises(TransactionNotFoundError) as context:
            update_transaction_category(
                db=self.session,
                transaction_id=99999,
                money_map_type=MoneyMapType.CORE,
                money_map_subcategory="Groceries",
            )

        assert context.exception.transaction_id == 99999


class TestSubcategoryValidation(DatabaseTestCase):
    """Tests for subcategory validation in transaction service."""

    def _create_month_with_transaction(self) -> Transaction:
        """Create a month with a transaction for testing."""
        month = Month(
            year=2025,
            month=1,
            total_income=1000.0,
            total_core=500.0,
            total_choice=300.0,
            total_compound=200.0,
            core_percentage=50.0,
            choice_percentage=30.0,
            compound_percentage=20.0,
            score=3,
            score_label="Great",
        )
        self.session.add(month)
        self.session.flush()

        transaction = Transaction(
            month_id=month.id,
            date=date(2025, 1, 15),
            description="Test Transaction",
            amount=-50.0,
            money_map_type=MoneyMapType.CHOICE.value,
            money_map_subcategory="Dining out",
            is_manually_corrected=False,
        )
        self.session.add(transaction)
        self.session.commit()

        return transaction

    def test_invalid_subcategory_raises_error(self) -> None:
        """Invalid subcategory for MoneyMapType raises InvalidSubcategoryError."""
        from app.services.transactions import update_transaction_category

        transaction = self._create_month_with_transaction()

        with self.assertRaises(InvalidSubcategoryError) as context:
            update_transaction_category(
                db=self.session,
                transaction_id=transaction.id,
                money_map_type=MoneyMapType.CORE,
                money_map_subcategory="Invalid Category",
            )

        assert context.exception.money_map_type == MoneyMapType.CORE.value
        assert context.exception.subcategory == "Invalid Category"

    def test_excluded_type_auto_clears_subcategory(self) -> None:
        """EXCLUDED type automatically clears subcategory to null."""
        from app.services.transactions import update_transaction_category

        transaction = self._create_month_with_transaction()

        updated_tx, _ = update_transaction_category(
            db=self.session,
            transaction_id=transaction.id,
            money_map_type=MoneyMapType.EXCLUDED,
            money_map_subcategory="Should be cleared",
        )

        assert updated_tx.money_map_type == MoneyMapType.EXCLUDED.value
        assert updated_tx.money_map_subcategory is None
