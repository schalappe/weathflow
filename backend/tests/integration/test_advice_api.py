"""Integration tests for advice API endpoints."""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.services.advice.models import AdviceResponse, ProblemArea
from app.services.exceptions import AdviceAPIError


def _create_month(db: Session, year: int, month: int, score: int = 2) -> Month:
    """Create a test month record in the database."""
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
        score=score,
        score_label="Okay",
    )
    db.add(month_record)
    db.commit()
    db.refresh(month_record)
    return month_record


def _create_mock_advice_response() -> AdviceResponse:
    """Create a mock AdviceResponse from AdviceGenerator."""
    return AdviceResponse(
        analysis="Votre gestion financière montre des progrès.",
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


MOCK_API_KEY_ENV = {"ANTHROPIC_API_KEY": "test-key-for-integration-tests"}


class TestGenerateThenRetrieveFlow:
    """Integration tests for full generate-then-retrieve workflow."""

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.routers.advice.AdviceGenerator")
    def test_full_generate_then_retrieve_flow(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Full flow: generate advice then retrieve it."""
        _create_month(db_session, 2025, 9)
        _create_month(db_session, 2025, 10)

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_mock_advice_response()
        mock_generator_class.return_value = mock_generator

        generate_response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert generate_response.status_code == 200
        generate_data = generate_response.json()
        assert generate_data["success"] is True
        assert generate_data["was_cached"] is False
        assert generate_data["advice"]["analysis"] == "Votre gestion financière montre des progrès."

        get_response = client.get("/api/advice/2025/10")

        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["exists"] is True
        assert get_data["advice"]["analysis"] == "Votre gestion financière montre des progrès."

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.routers.advice.AdviceGenerator")
    def test_advice_persisted_correctly_in_database(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Advice JSON is persisted correctly in database."""
        month = _create_month(db_session, 2025, 10)
        _create_month(db_session, 2025, 9)

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_mock_advice_response()
        mock_generator_class.return_value = mock_generator

        client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        db_session.expire_all()
        advice = db_session.query(Advice).filter(Advice.month_id == month.id).first()

        assert advice is not None
        assert advice.advice_text is not None

        stored_data = json.loads(advice.advice_text)
        assert stored_data["analysis"] == "Votre gestion financière montre des progrès."
        assert len(stored_data["problem_areas"]) == 3
        assert len(stored_data["recommendations"]) == 3
        assert stored_data["encouragement"] == "Continuez sur cette lancée!"

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.routers.advice.AdviceGenerator")
    def test_regeneration_replaces_existing_advice(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Regeneration replaces existing advice record."""
        month = _create_month(db_session, 2025, 10)
        _create_month(db_session, 2025, 9)

        old_advice = Advice(
            month_id=month.id,
            advice_text=(
                '{"analysis": "old advice", "problem_areas": [], "recommendations": [], "encouragement": "old"}'
            ),
        )
        db_session.add(old_advice)
        db_session.commit()

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_mock_advice_response()
        mock_generator_class.return_value = mock_generator

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10, "regenerate": True})

        assert response.status_code == 200
        assert response.json()["was_cached"] is False

        db_session.expire_all()
        advice_count = db_session.query(Advice).filter(Advice.month_id == month.id).count()
        assert advice_count == 1

        advice = db_session.query(Advice).filter(Advice.month_id == month.id).first()
        assert advice is not None
        stored_data = json.loads(advice.advice_text)
        assert stored_data["analysis"] == "Votre gestion financière montre des progrès."


class TestErrorHandling:
    """Integration tests for error scenarios."""

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.routers.advice.AdviceGenerator")
    def test_returns_503_when_claude_api_unavailable(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Returns 503 when Claude API is unavailable."""
        _create_month(db_session, 2025, 9)
        _create_month(db_session, 2025, 10)

        mock_generator = MagicMock()
        mock_generator.generate_advice.side_effect = AdviceAPIError(retry_count=3)
        mock_generator_class.return_value = mock_generator

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 503
        assert "AI service temporarily unavailable" in response.json()["detail"]

    def test_returns_400_when_insufficient_historical_data(self, client: TestClient, db_session: Session) -> None:
        """Returns 400 when insufficient historical data for advice generation."""
        _create_month(db_session, 2025, 10)

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 400
        assert "Not enough historical data" in response.json()["detail"]
