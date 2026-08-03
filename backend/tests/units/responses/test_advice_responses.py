"""Unit tests for advice API contracts."""

import json

import pytest
from pydantic import ValidationError

from app.responses.advice import AdviceData, GenerateAdviceRequest


def _trace(calculations: list[str] | None = None) -> dict[str, object]:
    """Build auditable decision trace."""
    return {
        "summary": "Les dépenses de restauration dépassent la moyenne récente.",
        "details": {
            "observations": [
                {
                    "fact": "240 € dépensés en restauration contre 120 € en moyenne.",
                    "period": "2025-10 à 2025-12",
                    "scope": "Transactions CHOICE / Dining out",
                    "source": "observed_data",
                }
            ],
            "calculations": (calculations if calculations is not None else ["240 € - 120 € = 120 € d'écart mensuel."]),
            "conventions": ["Écart matériel retenu au-delà de 20 %."],
            "limits": ["Trois mois observés seulement."],
        },
    }


def test_parses_recommendation_with_auditable_trace() -> None:
    """Recommendation exposes fact, period, scope, calculation, amount, deadline."""
    advice = AdviceData.model_validate_json(
        json.dumps(
            {
                "outputs": [
                    {
                        "type": "recommendation",
                        "income_dependent": False,
                        "priority": "high",
                        "action": "Réduire les repas au restaurant à la moyenne récente.",
                        "amount": 120,
                        "deadline": "2026-01-31",
                        "trace": _trace(),
                    }
                ]
            }
        )
    )

    output = advice.outputs[0]
    assert output.type == "recommendation"
    assert output.trace.details.observations[0].source == "observed_data"
    assert output.trace.details.observations[0].period == "2025-10 à 2025-12"
    assert output.trace.details.observations[0].scope == "Transactions CHOICE / Dining out"
    assert output.trace.details.calculations == ["240 € - 120 € = 120 € d'écart mensuel."]
    assert output.amount == 120
    assert output.deadline is not None
    assert output.deadline.isoformat() == "2026-01-31"


def test_accepts_no_action_without_invented_recommendation() -> None:
    """Stable month yields one no-action conclusion and no historical fields."""
    advice = AdviceData.model_validate(
        {
            "outputs": [
                {
                    "type": "no_action",
                    "priority": "low",
                    "conclusion": "Aucune action n'est justifiée par les écarts observés.",
                    "trace": _trace([]),
                }
            ]
        }
    )

    payload = advice.model_dump(mode="json")
    assert payload["outputs"][0]["type"] == "no_action"
    assert set(payload) == {"outputs"}
    assert (
        not {
            "problem_areas",
            "spending_patterns",
            "progress_review",
            "monthly_goal",
            "encouragement",
        }
        & payload.keys()
    )


def test_omits_underived_recommendation_amount_and_deadline() -> None:
    """Recommendation JSON omits optional values without derivation."""
    advice = AdviceData.model_validate(
        {
            "outputs": [
                {
                    "type": "recommendation",
                    "income_dependent": False,
                    "priority": "low",
                    "action": "Maintenir la trajectoire actuelle.",
                    "trace": _trace([]),
                }
            ]
        }
    )

    output = advice.model_dump(mode="json")["outputs"][0]
    assert "amount" not in output
    assert "deadline" not in output


def test_rejects_amount_without_deriving_calculation() -> None:
    """Recommendation amount requires supporting calculation."""
    with pytest.raises(ValidationError):
        AdviceData.model_validate(
            {
                "outputs": [
                    {
                        "type": "recommendation",
                        "income_dependent": False,
                        "priority": "high",
                        "action": "Réduire les repas au restaurant.",
                        "amount": 120,
                        "trace": _trace([]),
                    }
                ]
            }
        )


def test_rejects_historical_advice_contract() -> None:
    """Historical quota contract has no compatibility path."""
    with pytest.raises(ValidationError):
        AdviceData.model_validate(
            {
                "analysis": "Ancienne analyse",
                "problem_areas": [],
                "recommendations": [],
                "encouragement": "Ancien encouragement",
            }
        )


def test_generate_request_validates_period_and_defaults_cache_use() -> None:
    """Generation request validates period and defaults to cached advice."""
    with pytest.raises(ValidationError):
        GenerateAdviceRequest(year=1999, month=1)
    with pytest.raises(ValidationError):
        GenerateAdviceRequest(year=2025, month=13)

    request = GenerateAdviceRequest(year=2025, month=12)
    assert request.regenerate is False
