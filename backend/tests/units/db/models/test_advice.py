"""Tests for the Advice model."""

from sqlalchemy.exc import IntegrityError

from app.db.models.advice import Advice
from app.db.models.month import Month
from tests.conftest import DatabaseTestCase


class TestAdviceModel(DatabaseTestCase):
    """Tests for Advice model creation and constraints."""

    def test_create_advice_linked_to_month(self) -> None:
        """Should create an Advice record linked to a Month."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        advice = Advice(
            month_id=month.id,
            advice_text="Consider reducing dining out expenses to improve your score.",
        )
        self.session.add(advice)
        self.session.commit()

        self.assertIsNotNone(advice.id)
        self.assertEqual(advice.month_id, month.id)

    def test_advice_text_is_required(self) -> None:
        """advice_text should not be nullable."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        advice = Advice(month_id=month.id, advice_text=None)
        self.session.add(advice)

        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_generated_at_auto_sets_on_creation(self) -> None:
        """generated_at should be automatically set on creation."""
        month = Month(year=2025, month=10)
        self.session.add(month)
        self.session.commit()

        advice = Advice(
            month_id=month.id,
            advice_text="Your spending habits are excellent!",
        )
        self.session.add(advice)
        self.session.commit()

        self.assertIsNotNone(advice.generated_at)
