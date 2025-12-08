"""Tests for model relationships."""

from datetime import date

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from tests.conftest import DatabaseTestCase


class TestModelRelationships(DatabaseTestCase):
    """Tests for foreign key relationships and cascade behavior."""

    def test_month_transactions_returns_list(self) -> None:
        """Month.transactions should return a list of transactions."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        tx1 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Transaction 1",
            amount=-50.0,
        )
        tx2 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 16),
            description="Transaction 2",
            amount=-30.0,
        )
        self.session.add_all([tx1, tx2])
        self.session.commit()

        self.session.refresh(month)
        self.assertEqual(len(month.transactions), 2)
        self.assertIn(tx1, month.transactions)
        self.assertIn(tx2, month.transactions)

    def test_month_advice_records_returns_list(self) -> None:
        """Month.advice_records should return a list of advice records."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        advice = Advice(month_id=month.id, advice_text="Great job!")
        self.session.add(advice)
        self.session.commit()

        self.session.refresh(month)
        self.assertEqual(len(month.advice_records), 1)
        self.assertIn(advice, month.advice_records)

    def test_transaction_month_back_reference(self) -> None:
        """Transaction.month should reference the parent Month."""
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

        self.assertIs(transaction.month, month)
        self.assertEqual(transaction.month.year, 2025)
        self.assertEqual(transaction.month.month, 10)

    def test_cascade_delete_removes_transactions(self) -> None:
        """Deleting a Month should cascade delete its transactions."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test transaction",
            amount=-50.0,
        )
        advice = Advice(month_id=month.id, advice_text="Great job!")
        self.session.add_all([tx, advice])
        self.session.commit()

        tx_id = tx.id
        advice_id = advice.id

        self.session.delete(month)
        self.session.commit()

        # ##>: Verify cascade deleted the child records.
        self.assertIsNone(self.session.get(Transaction, tx_id))
        self.assertIsNone(self.session.get(Advice, advice_id))
