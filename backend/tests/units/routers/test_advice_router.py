"""Unit tests for advice router endpoints."""

import json
import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.main import app
from app.services.advice.models import AdviceResponse, ProblemArea
from app.services.exceptions import AdviceQueryError, InsufficientDataError

client = TestClient(app)


def _create_mock_month(month_id: int = 1, year: int = 2025, month: int = 10) -> Month:
    """Create a mock Month object."""
    mock_month = MagicMock(spec=Month)
    mock_month.id = month_id
    mock_month.year = year
    mock_month.month = month
    mock_month.total_income = 3000.0
    mock_month.total_core = 1500.0
    mock_month.total_choice = 900.0
    mock_month.total_compound = 600.0
    mock_month.core_percentage = 50.0
    mock_month.choice_percentage = 30.0
    mock_month.compound_percentage = 20.0
    mock_month.score = 3
    mock_month.score_label = "Great"
    return mock_month


def _create_mock_advice(month_id: int = 1) -> Advice:
    """Create a mock Advice object with valid JSON."""
    mock_advice = MagicMock(spec=Advice)
    mock_advice.id = 1
    mock_advice.month_id = month_id
    mock_advice.advice_text = json.dumps(
        {
            "analysis": "Test analysis",
            "problem_areas": [
                {"category": "Subscriptions", "amount": 85.0, "trend": "+20%"},
                {"category": "Dining", "amount": 150.0, "trend": "+15%"},
                {"category": "Entertainment", "amount": 120.0, "trend": "N/A"},
            ],
            "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
            "encouragement": "Keep going!",
        }
    )
    mock_advice.generated_at = datetime(2025, 10, 15, 12, 0, 0, tzinfo=UTC)
    return mock_advice


def _create_advice_response() -> AdviceResponse:
    """Create a mock AdviceResponse from AdviceGenerator."""
    return AdviceResponse(
        analysis="New analysis",
        problem_areas=[
            ProblemArea(category="Food", amount=200.0, trend="+10%"),
            ProblemArea(category="Transport", amount=100.0, trend="-5%"),
            ProblemArea(category="Shopping", amount=150.0, trend="N/A"),
        ],
        recommendations=["Reduce food spending", "Use public transport", "Track shopping"],
        encouragement="Great progress!",
    )


