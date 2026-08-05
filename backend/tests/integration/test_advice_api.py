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
    common: dict[str, object] = {
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
                        "evidence_type": "presence",
                        "source_months": ["2025-01"],
                        "transaction_ids": [],
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
            income_dependent=False,
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
        "evidence_type": "presence",
        "source_months": ["2025-01"],
        "transaction_ids": [],
    }
    assert output["trace"]["details"]["calculations"] == ["240 € - 120 € = 120 €."]
    assert mock_generator.generate_advice.call_count == 1


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.services.advice.service.advice_response_to_json")
@patch("app.api.deps.AdviceGenerator")
def test_generation_keeps_robust_output_beside_one_material_priority_question(
    mock_generator_class: MagicMock,
    mock_serialize: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Material priority uncertainty adds one question without hiding robust advice."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    robust_output = _advice().model_dump(mode="json")["outputs"][0]
    clarification = {
        "type": "clarification",
        "priority": "high",
        "subject": "Trajectoire d'épargne",
        "observation": "600 € sont disponibles pour l'épargne ce mois-ci.",
        "possible_effect": "La destination, le montant affecté et l'échéance changent selon la priorité.",
        "question": "Quelle est votre priorité financière active ?",
        "fact_type": "active_priority",
        "material_effects": [
            "Fonds d'urgence : affecter les 600 € à la réserve.",
            "Dette auto : affecter les 600 € au remboursement anticipé.",
        ],
    }
    generated_advice = {"outputs": [robust_output, clarification]}
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = generated_advice
    mock_generator_class.return_value = mock_generator
    mock_serialize.return_value = json.dumps(generated_advice)

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 200
    outputs = response.json()["advice"]["outputs"]
    assert [output["type"] for output in outputs] == ["recommendation", "clarification"]
    assert sum(output["type"] == "clarification" for output in outputs) == 1
    assert len(set(outputs[1]["material_effects"])) == 2


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_skip_replaces_persisted_question_with_unresolved_output(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Skipped clarification stays resolved after reload without memory."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    robust_output = _advice().model_dump(mode="json")["outputs"][0]
    clarification = {
        "type": "clarification",
        "priority": "medium",
        "subject": "Trajectoire d'épargne",
        "observation": "600 € sont disponibles pour l'épargne.",
        "possible_effect": "La destination dépend de la priorité active.",
        "question": "Quelle est votre priorité financière active ?",
        "fact_type": "active_priority",
        "material_effects": ["Fonds d'urgence", "Dette"],
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = AdviceResponse.model_validate(
        {"outputs": [robust_output, clarification]}
    )
    mock_generator_class.return_value = mock_generator
    client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    rejected_delete = client.post(
        "/api/advice/generate",
        json={"year": 2025, "month": 10, "clarification_action": "delete"},
    )

    skipped = client.post(
        "/api/advice/generate",
        json={"year": 2025, "month": 10, "clarification_action": "skip"},
    )
    reloaded = client.get("/api/advice/2025/10")

    assert rejected_delete.status_code == 422
    assert skipped.status_code == 200
    assert [output["type"] for output in skipped.json()["advice"]["outputs"]] == [
        "recommendation",
        "unresolved",
    ]
    assert reloaded.json()["advice"]["outputs"][1]["type"] == "unresolved"
    assert client.get("/api/advice/context/active-priority").json() == {"priority": None}
    assert mock_generator.generate_advice.call_count == 2


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.services.advice.service.advice_response_to_json")
@patch("app.api.deps.AdviceGenerator")
def test_priority_answer_is_remembered_and_changes_generated_output(
    mock_generator_class: MagicMock,
    mock_serialize: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Remembered answer reaches generation and its declared-fact trace."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    output = _advice().model_dump(mode="json")["outputs"][0]
    output["trace"]["details"]["declared_facts"] = [
        {
            "fact_type": "active_priority",
            "goal": "Constituer un fonds d'urgence",
            "target": "6 000 €",
            "deadline": "2027-06-30",
            "state": "active",
            "last_confirmed_at": "2026-08-02T12:00:00",
            "valid_until": "2027-01-29T12:00:00",
            "can_correct": True,
            "can_delete": True,
        }
    ]
    generated_advice = {"outputs": [output]}
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = generated_advice
    mock_generator_class.return_value = mock_generator
    mock_serialize.return_value = json.dumps(generated_advice)

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "active_priority": {
                "goal": "Constituer un fonds d'urgence",
                "target": "6 000 €",
                "deadline": "2027-06-30",
            },
            "remember_priority": True,
        },
    )

    assert response.status_code == 200
    context = client.get("/api/advice/context/active-priority").json()["priority"]
    assert context["goal"] == "Constituer un fonds d'urgence"
    generation_context = mock_generator.generate_advice.call_args.args[2]
    assert generation_context.active_priority.goal == context["goal"]
    assert generation_context.active_priority.state == "active"
    citation = response.json()["advice"]["outputs"][0]["trace"]["details"]["declared_facts"][0]
    assert citation["fact_type"] == "active_priority"
    assert citation["state"] == "active"
    assert citation["can_correct"] is True
    assert citation["can_delete"] is True


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_first_session_priority_keeps_clarification_for_correction(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """First session answer leaves the persisted question available."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    robust_output = _advice().model_dump(mode="json")["outputs"][0]
    clarification = {
        "type": "clarification",
        "priority": "high",
        "subject": "Trajectoire d'épargne",
        "observation": "600 € sont disponibles pour l'épargne.",
        "possible_effect": "La destination dépend de la priorité active.",
        "question": "Quelle est votre priorité financière active ?",
        "fact_type": "active_priority",
        "material_effects": ["Fonds d'urgence", "Dette"],
    }
    session_output = _advice().model_dump(mode="json")["outputs"][0]
    session_output["trace"]["details"]["declared_facts"] = [
        {
            "fact_type": "active_priority",
            "goal": "Préparer un voyage",
            "target": "2 000 €",
            "deadline": None,
            "state": "session",
            "last_confirmed_at": "2026-08-02T12:00:00",
            "valid_until": None,
            "can_correct": True,
            "can_delete": True,
        }
    ]
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = [
        AdviceResponse.model_validate({"outputs": [robust_output, clarification]}),
        AdviceResponse.model_validate({"outputs": [session_output]}),
    ]
    mock_generator_class.return_value = mock_generator
    client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    answered = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "active_priority": {
                "goal": "Préparer un voyage",
                "target": "2 000 €",
                "deadline": None,
            },
            "remember_priority": False,
        },
    )
    reloaded = client.get("/api/advice/2025/10")

    assert answered.status_code == 200
    assert answered.json()["advice"]["clarification_trace"] == {
        "questions_consumed": 1,
        "questions": [
            {
                "question_number": 1,
                "fact_type": "active_priority",
                "decision_lever": "action_or_priority",
                "outcome": "answered",
            }
        ],
        "stop_reason": "no_remaining_decision_impact",
    }
    assert reloaded.status_code == 200
    assert reloaded.json()["exists"] is True
    assert reloaded.json()["advice"]["outputs"][1]["type"] == "clarification"
    assert client.get("/api/advice/context/active-priority").json() == {"priority": None}


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_session_priority_changes_only_current_response(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Session answer neutralizes old memory and avoids advice cache."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Fonds d'urgence", "target": "6 000 €", "deadline": None},
    )
    output = _advice().model_dump(mode="json")["outputs"][0]
    output["trace"]["details"]["declared_facts"] = [
        {
            "fact_type": "active_priority",
            "goal": "Préparer un voyage",
            "target": "2 000 €",
            "deadline": None,
            "state": "session",
            "last_confirmed_at": "2026-08-02T12:00:00",
            "valid_until": None,
            "can_correct": True,
            "can_delete": True,
        }
    ]
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {"outputs": [output]}
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "active_priority": {
                "goal": "Préparer un voyage",
                "target": "2 000 €",
                "deadline": None,
            },
            "remember_priority": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["advice"]["outputs"][0]["trace"]["details"]["declared_facts"][0]["state"] == "session"
    context = client.get("/api/advice/context/active-priority").json()["priority"]
    assert context["goal"] == "Fonds d'urgence"
    assert context["state"] == "to_confirm"
    assert db_session.query(Advice).count() == 0


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_no_material_gap_persists_only_no_action_output(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """No material gap stores explicit zero-question trace."""
    month = _create_month(db_session, 2025, 10)
    _create_month(db_session, 2025, 9)
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = _advice("no_action")
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 200
    payload = response.json()["advice"]
    assert [output["type"] for output in payload["outputs"]] == ["no_action"]
    assert payload["clarification_trace"] == {
        "questions_consumed": 0,
        "questions": [],
        "stop_reason": "no_remaining_decision_impact",
    }
    stored = db_session.query(Advice).filter(Advice.month_id == month.id).one()
    assert set(json.loads(stored.advice_text)) == {"outputs", "clarification_trace"}


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
    assert set(json.loads(stored.advice_text)) == {"outputs", "clarification_trace"}


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


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_four_simultaneous_clarifications_are_ordered_and_capped(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Canonical queue shows coverage, obligation, then income; floor stays unresolved."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    robust_output = _advice().model_dump(mode="json")["outputs"][0]

    def clarification(
        fact_type: str,
        subject: str,
        question: str,
        answer_ease: str,
    ) -> dict[str, object]:
        """Build one canonical candidate."""
        return {
            "type": "clarification",
            "priority": "high",
            "decision_lever": "amount",
            "answer_ease": answer_ease,
            "subject": subject,
            "observation": "Une capacité mensuelle de 600 € est observée.",
            "possible_effect": "La réponse change le montant recommandé.",
            "question": question,
            "fact_type": fact_type,
            "material_effects": ["Aucune action", "Affecter 600 €"],
            **({"coverage_months": ["2025-09", "2025-10"]} if fact_type == "period_coverage" else {}),
        }

    draft = {
        "outputs": [
            robust_output,
            clarification(
                "safety_floor",
                "Plancher de sécurité",
                "Quel plancher souhaitez-vous protéger ?",
                "moderate",
            ),
            clarification(
                "usual_disposable_income",
                "Revenu habituel",
                "Quel est votre revenu disponible habituel ?",
                "easy",
            ),
            clarification(
                "recurring_obligation",
                "Obligation récurrente",
                "Quel montant devez-vous payer chaque mois ?",
                "moderate",
            ),
            clarification(
                "period_coverage",
                "Couverture",
                "Les deux mois couvrent-ils tous vos comptes ?",
                "easy",
            ),
        ]
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = draft
    mock_generator_class.return_value = mock_generator

    responses = [client.post("/api/advice/generate", json={"year": 2025, "month": 10})]
    for _ in range(3):
        responses.append(
            client.post(
                "/api/advice/generate",
                json={"year": 2025, "month": 10, "clarification_action": "skip"},
            )
        )

    expected_questions = [
        "period_coverage",
        "recurring_obligation",
        "usual_disposable_income",
    ]
    for index, response in enumerate(responses[:3], start=1):
        assert response.status_code == 200
        outputs = response.json()["advice"]["outputs"]
        assert sum(output["type"] == "clarification" for output in outputs) == 1
        assert (
            next(output for output in outputs if output["type"] == "clarification")["fact_type"]
            == (expected_questions[index - 1])
        )
        assert any(output["type"] == "recommendation" for output in outputs)
        trace = response.json()["advice"]["clarification_trace"]
        assert trace["questions_consumed"] == index
        assert [question["fact_type"] for question in trace["questions"]] == expected_questions[:index]
        assert trace["stop_reason"] == "question_pending"

    final_advice = responses[3].json()["advice"]
    assert responses[3].status_code == 200
    assert all(output["type"] != "clarification" for output in final_advice["outputs"])
    assert any(output["type"] == "recommendation" for output in final_advice["outputs"])
    assert any(
        output["type"] == "unresolved" and "Plancher de sécurité" in output["conclusion"]
        for output in final_advice["outputs"]
    )
    assert final_advice["clarification_trace"] == {
        "questions_consumed": 3,
        "questions": [
            {
                "question_number": index,
                "fact_type": fact_type,
                "decision_lever": "amount",
                "outcome": "skipped",
            }
            for index, fact_type in enumerate(expected_questions, start=1)
        ],
        "stop_reason": "quota_reached",
    }
    assert mock_generator.generate_advice.call_count == 4


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_decision_lever_precedes_display_priority(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Action-changing question precedes higher-display-priority amount question."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    common = {
        "type": "clarification",
        "subject": "Trajectoire d'épargne",
        "observation": "600 € restent disponibles.",
        "possible_effect": "La réponse change le conseil.",
        "material_effects": ["Aucune action", "Affecter 600 €"],
        "answer_ease": "easy",
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                **common,
                "priority": "high",
                "decision_lever": "amount",
                "question": "La période couvre-t-elle tous vos comptes ?",
                "fact_type": "period_coverage",
                "coverage_months": ["2025-09", "2025-10"],
            },
            {
                **common,
                "priority": "medium",
                "decision_lever": "action_or_priority",
                "question": "Quelle est votre priorité active ?",
                "fact_type": "active_priority",
            },
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 200
    question = next(output for output in response.json()["advice"]["outputs"] if output["type"] == "clarification")
    assert question["fact_type"] == "active_priority"
