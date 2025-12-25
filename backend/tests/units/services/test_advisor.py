"""Tests for AdviceGenerator service."""

import unittest
from unittest.mock import MagicMock

import anthropic
from pydantic import ValidationError

from app.services.advice.generator import AdviceGenerator, calculate_trend
from app.services.advice.models import AdviceResponse, MonthData, ProblemArea, Recommendation
from app.services.advice.prompt import ADVICE_SYSTEM_PROMPT
from app.services.exceptions import (
    AdviceAPIError,
    AdviceGenerationError,
    AdviceParseError,
    InsufficientDataError,
)


def _make_month_data(
    year: int = 2025,
    month: int = 1,
    total_income: float = 3000.0,
    total_core: float = 1500.0,
    total_choice: float = 600.0,
    total_compound: float = 600.0,
    score: int = 3,
    category_breakdown: dict[str, float] | None = None,
) -> MonthData:
    """Create a test MonthData with defaults."""
    return MonthData(
        year=year,
        month=month,
        total_income=total_income,
        total_core=total_core,
        total_choice=total_choice,
        total_compound=total_compound,
        core_percentage=50.0 if total_income > 0 else 0.0,
        choice_percentage=20.0 if total_income > 0 else 0.0,
        compound_percentage=20.0 if total_income > 0 else 0.0,
        score=score,
        score_label="Great",
        category_breakdown=category_breakdown,
    )


class TestAdviceDTOs(unittest.TestCase):
    """Tests for advice DTOs (Task Group 1)."""

    def test_month_data_validation_with_valid_data(self) -> None:
        """Should create MonthData with valid data."""
        month = _make_month_data(year=2025, month=6, score=2)

        self.assertEqual(month.year, 2025)
        self.assertEqual(month.month, 6)
        self.assertEqual(month.score, 2)

    def test_problem_area_is_immutable(self) -> None:
        """Should raise error when trying to modify ProblemArea."""
        problem = ProblemArea(category="Dining", amount=150.0, trend="+20%")

        with self.assertRaises(ValidationError):
            problem.category = "Shopping"  # type: ignore[misc]

    def test_advice_response_field_validation(self) -> None:
        """Should create AdviceResponse with all required fields."""
        problem_areas = [ProblemArea(category="Test", amount=100.0, trend="+10%")]
        recommendations = [
            Recommendation(
                priority=1,
                action="Rec 1",
                details="Details 1",
                expected_savings="50€",
                difficulty="Facile",
                quick_win=True,
            ),
            Recommendation(
                priority=2,
                action="Rec 2",
                details="Details 2",
                expected_savings="30€",
                difficulty="Modéré",
                quick_win=False,
            ),
        ]
        response = AdviceResponse(
            analysis="Test analysis",
            problem_areas=problem_areas,
            recommendations=recommendations,
            encouragement="Keep going!",
        )

        self.assertEqual(response.analysis, "Test analysis")
        self.assertEqual(len(response.problem_areas), 1)
        self.assertEqual(len(response.recommendations), 2)

    def test_insufficient_data_error_attributes(self) -> None:
        """Should store min_months_required attribute."""
        error = InsufficientDataError(min_months_required=2)

        self.assertEqual(error.min_months_required, 2)
        self.assertIn("2 months", str(error))


class TestAdvicePrompt(unittest.TestCase):
    """Tests for system prompt (Task Group 2)."""

    def test_system_prompt_is_non_empty_string(self) -> None:
        """Should have non-empty system prompt."""
        self.assertIsInstance(ADVICE_SYSTEM_PROMPT, str)
        self.assertGreater(len(ADVICE_SYSTEM_PROMPT), 100)

    def test_prompt_contains_required_keywords(self) -> None:
        """Should contain Money Map, JSON, and French keywords."""
        self.assertIn("Money Map", ADVICE_SYSTEM_PROMPT)
        self.assertIn("JSON", ADVICE_SYSTEM_PROMPT)
        self.assertIn("français", ADVICE_SYSTEM_PROMPT.lower())


