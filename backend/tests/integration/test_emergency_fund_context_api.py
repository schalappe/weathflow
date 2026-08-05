"""Integration tests for emergency-fund declared context."""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.emergency_fund_fact import EmergencyFundFact
from app.db.models.month import Month


def _create_month(db: Session, year: int, month: int) -> None:
    """Create canonical observed month."""
    db.add(
        Month(
            year=year,
            month=month,
            total_income=3_000,
            total_core=1_800,
            total_choice=500,
            total_compound=700,
            core_percentage=60,
            choice_percentage=16.67,
            compound_percentage=23.33,
            score=2,
            score_label="Okay",
        )
    )
    db.commit()


def test_emergency_fund_facts_are_stored_distinctly_and_remain_user_controlled(
    client: TestClient,
) -> None:
    """Reserve, floor, and allocation keep independent lifecycle and values."""
    for fact_type, amount in {
        "liquid_reserve": 2_000,
        "safety_floor": 5_400,
        "priority_allocation": 600,
    }.items():
        response = client.put(
            f"/api/advice/context/emergency-fund/{fact_type}",
            json={"amount": amount},
        )
        assert response.status_code == 200
        assert response.json()["fact"] == {
            "fact_type": fact_type,
            "amount": float(amount),
            "state": "active",
            "last_confirmed_at": response.json()["fact"]["last_confirmed_at"],
            "valid_until": response.json()["fact"]["valid_until"],
        }

    facts = client.get("/api/advice/context/emergency-fund").json()["facts"]
    assert {fact["fact_type"]: fact["amount"] for fact in facts} == {
        "liquid_reserve": 2_000,
        "safety_floor": 5_400,
        "priority_allocation": 600,
    }
    reserve = next(fact for fact in facts if fact["fact_type"] == "liquid_reserve")
    floor = next(fact for fact in facts if fact["fact_type"] == "safety_floor")
    assert reserve["valid_until"] < floor["valid_until"]

    corrected = client.put(
        "/api/advice/context/emergency-fund/liquid_reserve",
        json={"amount": 2_500},
    ).json()["fact"]
    assert corrected["amount"] == 2_500
    assert corrected["state"] == "corrected"

    deleted = client.delete("/api/advice/context/emergency-fund/priority_allocation")
    assert deleted.status_code == 204
    remaining = client.get("/api/advice/context/emergency-fund").json()["facts"]
    assert {fact["fact_type"] for fact in remaining} == {"liquid_reserve", "safety_floor"}


@patch("app.api.deps.AdviceGenerator")
def test_canonical_emergency_fund_trajectory_reaches_generation_and_trace(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Canonical facts produce 700 €/month, 3,400 € gap, and five-month trace."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Fonds d'urgence", "target": "5 400 €", "deadline": None},
    )
    for fact_type, amount in {
        "liquid_reserve": 2_000,
        "safety_floor": 5_400,
        "priority_allocation": 0,
    }.items():
        client.put(
            f"/api/advice/context/emergency-fund/{fact_type}",
            json={"amount": amount},
        )

    citations = [
        {
            "fact_type": "active_priority",
            "goal": "Fonds d'urgence",
            "target": "5 400 €",
            "deadline": None,
            "state": "active",
            "last_confirmed_at": "2026-08-02T12:00:00",
            "valid_until": "2027-01-29T12:00:00",
            "can_correct": True,
            "can_delete": True,
        },
        *[
            {
                "fact_type": fact_type,
                "amount": amount,
                "state": "active",
                "last_confirmed_at": "2026-08-02T12:00:00",
                "valid_until": "2026-09-01T12:00:00",
                "can_correct": True,
                "can_delete": True,
            }
            for fact_type, amount in {
                "liquid_reserve": 2_000,
                "safety_floor": 5_400,
                "priority_allocation": 0,
            }.items()
        ],
    ]
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "recommendation",
                "income_dependent": False,
                "priority": "high",
                "action": "Affecter 700 € par mois au fonds d'urgence.",
                "amount": 700,
                "deadline": "2025-12-31",
                "trace": {
                    "summary": "Un écart de 3 400 € reste à combler en environ cinq mois.",
                    "details": {
                        "observations": [
                            {
                                "fact": "3 000 € de revenus, 1 800 € d'essentiels et 500 € de discrétionnaire.",
                                "period": "2025-07",
                                "scope": "Transactions du mois",
                                "source": "observed_data",
                                "evidence_type": "presence",
                                "source_months": ["2025-01"],
                                "transaction_ids": [],
                            }
                        ],
                        "calculations": [
                            "3 000 € - 1 800 € - 500 € = 700 €/mois.",
                            "5 400 € - 2 000 € - 0 € = 3 400 €.",
                            "3 400 € / 700 € = 4,86, soit environ 5 mois.",
                        ],
                        "conventions": [],
                        "limits": [],
                        "declared_facts": citations,
                    },
                },
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 7})

    assert response.status_code == 200
    output = response.json()["advice"]["outputs"][0]
    assert output["amount"] == 700
    assert "3 400 €" in output["trace"]["summary"]
    assert "5 mois" in output["trace"]["details"]["calculations"][2]
    generation_context = mock_generator.generate_advice.call_args.args[2]
    assert generation_context.active_priority.goal == "Fonds d'urgence"
    assert {fact.fact_type: fact.amount for fact in generation_context.emergency_fund_facts} == {
        "liquid_reserve": 2_000,
        "safety_floor": 5_400,
        "priority_allocation": 0,
    }


