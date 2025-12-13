"""Unit tests for advice service functions."""

from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice import AdviceRepository
from app.services.advice import service as advice_service
from app.services.advice.models import AdviceResponse, ProblemArea
from tests.conftest import DatabaseTestCase


def _create_month(session: Session, year: int = 2025, month: int = 1) -> Month:
    """Create a test month record."""
    month_record = Month(
        year=year,
        month=month,
        total_income=3000.0,
        total_core=1500.0,
        total_choice=900.0,
        total_compound=600.0,
        core_percentage=50.0,
        choice_percentage=30.0,
        compound_percentage=20.0,
        score=3,
        score_label="Great",
    )
    session.add(month_record)
    session.commit()
    session.refresh(month_record)
    return month_record


def _create_advice_response() -> AdviceResponse:
    """Create a test AdviceResponse."""
    return AdviceResponse(
        analysis="Votre gestion financière est excellente ce mois-ci.",
        problem_areas=[
            ProblemArea(category="Subscriptions", amount=85.0, trend="+20%"),
            ProblemArea(category="Dining", amount=150.0, trend="+15%"),
            ProblemArea(category="Entertainment", amount=120.0, trend="N/A"),
        ],
        recommendations=[
            "Réduire les abonnements non utilisés.",
            "Limiter les repas au restaurant.",
            "Maintenir votre taux d'épargne actuel.",
        ],
        encouragement="Continuez sur cette lancée!",
    )


class TestGetAdviceByMonthId(DatabaseTestCase):
    """Tests for get_advice_by_month_id function."""

    def test_returns_advice_when_exists(self) -> None:
        """Get advice returns advice record when it exists for the month."""
        month = _create_month(self.session)
        advice = Advice(month_id=month.id, advice_text='{"analysis": "test"}')
        self.session.add(advice)
        self.session.commit()

        advice_repo = AdviceRepository(self.session)
        result = advice_service.get_advice_by_month_id(advice_repo, month.id)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.month_id, month.id)
        self.assertEqual(result.advice_text, '{"analysis": "test"}')

    def test_returns_none_when_not_exists(self) -> None:
        """Get advice returns None when no advice exists for the month."""
        month = _create_month(self.session)

        advice_repo = AdviceRepository(self.session)
        result = advice_service.get_advice_by_month_id(advice_repo, month.id)

        self.assertIsNone(result)


class TestCreateOrUpdateAdvice(DatabaseTestCase):
    """Tests for create_or_update_advice function."""

    def test_creates_new_advice_record(self) -> None:
        """Create or update creates new advice when none exists."""
        month = _create_month(self.session)
        advice_text = '{"analysis": "new advice"}'

        advice_repo = AdviceRepository(self.session)
        result = advice_service.create_or_update_advice(advice_repo, month.id, advice_text)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.month_id, month.id)
        self.assertEqual(result.advice_text, advice_text)
        self.assertIsNotNone(result.generated_at)

    def test_updates_existing_advice_record(self) -> None:
        """Create or update updates existing advice when it exists."""
        month = _create_month(self.session)
        original_advice = Advice(month_id=month.id, advice_text='{"analysis": "old"}')
        self.session.add(original_advice)
        self.session.commit()
        original_id = original_advice.id
        original_time = original_advice.generated_at

        advice_repo = AdviceRepository(self.session)
        new_text = '{"analysis": "updated"}'
        result = advice_service.create_or_update_advice(advice_repo, month.id, new_text)

        self.assertEqual(result.id, original_id)
        self.assertEqual(result.advice_text, new_text)
        self.assertGreaterEqual(result.generated_at, original_time)

        count = self.session.query(Advice).filter(Advice.month_id == month.id).count()
        self.assertEqual(count, 1)


class TestMonthToMonthData(DatabaseTestCase):
    """Tests for month_to_month_data conversion function."""

    def test_converts_month_to_month_data(self) -> None:
        """Month to MonthData converts all fields correctly."""
        month = _create_month(self.session, year=2025, month=10)

        result = advice_service.month_to_month_data(month)

        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.total_income, 3000.0)
        self.assertEqual(result.total_core, 1500.0)
        self.assertEqual(result.total_choice, 900.0)
        self.assertEqual(result.total_compound, 600.0)
        self.assertEqual(result.core_percentage, 50.0)
        self.assertEqual(result.choice_percentage, 30.0)
        self.assertEqual(result.compound_percentage, 20.0)
        self.assertEqual(result.score, 3)
        self.assertEqual(result.score_label, "Great")
        self.assertIsNone(result.category_breakdown)


class TestAdviceResponseToJson(DatabaseTestCase):
    """Tests for advice_response_to_json serialization function."""

    def test_serializes_advice_response_to_json(self) -> None:
        """Advice response to JSON serializes all fields."""
        advice = _create_advice_response()

        result = advice_service.advice_response_to_json(advice)

        self.assertIn("analysis", result)
        self.assertIn("problem_areas", result)
        self.assertIn("recommendations", result)
        self.assertIn("encouragement", result)
        self.assertIn("Subscriptions", result)
        self.assertIn("+20%", result)