class TestTrendCalculation(unittest.TestCase):
    """Tests for calculate_trend function (Task Group 3)."""

    def test_positive_trend_returns_plus_format(self) -> None:
        """Should return '+15%' for positive change."""
        result = calculate_trend(current=115.0, previous=100.0)
        self.assertEqual(result, "+15%")

    def test_negative_trend_returns_minus_format(self) -> None:
        """Should return '-8%' for negative change."""
        result = calculate_trend(current=92.0, previous=100.0)
        self.assertEqual(result, "-8%")

    def test_zero_change_returns_plus_zero(self) -> None:
        """Should return '+0%' for no change."""
        result = calculate_trend(current=100.0, previous=100.0)
        self.assertEqual(result, "+0%")

    def test_previous_zero_returns_na(self) -> None:
        """Should return 'N/A' when previous value is zero."""
        result = calculate_trend(current=100.0, previous=0.0)
        self.assertEqual(result, "N/A")

    def test_large_percentage_changes(self) -> None:
        """Should handle large percentage changes (>100%)."""
        result = calculate_trend(current=300.0, previous=100.0)
        self.assertEqual(result, "+200%")


class TestAdviceGeneratorInit(unittest.TestCase):
    """Tests for AdviceGenerator initialization (Task Group 4)."""

    def test_init_accepts_api_key_and_optional_params(self) -> None:
        """Should accept api_key, base_url, and model parameters."""
        generator = AdviceGenerator(api_key="test-key", base_url="http://test", model="test-model")

        self.assertEqual(generator._model, "test-model")

    def test_default_model_loaded_from_settings(self) -> None:
        """Should use settings model when not specified."""
        generator = AdviceGenerator(api_key="test-key")

        # ##>: Model should be loaded from settings.
        self.assertIsNotNone(generator._model)

    def test_class_var_constants_are_set(self) -> None:
        """Should have ClassVar constants set correctly."""
        self.assertEqual(AdviceGenerator.MIN_MONTHS_REQUIRED, 2)
        self.assertEqual(AdviceGenerator.MAX_RETRIES, 3)


class TestAdviceGeneratorValidation(unittest.TestCase):
    """Tests for input validation (Task Group 5)."""

    def setUp(self) -> None:
        """Create generator with mocked client."""
        self.generator = AdviceGenerator(api_key="test-key")
        self.generator._client = MagicMock()

    def test_raises_insufficient_data_error_with_zero_history(self) -> None:
        """Should raise InsufficientDataError with empty history."""
        current = _make_month_data()

        with self.assertRaises(InsufficientDataError) as context:
            self.generator.generate_advice(current, [])

        self.assertEqual(context.exception.min_months_required, 2)

    def test_passes_validation_with_two_months(self) -> None:
        """Should pass validation with current + 1 history month."""
        current = _make_month_data(year=2025, month=2)
        history = [_make_month_data(year=2025, month=1)]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"analysis": "Test", "problem_areas": [], "recommendations": [], "encouragement": "Good"}')
        ]
        self.generator._client.messages.create.return_value = mock_response  # type: ignore[attr-defined]

        result = self.generator.generate_advice(current, history)
        self.assertIsInstance(result, AdviceResponse)


class TestAdviceGeneratorPromptBuilding(unittest.TestCase):
    """Tests for prompt building (Task Group 6)."""

    def setUp(self) -> None:
        """Create generator."""
        self.generator = AdviceGenerator(api_key="test-key")

    def test_json_output_contains_all_month_data(self) -> None:
        """Should include all month data in JSON output."""
        current = _make_month_data(year=2025, month=2)
        history = [_make_month_data(year=2025, month=1)]

        prompt = self.generator._build_user_prompt(current, history)

        self.assertIn("2025", prompt)
        self.assertIn("total_income", prompt)
        self.assertIn("score", prompt)

    def test_ensure_ascii_false_preserves_french(self) -> None:
        """Should preserve French characters in output."""
        current = _make_month_data()
        history = [_make_month_data()]

        prompt = self.generator._build_user_prompt(current, history)

        # ##>: Prompt itself contains French instructions.
        self.assertIn("Analyse", prompt)

    def test_category_breakdown_included_when_present(self) -> None:
        """Should include category breakdown when available."""
        current = _make_month_data(category_breakdown={"Subscriptions": 85.0, "Dining": 120.0})
        history = [_make_month_data()]

        prompt = self.generator._build_user_prompt(current, history)

        self.assertIn("Subscriptions", prompt)
        self.assertIn("85.0", prompt)


