"""Tests for AdviceGenerator service."""

import json
from datetime import date, datetime
from unittest.mock import MagicMock

import anthropic
import pytest

from app.services.advice.generator import AdviceGenerator
from app.services.advice.models import (
    ActivePriorityContext,
    AdviceContext,
    AdviceResponse,
    CommitmentFactContext,
    EmergencyFundFactContext,
    IncomeFactContext,
    MonthData,
)
from app.services.advice.prompt import ADVICE_SYSTEM_PROMPT
from app.services.advice.service import resolve_clarification, validate_income_usage
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
        output["income_dependent"] = False
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


def test_clarification_requires_distinct_material_effects() -> None:
    """Wording-only alternatives cannot create a priority question."""
    response = json.dumps(
        {
            "outputs": [
                {
                    "type": "clarification",
                    "priority": "high",
                    "subject": "Épargne",
                    "observation": "600 € sont disponibles.",
                    "possible_effect": "La destination peut changer.",
                    "question": "Quelle est votre priorité active ?",
                    "fact_type": "active_priority",
                    "material_effects": ["Même action", "Même action"],
                }
            ]
        }
    )

    with pytest.raises(AdviceParseError):
        _generator()._parse_response(response)


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


def test_prompt_keeps_expired_priority_visible_but_inactive() -> None:
    """Expired priority reaches materiality check without becoming proof."""
    context = AdviceContext(
        active_priority=ActivePriorityContext(
            goal="Fonds d'urgence",
            target="6 000 €",
            deadline=None,
            state="to_confirm",
            last_confirmed_at=datetime(2026, 1, 1),
            valid_until=datetime(2026, 6, 30),
        )
    )

    prompt = _generator()._build_user_prompt(
        _month(month=2),
        [_month(month=1)],
        context,
    )

    assert '"state": "to_confirm"' in prompt
    assert "peut changer l'action" in prompt
    assert "reste visible mais inactif" in prompt


def test_prompt_defines_emergency_fund_materiality_and_trajectory() -> None:
    """Prompt keeps stocks declared and prescribes canonical trajectory math."""
    confirmed_at = datetime(2026, 8, 2)
    context = AdviceContext(
        active_priority=ActivePriorityContext(
            goal="Fonds d'urgence",
            target="5 400 €",
            state="active",
            last_confirmed_at=confirmed_at,
            valid_until=datetime(2027, 1, 29),
        ),
        emergency_fund_facts=[
            EmergencyFundFactContext(
                fact_type="liquid_reserve",
                amount=2_000,
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2026, 9, 1),
            ),
            EmergencyFundFactContext(
                fact_type="safety_floor",
                amount=5_400,
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2027, 1, 29),
            ),
            EmergencyFundFactContext(
                fact_type="priority_allocation",
                amount=0,
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2026, 9, 1),
            ),
        ],
    )

    prompt = _generator()._build_user_prompt(_month(month=2), [_month(month=1)], context)

    assert '"liquid_reserve":' not in prompt
    assert '"fact_type": "liquid_reserve"' in prompt
    assert "plancher - réserve liquide non affectée - montant déjà affecté" in prompt
    assert "revenu disponible habituel mensuel - dépenses essentielles" in prompt
    assert "N'infère jamais ces trois faits depuis les transactions" in prompt
    assert "conclusion `no_action`" in prompt


def test_prompt_calibrates_income_without_double_counting_observed_entries() -> None:
    """Prompt requires reliable declared income and single-counted expected entries."""
    confirmed_at = datetime(2026, 8, 2)
    context = AdviceContext(
        income_facts=[
            IncomeFactContext(
                fact_type="usual_disposable_income",
                amount=3_200,
                frequency="monthly",
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2026, 10, 31),
            ),
            IncomeFactContext(
                fact_type="expected_one_off_income",
                amount=1_500,
                expected_date=date(2026, 8, 3),
                matched_transaction=True,
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2026, 8, 3, 23, 59),
            ),
        ]
    )

    prompt = _generator()._build_user_prompt(_month(month=8), [_month(month=7)], context)

    assert '"fact_type": "usual_disposable_income"' in prompt
    assert '"frequency": "monthly"' in prompt
    assert '"expected_date": "2026-08-03"' in prompt
    assert '"matched_transaction": true' in prompt
    assert "ne constitue pas un revenu fiable" in prompt
    assert "aucun montant dépendant du revenu" in prompt
    assert "une seule fois" in prompt
    assert "hebdomadaire × 52 / 12" in prompt


def test_income_dependent_output_requires_active_income_trace() -> None:
    """Income-dependent amount without declared citation is rejected."""
    advice = AdviceResponse.model_validate_json(_decision_json())
    recommendation = advice.outputs[0]
    assert recommendation.type == "recommendation"
    advice = AdviceResponse(
        outputs=[
            recommendation.model_copy(
                update={
                    "income_dependent": True,
                    "trace": recommendation.trace.model_copy(update={"summary": "Le revenu borne ce montant."}),
                }
            )
        ]
    )

    with pytest.raises(AdviceParseError):
        validate_income_usage(advice, [], 2025, 1)


