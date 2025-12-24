"""Unit tests for advice router endpoints."""

import json
import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.main import app
from app.services.advice.eligibility import EligibilityResult
from app.services.advice.models import AdviceResponse, ProblemArea, Recommendation
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
        recommendations=[
            Recommendation(
                priority=1,
                action="Reduce food spending",
                details="Limit eating out to twice per week.",
                expected_savings="50€/mois",
                difficulty="Modéré",
                quick_win=False,
            ),
            Recommendation(
                priority=2,
                action="Use public transport",
                details="Take metro instead of Uber.",
                expected_savings="30€/mois",
                difficulty="Facile",
                quick_win=True,
            ),
            Recommendation(
                priority=3,
                action="Track shopping",
                details="Use a shopping list to avoid impulse buys.",
                expected_savings="40€/mois",
                difficulty="Facile",
                quick_win=True,
            ),
        ],
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

    @patch("app.api.advice.check_eligibility")
    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    @patch("app.api.deps.AdviceGenerator")
    @patch("app.api.deps.get_settings")
    def test_regenerate_excludes_current_month_advice_from_prompt(
        self,
        mock_settings: MagicMock,
        mock_generator_class: MagicMock,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
        mock_check_eligibility: MagicMock,
    ) -> None:
        """POST regenerate=True should NOT include current month's old advice in prompt.

        When regenerating advice, the AI should not see the previous recommendations
        for the current month, as this biases the new advice generation.
        Only strictly older months should have their past advice included.
        """
        mock_settings.return_value.anthropic_api_key.get_secret_value.return_value = "test-key"
        mock_settings.return_value.anthropic_base_url = None

        # ##>: Mock eligibility check to return eligible.
        mock_check_eligibility.return_value = EligibilityResult(
            is_eligible=True,
            history_limit=3,
            is_first_advice=False,
            reason=None,
        )

        # ##>: Current month (October 2025) has existing advice.
        current_month = _create_mock_month(month_id=1, year=2025, month=10)
        current_month_advice = _create_mock_advice(month_id=1)

        # ##>: Older month (September 2025) also has advice.
        older_month = _create_mock_month(month_id=2, year=2025, month=9)
        older_month_advice = _create_mock_advice(month_id=2)

        mock_months_service.get_month_with_transactions.return_value = current_month
        mock_months_service.get_months_history_with_transactions.return_value = [current_month, older_month]

        # ##>: Both months have existing advice in the database.
        mock_advice_service.get_advice_by_month_ids.return_value = {
            1: current_month_advice,
            2: older_month_advice,
        }
        mock_advice_service.extract_recommendations_from_advice.return_value = ["Old recommendation"]

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_advice_response()
        mock_generator_class.return_value = mock_generator

        mock_stored_advice = _create_mock_advice()
        mock_advice_service.create_or_update_advice.return_value = mock_stored_advice
        mock_advice_service.month_to_month_data.return_value = MagicMock()
        mock_advice_service.advice_response_to_json.return_value = "{}"

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 10, "regenerate": True})

        self.assertEqual(response.status_code, 200)

        # ##>: Verify month_to_month_data was called twice: once for older month, once for current.
        self.assertEqual(mock_advice_service.month_to_month_data.call_count, 2)

        # ##>: Find the call for the current month (October 2025).
        current_month_call = None
        for call in mock_advice_service.month_to_month_data.call_args_list:
            month_arg = call[0][0]
            if month_arg.month == 10 and month_arg.year == 2025:
                current_month_call = call
                break

        self.assertIsNotNone(current_month_call, "Expected call for current month (October 2025)")
        assert current_month_call is not None  # Type guard for mypy.

        # ##>: Current month should have past_advice=None when regenerating.
        # The second argument is the past_advice parameter.
        past_advice_arg = current_month_call[0][1] if len(current_month_call[0]) > 1 else None
        self.assertIsNone(
            past_advice_arg, "When regenerating, current month's old advice should NOT be included in prompt"
        )

    @patch("app.api.advice.check_eligibility")
    @patch("app.api.advice.advice_service")
    @patch("app.api.advice.months_service")
    @patch("app.api.deps.AdviceGenerator")
    @patch("app.api.deps.get_settings")
    def test_excludes_future_months_from_history(
        self,
        mock_settings: MagicMock,
        mock_generator_class: MagicMock,
        mock_months_service: MagicMock,
        mock_advice_service: MagicMock,
        mock_check_eligibility: MagicMock,
    ) -> None:
        """POST should only include strictly older months in history, not future months.

        When generating advice for September, October's advice should NOT be included
        even if October has already been generated. Only August and earlier should be
        included in the history.
        """
        mock_settings.return_value.anthropic_api_key.get_secret_value.return_value = "test-key"
        mock_settings.return_value.anthropic_base_url = None

        mock_check_eligibility.return_value = EligibilityResult(
            is_eligible=True,
            history_limit=3,
            is_first_advice=False,
            reason=None,
        )

        # ##>: Target month is September 2025.
        september = _create_mock_month(month_id=1, year=2025, month=9)

        # ##>: October 2025 is a FUTURE month (should be excluded from history).
        october = _create_mock_month(month_id=2, year=2025, month=10)
        october_advice = _create_mock_advice(month_id=2)

        # ##>: August 2025 is an OLDER month (should be included in history).
        august = _create_mock_month(month_id=3, year=2025, month=8)
        august_advice = _create_mock_advice(month_id=3)

        mock_months_service.get_month_with_transactions.return_value = september
        # ##>: History returns all months including the future one (October).
        mock_months_service.get_months_history_with_transactions.return_value = [october, september, august]

        # ##>: No cached advice for September, so it will generate new advice.
        mock_advice_service.get_advice_by_month_id.return_value = None
        mock_advice_service.get_advice_by_month_ids.return_value = {
            2: october_advice,
            3: august_advice,
        }
        mock_advice_service.extract_recommendations_from_advice.return_value = ["Past recommendation"]

        mock_generator = MagicMock()
        mock_generator.generate_advice.return_value = _create_advice_response()
        mock_generator_class.return_value = mock_generator

        mock_stored_advice = _create_mock_advice()
        mock_advice_service.create_or_update_advice.return_value = mock_stored_advice
        mock_advice_service.month_to_month_data.return_value = MagicMock()
        mock_advice_service.advice_response_to_json.return_value = "{}"

        response = client.post("/api/advice/generate", json={"year": 2025, "month": 9})

        self.assertEqual(response.status_code, 200)

        # ##>: Verify month_to_month_data was called only for September (current) and August (older).
        # It should NOT be called for October (future month).
        call_months = [call[0][0].month for call in mock_advice_service.month_to_month_data.call_args_list]

        self.assertIn(9, call_months, "September (current month) should be included")
        self.assertIn(8, call_months, "August (older month) should be included in history")
        self.assertNotIn(10, call_months, "October (future month) should NOT be included in history")

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
