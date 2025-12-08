"""Tests for model relationships."""

from datetime import date

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction


def test_month_transactions_returns_list(test_db_session) -> None:
    """Month.transactions should return a list of transactions."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

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
    test_db_session.add_all([tx1, tx2])
    test_db_session.commit()

    test_db_session.refresh(month)
    assert len(month.transactions) == 2
    assert tx1 in month.transactions
    assert tx2 in month.transactions


def test_month_advice_records_returns_list(test_db_session) -> None:
    """Month.advice_records should return a list of advice records."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    advice = Advice(month_id=month.id, advice_text="Great job!")
    test_db_session.add(advice)
    test_db_session.commit()

    test_db_session.refresh(month)
    assert len(month.advice_records) == 1
    assert advice in month.advice_records


def test_transaction_month_back_reference(test_db_session) -> None:
    """Transaction.month should reference the parent Month."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    transaction = Transaction(
        month_id=month.id,
        date=date(2025, 10, 15),
        description="Test transaction",
        amount=-50.0,
    )
    test_db_session.add(transaction)
    test_db_session.commit()

    assert transaction.month is month
    assert transaction.month.year == 2025
    assert transaction.month.month == 10


def test_cascade_delete_removes_transactions(test_db_session) -> None:
    """Deleting a Month should cascade delete its transactions."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    tx = Transaction(
        month_id=month.id,
        date=date(2025, 10, 15),
        description="Test transaction",
        amount=-50.0,
    )
    advice = Advice(month_id=month.id, advice_text="Great job!")
    test_db_session.add_all([tx, advice])
    test_db_session.commit()

    tx_id = tx.id
    advice_id = advice.id

    test_db_session.delete(month)
    test_db_session.commit()

    # ##>: Verify cascade deleted the child records.
    assert test_db_session.get(Transaction, tx_id) is None
    assert test_db_session.get(Advice, advice_id) is None