@patch("app.api.deps.AdviceGenerator")
def test_material_fact_answer_is_remembered_before_next_clarification(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Answered fact becomes context; next material fact may be asked."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Trajectoire du fonds d'urgence",
                "observation": "Une capacité mensuelle de 700 € est observée.",
                "possible_effect": "Le plancher peut changer l'écart et l'échéance.",
                "question": "Quel plancher de sécurité souhaitez-vous protéger ?",
                "fact_type": "safety_floor",
                "material_effects": [
                    "Un plancher déjà atteint produit une conclusion sans action.",
                    "Un plancher supérieur produit une trajectoire d'épargne.",
                ],
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 7,
            "emergency_fund_fact": {
                "fact_type": "liquid_reserve",
                "amount": 2_000,
            },
            "remember_fact": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["advice"]["outputs"][0]["fact_type"] == "safety_floor"
    facts = client.get("/api/advice/context/emergency-fund").json()["facts"]
    assert {fact["fact_type"]: fact["amount"] for fact in facts} == {"liquid_reserve": 2_000}
    generation_context = mock_generator.generate_advice.call_args.args[2]
    assert generation_context.emergency_fund_facts[0].fact_type == "liquid_reserve"


@patch("app.api.deps.AdviceGenerator")
def test_reserve_and_allocation_meeting_floor_produce_no_action(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Reserve plus distinct allocation can close gap without double count."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Fonds d'urgence", "target": "5 400 €", "deadline": None},
    )
    amounts = {
        "liquid_reserve": 2_000,
        "safety_floor": 5_400,
        "priority_allocation": 3_400,
    }
    for fact_type, amount in amounts.items():
        client.put(
            f"/api/advice/context/emergency-fund/{fact_type}",
            json={"amount": amount},
        )
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "no_action",
                "priority": "low",
                "conclusion": "Le plancher de sécurité est atteint ; aucune affectation supplémentaire.",
                "trace": {
                    "summary": "2 000 € de réserve et 3 400 € déjà affectés atteignent 5 400 €.",
                    "details": {
                        "observations": [
                            {
                                "fact": "Une capacité mensuelle de 700 € est observée.",
                                "period": "2025-07",
                                "scope": "Transactions du mois",
                                "source": "observed_data",
                                "evidence_type": "presence",
                                "source_months": ["2025-01"],
                                "transaction_ids": [],
                            }
                        ],
                        "calculations": ["5 400 € - 2 000 € - 3 400 € = 0 €."],
                        "conventions": [],
                        "limits": [],
                        "declared_facts": [
                            {
                                "fact_type": fact_type,
                                "amount": amount,
                                "state": "active",
                                "last_confirmed_at": "2026-08-02T12:00:00",
                                "valid_until": "2027-01-29T12:00:00",
                                "can_correct": True,
                                "can_delete": True,
                            }
                            for fact_type, amount in amounts.items()
                        ],
                    },
                },
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 7})

    assert response.status_code == 200
    output = response.json()["advice"]["outputs"][0]
    assert output["type"] == "no_action"
    assert "aucune affectation supplémentaire" in output["conclusion"]
    assert output["trace"]["details"]["calculations"] == ["5 400 € - 2 000 € - 3 400 € = 0 €."]


def test_emergency_fund_freshness_expires_positions_and_floor_independently(
    client: TestClient,
    db_session: Session,
) -> None:
    """J+31 positions and J+181 floor stay visible but become inactive."""
    for fact_type, amount in {
        "liquid_reserve": 2_000,
        "safety_floor": 5_400,
        "priority_allocation": 400,
    }.items():
        client.put(
            f"/api/advice/context/emergency-fund/{fact_type}",
            json={"amount": amount},
        )
    for fact_type, age in {
        "liquid_reserve": 31,
        "safety_floor": 181,
        "priority_allocation": 31,
    }.items():
        fact = db_session.get(EmergencyFundFact, fact_type)
        assert fact is not None
        fact.last_confirmed_at = datetime.now() - timedelta(days=age)
        fact.valid_until = datetime.now() - timedelta(days=1)
    db_session.commit()

    facts = client.get("/api/advice/context/emergency-fund").json()["facts"]

    assert {fact["fact_type"] for fact in facts} == {
        "liquid_reserve",
        "safety_floor",
        "priority_allocation",
    }
    assert {fact["state"] for fact in facts} == {"to_confirm"}


