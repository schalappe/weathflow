"""Integration tests for advice API endpoints."""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.services.advice.models import AdviceResponse
from app.services.exceptions import AdviceAPIError

MOCK_API_KEY_ENV = {"ANTHROPIC_API_KEY": "test-key-for-integration-tests"}


def _create_month(db: Session, year: int, month: int) -> Month:
    """Create persisted month."""
    record = Month(
        year=year,
        month=month,
        total_income=3000.0,
        total_core=1500.0,
        total_choice=900.0,
        total_compound=600.0,
        core_percentage=50.0,
        choice_percentage=30.0,
        compound_percentage=20.0,
        score=2,
        score_label="Okay",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _advice(output_type: str = "recommendation") -> AdviceResponse:
    """Build strict generated advice."""
    common = {
        "type": output_type,
        "priority": "high",
        "trace": {
            "summary": "Écart matériel observé sur la restauration.",
            "details": {
                "observations": [
                    {
                        "fact": "240 € ce mois contre 120 € en moyenne.",
                        "period": "2025-08 à 2025-10",
                        "scope": "Transactions CHOICE / Dining out",
                        "source": "observed_data",
                    }
                ],
                "calculations": ["240 € - 120 € = 120 €."],
                "conventions": ["Écart supérieur à 20 % considéré matériel."],
                "limits": [],
            },
        },
    }
    if output_type == "recommendation":
        common.update(
            action="Réduire les repas au restaurant à la moyenne récente.",
            amount=120,
            deadline="2025-11-30",
        )
    else:
        common["conclusion"] = "Aucune action n'est justifiée par les écarts observés."
    return AdviceResponse.model_validate({"outputs": [common]})


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_generate_cache_and_retrieve_decision_outputs(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Generation, cache, and read preserve auditable decision output."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = _advice()
    mock_generator_class.return_value = mock_generator

    generated = client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    cached = client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    retrieved = client.get("/api/advice/2025/10")

    assert generated.status_code == 200
    assert generated.json()["was_cached"] is False
    assert generated.json()["is_valid"] is True
    assert cached.json()["was_cached"] is True
    assert retrieved.json()["exists"] is True
    assert retrieved.json()["is_valid"] is True
    output = retrieved.json()["advice"]["outputs"][0]
    assert output["type"] == "recommendation"
    assert output["trace"]["details"]["observations"][0] == {
        "fact": "240 € ce mois contre 120 € en moyenne.",
        "period": "2025-08 à 2025-10",
        "scope": "Transactions CHOICE / Dining out",
        "source": "observed_data",
    }
    assert output["trace"]["details"]["calculations"] == ["240 € - 120 € = 120 €."]
    assert mock_generator.generate_advice.call_count == 1


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_no_material_gap_persists_only_no_action_output(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """No material gap stores no-action without historical quota fields."""
    month = _create_month(db_session, 2025, 10)
    _create_month(db_session, 2025, 9)
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = _advice("no_action")
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 200
    payload = response.json()["advice"]
    assert [output["type"] for output in payload["outputs"]] == ["no_action"]
    assert set(payload) == {"outputs"}
    stored = db_session.query(Advice).filter(Advice.month_id == month.id).one()
    assert set(json.loads(stored.advice_text)) == {"outputs"}


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_regeneration_replaces_historical_contract(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Explicit regeneration cleanly replaces historical advice JSON."""
    month = _create_month(db_session, 2025, 10)
    _create_month(db_session, 2025, 9)
    db_session.add(
        Advice(
            month_id=month.id,
            advice_text='{"analysis":"old","problem_areas":[],"recommendations":[],"encouragement":"old"}',
        )
    )
    db_session.commit()
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = _advice()
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={"year": 2025, "month": 10, "regenerate": True},
    )

    assert response.status_code == 200
    assert db_session.query(Advice).filter(Advice.month_id == month.id).count() == 1
    stored = db_session.query(Advice).filter(Advice.month_id == month.id).one()
    assert set(json.loads(stored.advice_text)) == {"outputs"}


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_generation_reports_api_failure(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Model outage returns service unavailable."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = AdviceAPIError(retry_count=3)
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 503
    assert "AI service temporarily unavailable" in response.json()["detail"]


def test_generation_requires_history(client: TestClient, db_session: Session) -> None:
    """Generation requires one older month."""
    _create_month(db_session, 2025, 10)

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 400
    assert "Not enough historical data" in response.json()["detail"]
