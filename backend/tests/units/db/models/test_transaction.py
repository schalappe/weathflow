"""Tests for the Transaction model."""

from datetime import date

from sqlalchemy.exc import IntegrityError

from app.db.models.month import Month
from app.db.models.transaction import Transaction
from tests.conftest import DatabaseTestCase


class TestTransactionModel(DatabaseTestCase):
    """Tests for Transaction model creation and constraints."""

    def test_create_transaction_linked_to_month(self) -> None:
        """Should create a Transaction linked to a Month."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        transaction = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test transaction",
            amount=-50.0,
        )
        self.session.add(transaction)
        self.session.commit()

        self.assertIsNotNone(transaction.id)
        self.assertEqual(transaction.month_id, month.id)

    def test_check_constraint_rejects_invalid_money_map_type(self) -> None:
        """Invalid money_map_type value should raise IntegrityError."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        transaction = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test transaction",
            amount=-50.0,
            money_map_type="INVALID_TYPE",
        )
        self.session.add(transaction)

        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_foreign_key_relationship_works(self) -> None:
        """Transaction should reference its parent Month correctly."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        transaction = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test transaction",
            amount=-50.0,
            money_map_type="CORE",
        )
        self.session.add(transaction)
        self.session.commit()

        self.assertEqual(transaction.month.id, month.id)
        self.assertEqual(transaction.month.year, 2025)

    def test_is_manually_corrected_defaults_to_false(self) -> None:
        """is_manually_corrected should default to False."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        transaction = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test transaction",
            amount=-50.0,
        )
        self.session.add(transaction)
        self.session.commit()

        self.assertFalse(transaction.is_manually_corrected)