class TestPostGenerateAdvice(unittest.TestCase):
    """Tests for POST /api/advice/generate endpoint."""

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    @patch("app.api.deps.AdviceGenerator")
    @patch("app.api.deps.get_settings")
    def test_generates_new_advice_when_none_exists(
        self,
        mock_settings: MagicMock,
        mock_generator_class: MagicMock,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """POST generates new advice when no cached advice exists."""
        mock_settings.return_value.anthropic_api_key.get_secret_value.return_value = "test-key"
        mock_settings.return_value.anthropic_base_url = None

        mock_month = _create_mock_month()
        mock_months_service.get_month_with_transactions.return_value = mock_month
        mock_months_service.get_months_history_with_transactions.return_value = [mock_month]
        mock_advice_service.get_advice_by_month_id.return_value = None
        mock_advice_service.get_advice_by_month_ids.return_value = {}

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_advice_response()
        mock_generator_class.return_value = mock_generator

        mock_stored_advice = _create_mock_advice()
        mock_advice_service.create_or_update_advice.return_value = mock_stored_advice
        mock_advice_service.month_to_month_data.return_value = MagicMock()
        mock_advice_service.advice_response_to_json.return_value = "{}"
        mock_advice_service.extract_recommendations_from_advice.return_value = None

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["was_cached"])
        self.assertIn("advice", data)

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    def test_returns_cached_advice_when_exists_and_not_regenerate(
        self,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """POST returns cached advice when exists and regenerate=False."""
        mock_month = _create_mock_month()
        mock_months_service.get_month_with_transactions.return_value = mock_month
        mock_advice_service.get_advice_by_month_id.return_value = _create_mock_advice()

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["was_cached"])
        self.assertEqual(data["advice"]["analysis"], "Test analysis")

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    @patch("app.api.deps.AdviceGenerator")
    @patch("app.api.deps.get_settings")
    def test_regenerates_advice_when_regenerate_true(
        self,
        mock_settings: MagicMock,
        mock_generator_class: MagicMock,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """POST regenerates advice when regenerate=True even if cached exists."""
        mock_settings.return_value.anthropic_api_key.get_secret_value.return_value = "test-key"
        mock_settings.return_value.anthropic_base_url = None

        mock_month = _create_mock_month()
        mock_months_service.get_month_with_transactions.return_value = mock_month
        mock_months_service.get_months_history_with_transactions.return_value = [mock_month]

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_advice_response()
        mock_generator_class.return_value = mock_generator

        mock_stored_advice = _create_mock_advice()
        mock_advice_service.create_or_update_advice.return_value = mock_stored_advice
        mock_advice_service.month_to_month_data.return_value = MagicMock()
        mock_advice_service.advice_response_to_json.return_value = "{}"
        mock_advice_service.get_advice_by_month_ids.return_value = {}
        mock_advice_service.extract_recommendations_from_advice.return_value = None

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10, "regenerate": True})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["was_cached"])

    @patch("app.api.advice.months_service")
    def test_returns_404_when_month_not_found(self, mock_months_service: MagicMock) -> None:
        """POST returns 404 when month not found in database."""
        mock_months_service.get_month_with_transactions.return_value = None

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        self.assertEqual(response.status_code, 404)
        self.assertIn("No data found", response.json()["detail"])

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    @patch("app.api.deps.AdviceGenerator")
    @patch("app.api.deps.get_settings")
    def test_returns_400_when_insufficient_data(
        self,
        mock_settings: MagicMock,
        mock_generator_class: MagicMock,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """POST returns 400 when insufficient historical data."""
        mock_settings.return_value.anthropic_api_key.get_secret_value.return_value = "test-key"
        mock_settings.return_value.anthropic_base_url = None

        mock_month = _create_mock_month()
        mock_months_service.get_month_with_transactions.return_value = mock_month
        mock_months_service.get_months_history_with_transactions.return_value = [mock_month]
        mock_advice_service.get_advice_by_month_id.return_value = None
        mock_advice_service.get_advice_by_month_ids.return_value = {}
        mock_advice_service.month_to_month_data.return_value = MagicMock()
        mock_advice_service.extract_recommendations_from_advice.return_value = None

        mock_generator = MagicMock()
        mock_generator.generate_advice.side_effect = InsufficientDataError(min_months_required=2)
        mock_generator_class.return_value = mock_generator

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Not enough historical data", response.json()["detail"])

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    def test_returns_500_when_cached_advice_is_corrupted(
        self,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """POST returns 500 with helpful message when cached advice JSON is corrupted."""
        mock_month = _create_mock_month()
        mock_months_service.get_month_with_transactions.return_value = mock_month

        mock_advice = MagicMock(spec=Advice)
        mock_advice.advice_text = "invalid json {"
        mock_advice_service.get_advice_by_month_id.return_value = mock_advice

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        self.assertEqual(response.status_code, 500)
        self.assertIn("corrupted", response.json()["detail"].lower())
        self.assertIn("regenerate", response.json()["detail"].lower())

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    @patch("app.api.deps.AdviceGenerator")
    @patch("app.api.deps.get_settings")
    def test_returns_503_when_database_error_during_storage(
        self,
        mock_settings: MagicMock,
        mock_generator_class: MagicMock,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """POST returns 503 when database fails during advice storage."""
        mock_settings.return_value.anthropic_api_key.get_secret_value.return_value = "test-key"
        mock_settings.return_value.anthropic_base_url = None

        mock_month = _create_mock_month()
        mock_months_service.get_month_with_transactions.return_value = mock_month
        mock_months_service.get_months_history_with_transactions.return_value = [mock_month]
        mock_advice_service.get_advice_by_month_id.return_value = None
        mock_advice_service.get_advice_by_month_ids.return_value = {}
        mock_advice_service.month_to_month_data.return_value = MagicMock()
        mock_advice_service.advice_response_to_json.return_value = "{}"
        mock_advice_service.extract_recommendations_from_advice.return_value = None

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_advice_response()
        mock_generator_class.return_value = mock_generator

        mock_advice_service.create_or_update_advice.side_effect = AdviceQueryError(1, "Connection lost")

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        self.assertEqual(response.status_code, 503)
        self.assertIn("Database temporarily unavailable", response.json()["detail"])


class TestGetAdvice(unittest.TestCase):
    """Tests for GET /api/advice/{year}/{month} endpoint."""

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    def test_returns_existing_advice_with_exists_true(
        self,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """GET returns existing advice with exists=True."""
        mock_month = _create_mock_month()
        mock_months_service.get_month_by_year_month.return_value = mock_month
        mock_advice_service.get_advice_by_month_id.return_value = _create_mock_advice()

        response = client.get("/api/advice/2025/10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["exists"])
        self.assertEqual(data["advice"]["analysis"], "Test analysis")

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    def test_returns_exists_false_when_no_advice(
        self,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """GET returns exists=False when no advice generated yet."""
        mock_month = _create_mock_month()
        mock_months_service.get_month_by_year_month.return_value = mock_month
        mock_advice_service.get_advice_by_month_id.return_value = None

        response = client.get("/api/advice/2025/10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["exists"])
        self.assertIsNone(data["advice"])

    @patch("app.api.advice.months_service")
    def test_returns_404_when_month_not_found(self, mock_months_service: MagicMock) -> None:
        """GET returns 404 when month not found in database."""
        mock_months_service.get_month_by_year_month.return_value = None

        response = client.get("/api/advice/2025/10")

        self.assertEqual(response.status_code, 404)
        self.assertIn("No data found", response.json()["detail"])

    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    def test_returns_500_when_stored_advice_is_corrupted(
        self,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
    ) -> None:
        """GET returns 500 with helpful message when advice JSON is corrupted."""
        mock_month = _create_mock_month()
        mock_months_service.get_month_by_year_month.return_value = mock_month

        mock_advice = MagicMock(spec=Advice)
        mock_advice.advice_text = "not valid json"
        mock_advice_service.get_advice_by_month_id.return_value = mock_advice

        response = client.get("/api/advice/2025/10")

        self.assertEqual(response.status_code, 500)
        self.assertIn("corrupted", response.json()["detail"].lower())
