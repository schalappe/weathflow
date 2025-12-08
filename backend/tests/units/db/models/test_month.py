"""Tests for the Month model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models.month import Month


def test_create_month_with_required_fields(test_db_session) -> None:
    """Should create a Month record with required year and month fields."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    assert month.id is not None
    assert month.year == 2025
    assert month.month == 10


def test_unique_constraint_on_year_month(test_db_session) -> None:
    """Duplicate (year, month) combination should raise IntegrityError."""
    month1 = Month(year=2025, month=10)
    test_db_session.add(month1)
    test_db_session.commit()

    month2 = Month(year=2025, month=10)
    test_db_session.add(month2)

    with pytest.raises(IntegrityError):
        test_db_session.commit()


def test_default_values_for_totals_and_percentages(test_db_session) -> None:
    """Totals and percentages should default to 0.0."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    assert month.total_income == 0.0
    assert month.total_core == 0.0
    assert month.total_choice == 0.0
    assert month.total_compound == 0.0
    assert month.core_percentage == 0.0
    assert month.choice_percentage == 0.0
    assert month.compound_percentage == 0.0
    assert month.score == 0


def test_timestamps_are_auto_set(test_db_session) -> None:
    """created_at and updated_at should be automatically set on creation."""
    month = Month(year=2025, month=10)
    test_db_session.add(month)
    test_db_session.commit()

    assert month.created_at is not None
    assert month.updated_at is not None
