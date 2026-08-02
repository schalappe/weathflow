"""Tests for AdviceGenerator service."""

import json
from unittest.mock import MagicMock

import anthropic
import pytest

from app.services.advice.generator import AdviceGenerator
from app.services.advice.models import AdviceResponse, MonthData
from app.services.advice.prompt import ADVICE_SYSTEM_PROMPT
from app.services.exceptions import AdviceAPIError, AdviceGenerationError, AdviceParseError, InsufficientDataError


def _month(year: int = 2025, month: int = 1) -> MonthData:
    """Build observed month data."""
    return MonthData(
        year=year,
        month=month,
        total_income=3000,
        total_core=1500,
        total_choice=900,
        total_compound=600,
        core_percentage=50,
        choice_percentage=30,
        compound_percentage=20,
        score=3,
        score_label="Great",
    )


def _decision_json(output_type: str = "recommendation") -> str:
    """Build model response JSON."""
    output: dict[str, object] = {
        "type": output_type,
        "priority": "high",
        "trace": {
            "summary": "Écart matériel observé.",
            "details": {
                "observations": [
                    {
                        "fact": "240 € contre 120 € en moyenne.",
                        "period": "2025-01 à 2025-03",
                        "scope": "CHOICE / Dining out",
                        "source": "observed_data",
                    }
                ],
                "calculations": ["240 - 120 = 120"],
                "conventions": [],
                "limits": [],
            },
        },
    }
    if output_type == "recommendation":
        output["action"] = "Réduire les repas au restaurant."
        output["amount"] = 120
    else:
        output["conclusion"] = "Aucune action n'est justifiée."
    return json.dumps({"outputs": [output]})


def _generator() -> AdviceGenerator:
    """Build generator with mocked API client."""
    generator = AdviceGenerator(api_key="test-key")
    generator._client = MagicMock()
    return generator


def test_prompt_requires_selective_observed_decisions_without_quota() -> None:
    """Prompt requests strict decision outputs and no artificial quota."""
    assert '"outputs"' in ADVICE_SYSTEM_PROMPT
    assert "observed_data" in ADVICE_SYSTEM_PROMPT
    assert "no_action" in ADVICE_SYSTEM_PROMPT
    assert "Exactement 3" not in ADVICE_SYSTEM_PROMPT


def test_generate_advice_returns_strict_decision_output() -> None:
    """Public generation parses model response into decision outputs."""
    generator = _generator()
    response = MagicMock()
    response.content = [MagicMock(text=_decision_json())]
    generator._client.messages.create.return_value = response  # type: ignore[attr-defined]

    result = generator.generate_advice(_month(month=2), [_month(month=1)])

    assert isinstance(result, AdviceResponse)
    assert result.outputs[0].type == "recommendation"


def test_generate_advice_accepts_no_action_conclusion() -> None:
    """Public generation accepts justified no-action output."""
    generator = _generator()
    response = MagicMock()
    response.content = [MagicMock(text=f"```json\n{_decision_json('no_action')}\n```")]
    generator._client.messages.create.return_value = response  # type: ignore[attr-defined]

    result = generator.generate_advice(_month(month=2), [_month(month=1)])

    assert result.outputs[0].type == "no_action"


def test_generate_advice_rejects_historical_contract() -> None:
    """Generation rejects historical quota response."""
    generator = _generator()
    response = MagicMock()
    response.content = [
        MagicMock(text='{"analysis":"old","problem_areas":[],"recommendations":[],"encouragement":"old"}')
    ]
    generator._client.messages.create.return_value = response  # type: ignore[attr-defined]

    with pytest.raises(AdviceParseError):
        generator.generate_advice(_month(month=2), [_month(month=1)])


def test_generate_advice_requires_history_before_api_call() -> None:
    """Generation requires one older month."""
    generator = _generator()

    with pytest.raises(InsufficientDataError):
        generator.generate_advice(_month(), [])

    generator._client.messages.create.assert_not_called()  # type: ignore[attr-defined]


def test_prompt_includes_all_observed_months() -> None:
    """Generation prompt includes current and historical observations."""
    generator = _generator()

    prompt = generator._build_user_prompt(_month(month=2), [_month(month=1)])

    assert prompt.count('"month":') == 2
    assert '"total_income": 3000.0' in prompt


def test_api_authentication_error_is_explicit() -> None:
    """Authentication failure maps to generation error."""
    generator = _generator()
    generator._client.messages.create.side_effect = anthropic.AuthenticationError(  # type: ignore[attr-defined]
        message="Invalid API key", response=MagicMock(), body=None
    )

    with pytest.raises(AdviceGenerationError, match="API key"):
        generator._call_claude_api("prompt")


def test_api_connection_error_is_retryable() -> None:
    """Connection failure maps to retryable advice error."""
    generator = _generator()
    generator._client.messages.create.side_effect = anthropic.APIConnectionError(  # type: ignore[attr-defined]
        request=MagicMock()
    )

    with pytest.raises(AdviceAPIError) as error:
        generator._call_claude_api("prompt")

    assert error.value.retry_count == 3


def test_empty_api_response_is_invalid() -> None:
    """Empty model response fails parsing."""
    generator = _generator()
    response = MagicMock()
    response.content = []
    generator._client.messages.create.return_value = response  # type: ignore[attr-defined]

    with pytest.raises(AdviceParseError):
        generator._call_claude_api("prompt")


def test_thinking_mode_skips_reasoning_and_returns_text() -> None:
    """Thinking mode configures budget and extracts final text."""
    generator = AdviceGenerator(api_key="test-key", thinking_enabled=True, thinking_budget=5000)
    generator._client = MagicMock()
    thinking = MagicMock(type="thinking", thinking="internal")
    text = MagicMock(type="text", text=_decision_json())
    response = MagicMock(content=[thinking, text])
    generator._client.messages.create.return_value = response  # type: ignore[attr-defined]

    result = generator._call_claude_api("prompt")
    call = generator._client.messages.create.call_args.kwargs  # type: ignore[attr-defined]

    assert result == _decision_json()
    assert call["thinking"] == {"type": "enabled", "budget_tokens": 5000}