def test_income_normalization_rejects_nonderivable_precision() -> None:
    """Income normalization cannot drift beyond currency precision."""
    payload = json.loads(_decision_json())
    output = payload["outputs"][0]
    output["income_dependent"] = True
    details = output["trace"]["details"]
    details["conventions"] = ["Fréquence mensuelle."]
    details["declared_facts"] = [
        {
            "fact_type": "usual_disposable_income",
            "amount": 3_200,
            "frequency": "monthly",
            "expected_date": None,
            "matched_transaction": False,
            "state": "active",
            "last_confirmed_at": "2025-01-01T00:00:00",
            "valid_until": "2025-03-31T00:00:00",
            "can_correct": True,
            "can_delete": True,
        }
    ]
    details["income_normalizations"] = [
        {
            "fact_type": "usual_disposable_income",
            "source_amount": 3_200,
            "source_frequency": "monthly",
            "period": "2025-01",
            "conversion": "monthly",
            "normalized_amount": 3_200.01,
        }
    ]
    advice = AdviceResponse.model_validate(payload)
    context = IncomeFactContext(
        fact_type="usual_disposable_income",
        amount=3_200,
        frequency="monthly",
        state="active",
        last_confirmed_at=datetime(2025, 1, 1),
        valid_until=datetime(2025, 3, 31),
    )

    with pytest.raises(AdviceParseError):
        validate_income_usage(advice, [context], 2025, 1)


def test_income_clarification_can_be_skipped() -> None:
    """Income clarification resolves to an explicit abstention."""
    advice = AdviceResponse.model_validate(
        {
            "outputs": [
                {
                    "type": "clarification",
                    "priority": "medium",
                    "subject": "Capacité soutenable",
                    "observation": "Le revenu fiable est absent.",
                    "possible_effect": "Le montant peut changer.",
                    "question": "Quel est votre revenu disponible habituel ?",
                    "fact_type": "usual_disposable_income",
                    "material_effects": ["Calculer une capacité.", "Ne fournir aucun montant."],
                }
            ]
        }
    )

    resolved = resolve_clarification(advice, 2026, 8, "skip")

    assert resolved.outputs[0].type == "unresolved"
    assert "revenu disponible habituel" in resolved.outputs[0].trace.details.limits[0]


def test_prompt_protects_obligations_and_debt_before_savings() -> None:
    """Prompt subtracts hard commitments and keeps debt contracts declared."""
    confirmed_at = datetime(2026, 8, 2)
    context = AdviceContext(
        commitment_facts=[
            CommitmentFactContext(
                fact_id=1,
                fact_type="recurring_obligation",
                label="Pension alimentaire",
                amount=300,
                frequency="monthly",
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2026, 10, 31),
            ),
            CommitmentFactContext(
                fact_id=2,
                fact_type="debt_terms",
                label="Prêt auto",
                minimum_payment=250,
                annual_rate=4.2,
                state="active",
                last_confirmed_at=confirmed_at,
                valid_until=datetime(2026, 10, 31),
            ),
        ]
    )

    prompt = _generator()._build_user_prompt(_month(month=2), [_month(month=1)], context)

    assert '"fact_type": "recurring_obligation"' in prompt
    assert '"fact_type": "debt_terms"' in prompt
    assert "obligations exigibles" in prompt
    assert "paiements minimums" in prompt
    assert "prime sur toute épargne" in prompt
    assert "50/30/20" in prompt
    assert "N'infère jamais" in prompt
    assert "date explicite la plus proche" in prompt


def test_debt_clarification_can_be_skipped() -> None:
    """Debt clarification resolves to an explicit abstention."""
    advice = AdviceResponse.model_validate(
        {
            "outputs": [
                {
                    "type": "clarification",
                    "priority": "high",
                    "subject": "Dette auto",
                    "observation": "Le minimum est inconnu.",
                    "possible_effect": "Le paiement peut primer sur l'épargne.",
                    "question": "Quel est le minimum exigible ?",
                    "fact_type": "debt_terms",
                    "material_effects": ["Payer le minimum.", "Suspendre l'épargne."],
                }
            ]
        }
    )

    resolved = resolve_clarification(advice, 2025, 7, "skip")

    assert resolved.outputs[0].type == "unresolved"
    assert "Information non fournie (conditions de dette)" in resolved.outputs[0].trace.details.limits[0]


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
    generator._client.messages.create.return_value = response

    result = generator._call_claude_api("prompt")
    call = generator._client.messages.create.call_args.kwargs

    assert result == _decision_json()
    assert call["thinking"] == {"type": "enabled", "budget_tokens": 5000}