@patch("app.api.deps.AdviceGenerator")
def test_transactions_alone_never_create_emergency_fund_context(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Observed flows cannot create or contest declared stocks and floor."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Trajectoire du fonds d'urgence",
                "observation": "Une capacité mensuelle de 700 € est observée.",
                "possible_effect": "La réserve change l'écart et l'échéance.",
                "question": "Quelle réserve liquide non affectée détenez-vous ?",
                "fact_type": "liquid_reserve",
                "material_effects": [
                    "Une réserve suffisante produit une conclusion sans action.",
                    "Une réserve insuffisante produit une trajectoire.",
                ],
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 7})

    assert response.status_code == 200
    assert mock_generator.generate_advice.call_args.args[2].emergency_fund_facts == []
    assert client.get("/api/advice/context/emergency-fund").json() == {"facts": []}


@patch("app.api.deps.AdviceGenerator")
def test_session_fact_keeps_blocking_question_available(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Deleting a session answer restores its persisted question."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    first_question = {
        "type": "clarification",
        "priority": "high",
        "subject": "Trajectoire du fonds d'urgence",
        "observation": "Une capacité mensuelle de 700 € est observée.",
        "possible_effect": "La réserve change l'écart et l'échéance.",
        "question": "Quelle réserve liquide non affectée détenez-vous ?",
        "fact_type": "liquid_reserve",
        "material_effects": ["Aucune action", "Trajectoire d'épargne"],
    }
    next_question = {
        **first_question,
        "question": "Quel plancher de sécurité souhaitez-vous protéger ?",
        "fact_type": "safety_floor",
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = [
        {"outputs": [first_question]},
        {"outputs": [next_question]},
    ]
    mock_generator_class.return_value = mock_generator
    client.post("/api/advice/generate", json={"year": 2025, "month": 7})

    answered = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 7,
            "emergency_fund_fact": {
                "fact_type": "liquid_reserve",
                "amount": 2_000,
            },
            "remember_fact": False,
        },
    )
    restored = client.get("/api/advice/2025/7")

    assert answered.status_code == 200
    assert answered.json()["advice"]["outputs"][0]["fact_type"] == "safety_floor"
    assert answered.json()["advice"]["outputs"][0]["question_number"] == 2
    assert restored.json()["advice"]["outputs"][0]["fact_type"] == "liquid_reserve"
    assert restored.json()["advice"]["outputs"][0]["question_number"] == 1


@patch("app.api.deps.AdviceGenerator")
def test_fourth_material_question_becomes_unresolved(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Three prior questions exhaust the global clarification budget."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    month = db_session.query(Month).filter_by(year=2025, month=7).one()
    current_question = {
        "type": "clarification",
        "priority": "high",
        "subject": "Trajectoire du fonds d'urgence",
        "observation": "Une capacité mensuelle de 700 € est observée.",
        "possible_effect": "La réserve change l'écart et l'échéance.",
        "question": "Quelle réserve liquide non affectée détenez-vous ?",
        "fact_type": "liquid_reserve",
        "question_number": 3,
        "material_effects": ["Aucune action", "Trajectoire d'épargne"],
    }
    db_session.add(
        Advice(
            month_id=month.id,
            advice_text=json.dumps(
                {
                    "outputs": [current_question],
                    "clarification_trace": {
                        "questions_consumed": 3,
                        "questions": [
                            {
                                "question_number": 1,
                                "fact_type": "period_coverage",
                                "decision_lever": "action_or_priority",
                                "outcome": "skipped",
                            },
                            {
                                "question_number": 2,
                                "fact_type": "recurring_obligation",
                                "decision_lever": "action_or_priority",
                                "outcome": "answered",
                            },
                            {
                                "question_number": 3,
                                "fact_type": "liquid_reserve",
                                "decision_lever": "action_or_priority",
                                "outcome": "pending",
                            },
                        ],
                        "stop_reason": "question_pending",
                    },
                }
            ),
        )
    )
    db_session.commit()
    db_session.expunge_all()
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                **current_question,
                "question": "Quel plancher de sécurité souhaitez-vous protéger ?",
                "fact_type": "safety_floor",
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 7,
            "emergency_fund_fact": {
                "fact_type": "liquid_reserve",
                "amount": 2_000,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["advice"]["outputs"][0]["type"] == "unresolved"
    assert mock_generator.generate_advice.call_args.args[2].clarifications_remaining == 0