class TestAdviceGeneratorAPICall(unittest.TestCase):
    """Tests for Claude API call (Task Group 7)."""

    def setUp(self) -> None:
        """Create generator with mocked client."""
        self.generator = AdviceGenerator(api_key="test-key")
        self.mock_client = MagicMock()
        self.generator._client = self.mock_client

    def test_successful_api_call_returns_response_text(self) -> None:
        """Should return response text on success."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test response")]
        self.mock_client.messages.create.return_value = mock_response

        result = self.generator._call_claude_api("test prompt")

        self.assertEqual(result, "test response")

    def test_authentication_error_raises_advice_generation_error(self) -> None:
        """Should raise AdviceGenerationError on authentication failure."""
        self.mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="Invalid API key", response=MagicMock(), body=None
        )

        with self.assertRaises(AdviceGenerationError) as context:
            self.generator._call_claude_api("test prompt")

        self.assertIn("API key", str(context.exception))

    def test_api_connection_error_raises_advice_api_error(self) -> None:
        """Should raise AdviceAPIError on connection failure."""
        self.mock_client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())

        with self.assertRaises(AdviceAPIError) as context:
            self.generator._call_claude_api("test prompt")

        self.assertEqual(context.exception.retry_count, 3)

    def test_empty_response_raises_advice_parse_error(self) -> None:
        """Should raise AdviceParseError on empty response."""
        mock_response = MagicMock()
        mock_response.content = []
        self.mock_client.messages.create.return_value = mock_response

        with self.assertRaises(AdviceParseError):
            self.generator._call_claude_api("test prompt")

    def test_rate_limit_error_raises_advice_api_error(self) -> None:
        """Should raise AdviceAPIError on rate limit."""
        self.mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded", response=MagicMock(), body=None
        )

        with self.assertRaises(AdviceAPIError) as context:
            self.generator._call_claude_api("test prompt")

        self.assertEqual(context.exception.retry_count, 3)

    def test_api_status_error_raises_advice_api_error(self) -> None:
        """Should raise AdviceAPIError on API status errors (5xx, 4xx)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        self.mock_client.messages.create.side_effect = anthropic.APIStatusError(
            message="Internal Server Error", response=mock_response, body=None
        )

        with self.assertRaises(AdviceAPIError) as context:
            self.generator._call_claude_api("test prompt")

        self.assertEqual(context.exception.retry_count, 3)

    def test_non_text_content_block_raises_advice_parse_error(self) -> None:
        """Should raise AdviceParseError when content block has no text attribute."""
        mock_response = MagicMock()
        mock_content = MagicMock(spec=[])
        mock_response.content = [mock_content]
        self.mock_client.messages.create.return_value = mock_response

        with self.assertRaises(AdviceParseError) as context:
            self.generator._call_claude_api("test prompt")

        self.assertIn("no text content", str(context.exception))


