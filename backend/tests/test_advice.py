"""Tests for the Advice model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Advice, Month


def test_create_advice_linked_to_month(test_db_session) -> None:
    """Should create an Advice record linked to a Month."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    advice = Advice(
        month_id=month.id,
        advice_text='Consider reducing dining out expenses to improve your score.',
    )
    test_db_session.add(advice)
    test_db_session.commit()

    assert advice.id is not None
    assert advice.month_id == month.id


def test_advice_text_is_required(test_db_session) -> None:
    """advice_text should not be nullable."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    advice = Advice(month_id=month.id, advice_text=None)  # type: ignore[arg-type]
    test_db_session.add(advice)

    with pytest.raises(IntegrityError):
        test_db_session.commit()


def test_generated_at_auto_sets_on_creation(test_db_session) -> None:
    """generated_at should be automatically set on creation."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    advice = Advice(
        month_id=month.id,
        advice_text='Your spending habits are excellent!',
    )
    test_db_session.add(advice)
    test_db_session.commit()

    assert advice.generated_at is not None
