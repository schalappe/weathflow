"""Tests for the Transaction model."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Month, Transaction


def test_create_transaction_linked_to_month(test_db_session) -> None:
    """Should create a Transaction linked to a Month."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    transaction = Transaction(
        month_id=month.id,
        date=date(2025, 10, 15),
        description='Test transaction',
        amount=-50.0,
    )
    test_db_session.add(transaction)
    test_db_session.commit()

    assert transaction.id is not None
    assert transaction.month_id == month.id


def test_check_constraint_rejects_invalid_money_map_type(test_db_session) -> None:
    """Invalid money_map_type value should raise IntegrityError."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    transaction = Transaction(
        month_id=month.id,
        date=date(2025, 10, 15),
        description='Test transaction',
        amount=-50.0,
        money_map_type='INVALID_TYPE',
    )
    test_db_session.add(transaction)

    with pytest.raises(IntegrityError):
        test_db_session.commit()


def test_foreign_key_relationship_works(test_db_session) -> None:
    """Transaction should reference its parent Month correctly."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    transaction = Transaction(
        month_id=month.id,
        date=date(2025, 10, 15),
        description='Test transaction',
        amount=-50.0,
        money_map_type='CORE',
    )
    test_db_session.add(transaction)
    test_db_session.commit()

    assert transaction.month.id == month.id
    assert transaction.month.year == 2025


def test_is_manually_corrected_defaults_to_false(test_db_session) -> None:
    """is_manually_corrected should default to False."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    transaction = Transaction(
        month_id=month.id,
        date=date(2025, 10, 15),
        description='Test transaction',
        amount=-50.0,
    )
    test_db_session.add(transaction)
    test_db_session.commit()

    assert transaction.is_manually_corrected is False
