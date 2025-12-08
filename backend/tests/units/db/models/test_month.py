"""Tests for the Month model."""

from sqlalchemy.exc import IntegrityError

from app.db.models.month import Month
from tests.conftest import DatabaseTestCase


class TestMonthModel(DatabaseTestCase):
    """Tests for Month model creation and constraints."""

    def test_create_month_with_required_fields(self) -> None:
        """Should create a Month record with required year and month fields."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        self.assertIsNotNone(month.id)
        self.assertEqual(month.year, 2025)
        self.assertEqual(month.month, 10)

    def test_unique_constraint_on_year_month(self) -> None:
        """Duplicate (year, month) combination should raise IntegrityError."""
        month1 = Month(year=2025, month=10)
        self.session.add(month1)
        self.session.commit()

        month2 = Month(year=2025, month=10)
        self.session.add(month2)

        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_default_values_for_totals_and_percentages(self) -> None:
        """Totals and percentages should default to 0.0."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        self.assertEqual(month.total_income, 0.0)
        self.assertEqual(month.total_core, 0.0)
        self.assertEqual(month.total_choice, 0.0)
        self.assertEqual(month.total_compound, 0.0)
        self.assertEqual(month.core_percentage, 0.0)
        self.assertEqual(month.choice_percentage, 0.0)
        self.assertEqual(month.compound_percentage, 0.0)
        self.assertEqual(month.score, 0)

    def test_timestamps_are_auto_set(self) -> None:
        """created_at and updated_at should be automatically set on creation."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        self.assertIsNotNone(month.created_at)
        self.assertIsNotNone(month.updated_at)