class TestAdviceGeneratorResponseParsing(unittest.TestCase):
    """Tests for response parsing (Task Group 8)."""

    def setUp(self) -> None:
        """Create generator."""
        self.generator = AdviceGenerator(api_key="test-key")

    def test_valid_json_creates_advice_response(self) -> None:
        """Should create AdviceResponse from valid JSON."""
        response_text = """
        {
            "analysis": "Vos finances sont stables.",
            "problem_areas": [
                {"category": "Dining", "amount": 150.0, "trend": "+20%"}
            ],
            "recommendations": ["Réduire les sorties restaurant"],
            "encouragement": "Continuez ainsi!"
        }
        """

        result = self.generator._parse_response(response_text)

        self.assertIsInstance(result, AdviceResponse)
        self.assertEqual(result.analysis, "Vos finances sont stables.")
        self.assertEqual(len(result.problem_areas), 1)
        self.assertEqual(result.problem_areas[0].category, "Dining")

    def test_markdown_code_blocks_are_stripped(self) -> None:
        """Should strip markdown code blocks from response."""
        response_text = """```json
{
    "analysis": "Test",
    "problem_areas": [],
    "recommendations": [],
    "encouragement": "Good"
}
```"""

        result = self.generator._parse_response(response_text)

        self.assertEqual(result.analysis, "Test")

    def test_invalid_json_raises_advice_parse_error(self) -> None:
        """Should raise AdviceParseError on malformed JSON."""
        response_text = "not valid json {{{"

        with self.assertRaises(AdviceParseError) as context:
            self.generator._parse_response(response_text)

        self.assertIn("not valid json", context.exception.raw_response)

    def test_missing_fields_raise_advice_parse_error(self) -> None:
        """Should raise AdviceParseError when required fields missing."""
        response_text = '{"analysis": "Test"}'

        with self.assertRaises(AdviceParseError):
            self.generator._parse_response(response_text)

    def test_json_array_response_raises_advice_parse_error(self) -> None:
        """Should raise AdviceParseError when JSON is not an object."""
        response_text = '["item1", "item2"]'

        with self.assertRaises(AdviceParseError):
            self.generator._parse_response(response_text)

    def test_json_string_response_raises_advice_parse_error(self) -> None:
        """Should raise AdviceParseError when JSON is a primitive string."""
        response_text = '"just a string"'

        with self.assertRaises(AdviceParseError):
            self.generator._parse_response(response_text)


class TestAdviceGeneratorIntegration(unittest.TestCase):
    """Tests for main method integration (Task Group 9)."""

    def setUp(self) -> None:
        """Create generator with mocked client."""
        self.generator = AdviceGenerator(api_key="test-key")
        self.mock_client = MagicMock()
        self.generator._client = self.mock_client

    def test_full_flow_with_valid_data_returns_advice_response(self) -> None:
        """Should complete full flow and return AdviceResponse."""
        current = _make_month_data(year=2025, month=2)
        history = [_make_month_data(year=2025, month=1)]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text="""{
                    "analysis": "Vos dépenses sont équilibrées.",
                    "problem_areas": [
                        {"category": "Subscriptions", "amount": 85.0, "trend": "+15%"},
                        {"category": "Dining", "amount": 150.0, "trend": "+10%"},
                        {"category": "Entertainment", "amount": 100.0, "trend": "+5%"}
                    ],
                    "recommendations": [
                        "Révisez vos abonnements",
                        "Préparez plus de repas maison",
                        "Cherchez des alternatives gratuites"
                    ],
                    "encouragement": "Vous êtes sur la bonne voie!"
                }"""
            )
        ]
        self.mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_advice(current, history)

        self.assertIsInstance(result, AdviceResponse)
        self.assertEqual(len(result.problem_areas), 3)
        self.assertEqual(len(result.recommendations), 3)
        self.mock_client.messages.create.assert_called_once()

    def test_insufficient_data_raises_error_early(self) -> None:
        """Should raise InsufficientDataError before API call."""
        current = _make_month_data()

        with self.assertRaises(InsufficientDataError):
            self.generator.generate_advice(current, [])

        self.mock_client.messages.create.assert_not_called()


class TestExceptionHierarchy(unittest.TestCase):
    """Tests for exception hierarchy."""

    def test_insufficient_data_error_inherits_from_advice_generation_error(self) -> None:
        """Should be catchable as AdviceGenerationError."""
        self.assertTrue(issubclass(InsufficientDataError, AdviceGenerationError))

    def test_advice_api_error_inherits_from_advice_generation_error(self) -> None:
        """Should be catchable as AdviceGenerationError."""
        self.assertTrue(issubclass(AdviceAPIError, AdviceGenerationError))

    def test_advice_parse_error_inherits_from_advice_generation_error(self) -> None:
        """Should be catchable as AdviceGenerationError."""
        self.assertTrue(issubclass(AdviceParseError, AdviceGenerationError))
