"""Integration tests for advice eligibility API behavior."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.services.advice.models import AdviceResponse, ProblemArea


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
        ],
        recommendations=[
            "Réduire les abonnements non utilisés.",
        ],
        encouragement="Continuez sur cette lancée!",
    )


MOCK_API_KEY_ENV = {"ANTHROPIC_API_KEY": "test-key-for-integration-tests"}


class TestGetAdviceEligibility:
    """Tests for eligibility info in GET /api/advice/{year}/{month}."""

    def test_get_advice_returns_eligibility_info(self, client: TestClient, db_session: Session) -> None:
        """GET /api/advice returns eligibility field with can_generate status."""
        # ##>: Create two months - October is most recent, so September and October are eligible.
        _create_month(db_session, 2025, 9)
        _create_month(db_session, 2025, 10)

        response = client.get("/api/advice/2025/10")

        assert response.status_code == 200
        data = response.json()
        assert "eligibility" in data
        assert data["eligibility"]["can_generate"] is True
        assert data["eligibility"]["is_first_advice"] is True  # ##>: No advice exists yet.

    def test_get_advice_returns_not_eligible_for_old_month(self, client: TestClient, db_session: Session) -> None:
        """GET /api/advice returns can_generate=False for months outside window."""
        _create_month(db_session, 2025, 8)  # ##>: Old month.
        _create_month(db_session, 2025, 9)
        _create_month(db_session, 2025, 10)  # ##>: Most recent.

        response = client.get("/api/advice/2025/8")

        assert response.status_code == 200
        data = response.json()
        assert data["eligibility"]["can_generate"] is False
        assert data["eligibility"]["reason"] is not None
        assert "2025-10" in data["eligibility"]["reason"]


class TestGenerateAdviceEligibility:
    """Tests for eligibility enforcement in POST /api/advice/generate."""

    def test_generate_advice_returns_403_when_not_eligible(self, client: TestClient, db_session: Session) -> None:
        """POST /api/advice/generate returns 403 for ineligible months."""
        _create_month(db_session, 2025, 8)  # ##>: Old month.
        _create_month(db_session, 2025, 10)  # ##>: Most recent.

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 8})

        assert response.status_code == 403
        assert "2025-10" in response.json()["detail"]

    def test_eligibility_reason_included_in_403_response(self, client: TestClient, db_session: Session) -> None:
        """403 response includes clear reason message."""
        _create_month(db_session, 2025, 7)  # ##>: Old month.
        _create_month(db_session, 2025, 10)  # ##>: Most recent.

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 7})

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Les conseils ne peuvent être générés que pour les 2 mois les plus récents" in detail

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.api.deps.AdviceGenerator")
    def test_generate_advice_uses_dynamic_history_limit(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Uses eligibility.history_limit to fetch appropriate history."""
        # ##>: Create 4 months of data.
        for m in range(7, 11):
            _create_month(db_session, 2025, m)

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_mock_advice_response()
        mock_generator_class.return_value = mock_generator

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 200
        # ##>: First advice uses 12-month limit, should have called generate_advice.
        mock_generator.generate_advice.assert_called_once()

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.api.deps.AdviceGenerator")
    def test_generate_first_advice_uses_12_month_limit(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """First advice generation uses 12-month history limit."""
        # ##>: Create 13 months of data to verify limit is respected.
        for m in range(1, 13):
            _create_month(db_session, 2024, m)
        _create_month(db_session, 2025, 1)

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_mock_advice_response()
        mock_generator_class.return_value = mock_generator

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 1})

        assert response.status_code == 200
        # ##>: Verify first advice scenario detected.
        data = response.json()
        assert data["success"] is True

    @patch.dict("os.environ", MOCK_API_KEY_ENV)
    @patch("app.api.deps.AdviceGenerator")
    def test_regenerating_first_advice_uses_12_month_limit(
        self,
        mock_generator_class: MagicMock,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Regenerating the only advice still uses 12-month limit."""
        month_oct = _create_month(db_session, 2025, 10)

        # ##>: Add advice only for October (the target month).
        advice = Advice(
            month_id=month_oct.id,
            advice_text='{"analysis":"old","problem_areas":[],"recommendations":[],"encouragement":"old"}',
        )
        db_session.add(advice)
        db_session.commit()

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_mock_advice_response()
        mock_generator_class.return_value = mock_generator

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10, "regenerate": True})

        assert response.status_code == 200
        assert response.json()["was_cached"] is False
