"""Integration tests for obligations and debt context."""

from datetime import date, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.base import utc_now
from app.db.models.commitment_fact import CommitmentFact
from app.db.models.month import Month
from app.services.advice.models import AdviceContext


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


def test_commitments_keep_their_fields_and_validity_cycles(client: TestClient) -> None:
    """Obligations and debt facts preserve values and nearest expiry."""
    today = date.today()
    recurring_end = today + timedelta(days=10)
    due_date = today + timedelta(days=120)
    payloads = [
        {
            "fact_type": "recurring_obligation",
            "label": "Pension alimentaire",
            "amount": 300,
            "frequency": "monthly",
            "end_date": recurring_end.isoformat(),
        },
        {
            "fact_type": "one_off_obligation",
            "label": "Impôts",
            "amount": 450,
            "due_date": due_date.isoformat(),
        },
        {
            "fact_type": "debt_position",
            "label": "Prêt auto",
            "balance": 8_000,
            "overdue_amount": 0,
        },
        {
            "fact_type": "debt_terms",
            "label": "Prêt auto",
            "minimum_payment": 250,
            "annual_rate": 4.2,
            "cost": None,
            "end_date": None,
        },
    ]

    created = [client.post("/api/advice/context/commitments", json=payload).json()["fact"] for payload in payloads]

    assert [fact["fact_type"] for fact in created] == [payload["fact_type"] for payload in payloads]
    assert created[0]["valid_until"].startswith(recurring_end.isoformat())
    assert created[1]["valid_until"].startswith(due_date.isoformat())
    position_lifetime = datetime.fromisoformat(created[2]["valid_until"]) - datetime.fromisoformat(
        created[2]["last_confirmed_at"]
    )
    terms_lifetime = datetime.fromisoformat(created[3]["valid_until"]) - datetime.fromisoformat(
        created[3]["last_confirmed_at"]
    )
    assert position_lifetime == timedelta(days=30)
    assert terms_lifetime == timedelta(days=90)
    assert client.get("/api/advice/context/commitments").json()["facts"] == created


@patch("app.api.deps.AdviceGenerator")
def test_feasible_debt_minimum_stays_prioritized_when_savings_need_clarification(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Known feasible minimum remains actionable beside unresolved savings."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    recurring = client.post(
        "/api/advice/context/commitments",
        json={
            "fact_type": "recurring_obligation",
            "label": "Pension alimentaire",
            "amount": 300,
            "frequency": "monthly",
            "end_date": None,
        },
    ).json()["fact"]
    terms = client.post(
        "/api/advice/context/commitments",
        json={
            "fact_type": "debt_terms",
            "label": "Prêt auto",
            "minimum_payment": 250,
            "annual_rate": 4.2,
            "cost": None,
            "end_date": None,
        },
    ).json()["fact"]
    recurring_citation = {
        **recurring,
        "state": "active",
        "can_correct": True,
        "can_delete": True,
    }
    citation = {
        **terms,
        "state": "active",
        "can_correct": True,
        "can_delete": True,
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "recommendation",
                "priority": "high",
                "action": "Payer le minimum exigible du prêt auto.",
                "amount": 250,
                "deadline": "2025-07-31",
                "trace": {
                    "summary": "Le paiement minimum connu prime sur l'épargne.",
                    "details": {
                        "observations": [
                            {
                                "fact": "La capacité observée couvre le minimum.",
                                "period": "2025-07",
                                "scope": "Transactions du mois",
                                "source": "observed_data",
                            }
                        ],
                        "calculations": ["3 000 € - 1 800 € - 500 € - 300 € = 400 €, donc 250 € est faisable."],
                        "conventions": ["Une obligation dure prime sur l'épargne."],
                        "limits": [],
                        "declared_facts": [recurring_citation, citation],
                    },
                },
            },
            {
                "type": "clarification",
                "priority": "medium",
                "subject": "Trajectoire d'épargne",
                "observation": "150 € restent après obligations et minimum.",
                "possible_effect": "Le plancher de sécurité peut changer l'affectation.",
                "question": "Quel plancher de sécurité souhaitez-vous protéger ?",
                "fact_type": "safety_floor",
                "material_effects": ["Épargner 150 €.", "Ne pas augmenter l'épargne."],
            },
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 7})

    assert response.status_code == 200
    outputs = response.json()["advice"]["outputs"]
    assert outputs[0]["priority"] == "high"
    assert outputs[0]["amount"] == 250
    assert outputs[0]["trace"]["details"]["declared_facts"][0]["amount"] == 300
    assert "300 € = 400 €" in outputs[0]["trace"]["details"]["calculations"][0]
    assert outputs[1]["type"] == "clarification"
    context = mock_generator.generate_advice.call_args.args[2]
    assert [fact.fact_type for fact in context.commitment_facts] == [
        recurring["fact_type"],
        terms["fact_type"],
    ]


@patch("app.api.deps.AdviceGenerator")
def test_session_commitment_replaces_stored_value_for_current_generation(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Session correction replaces, but does not overwrite, the stored fact."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    payload = {
        "fact_type": "debt_terms",
        "label": "Prêt auto",
        "minimum_payment": 250,
        "annual_rate": 4.2,
        "cost": None,
        "end_date": None,
    }
    client.post("/api/advice/context/commitments", json=payload)

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        fact = context.commitment_facts[0]
        citation = {
            **fact.model_dump(mode="json"),
            "can_correct": True,
            "can_delete": True,
        }
        return {
            "outputs": [
                {
                    "type": "recommendation",
                    "priority": "high",
                    "action": "Payer le minimum corrigé.",
                    "amount": fact.minimum_payment,
                    "deadline": "2025-07-31",
                    "trace": {
                        "summary": "La valeur de session remplace la valeur mémorisée.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "Le minimum corrigé est faisable.",
                                    "period": "2025-07",
                                    "scope": "Dette déclarée",
                                    "source": "observed_data",
                                }
                            ],
                            "calculations": ["275 € de capacité - 275 € de minimum = 0 €."],
                            "declared_facts": [citation],
                        },
                    },
                }
            ]
        }

    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 7,
            "remember_fact": False,
            "commitment_fact": {**payload, "minimum_payment": 275},
        },
    )

    assert response.status_code == 200
    context = mock_generator.generate_advice.call_args.args[2]
    assert [(fact.minimum_payment, fact.state) for fact in context.commitment_facts] == [(275, "session")]
    stored = client.get("/api/advice/context/commitments").json()["facts"]
    assert [(fact["minimum_payment"], fact["state"]) for fact in stored] == [(250, "to_confirm")]


def test_correction_and_deletion_invalidate_only_dependent_advice(
    client: TestClient,
    db_session: Session,
) -> None:
    """Fact mutation removes dependent outputs and preserves unrelated advice."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    payload = {
        "fact_type": "recurring_obligation",
        "label": "Pension alimentaire",
        "amount": 300,
        "frequency": "monthly",
        "end_date": None,
    }
    fact = client.post("/api/advice/context/commitments", json=payload).json()["fact"]
    months = db_session.query(Month).order_by(Month.month).all()
    dependent_json = f'{{"outputs":[{{"fact_id":{fact["fact_id"]}}}]}}'
    db_session.add_all(
        [
            Advice(month_id=months[0].id, advice_text=dependent_json),
            Advice(month_id=months[1].id, advice_text='{"outputs":[]}'),
        ]
    )
    db_session.commit()

    corrected = client.put(
        f"/api/advice/context/commitments/{fact['fact_id']}",
        json={**payload, "amount": 350},
    )

    assert corrected.status_code == 200
    assert corrected.json()["fact"]["amount"] == 350
    assert corrected.json()["fact"]["state"] == "corrected"
    assert [advice.month_id for advice in db_session.query(Advice).all()] == [months[1].id]

    db_session.add(Advice(month_id=months[0].id, advice_text=dependent_json))
    db_session.commit()
    deleted = client.delete(f"/api/advice/context/commitments/{fact['fact_id']}")

    assert deleted.status_code == 204
    assert client.get("/api/advice/context/commitments").json() == {"facts": []}
    assert [advice.month_id for advice in db_session.query(Advice).all()] == [months[1].id]


def test_dated_and_volatile_facts_expire_without_disappearing(
    client: TestClient,
    db_session: Session,
) -> None:
    """Dated obligation and 30/90-day debt facts become inactive."""
    yesterday = date.today() - timedelta(days=1)
    payloads = [
        {
            "fact_type": "one_off_obligation",
            "label": "Impôts",
            "amount": 450,
            "due_date": yesterday.isoformat(),
        },
        {
            "fact_type": "debt_position",
            "label": "Prêt auto",
            "balance": 8_000,
            "overdue_amount": 100,
        },
        {
            "fact_type": "debt_terms",
            "label": "Prêt auto",
            "minimum_payment": 250,
            "annual_rate": 4.2,
            "cost": None,
            "end_date": None,
        },
    ]
    created = [client.post("/api/advice/context/commitments", json=payload).json()["fact"] for payload in payloads]
    for created_fact in created[1:]:
        fact = db_session.get(CommitmentFact, created_fact["fact_id"])
        assert fact is not None
        fact.valid_until = utc_now().replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()

    facts = client.get("/api/advice/context/commitments").json()["facts"]

    assert {fact["fact_type"]: fact["state"] for fact in facts} == {
        "one_off_obligation": "to_confirm",
        "debt_position": "to_confirm",
        "debt_terms": "to_confirm",
    }
    assert {fact["fact_type"] for fact in facts} == {
        "one_off_obligation",
        "debt_position",
        "debt_terms",
    }


@patch("app.api.deps.AdviceGenerator")
def test_transactions_alone_never_create_debt_or_obligation_facts(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Observed flows leave debt contracts and obligations undeclared."""
    _create_month(db_session, 2025, 6)
    _create_month(db_session, 2025, 7)
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Paiement de dette",
                "observation": "Une capacité mensuelle est observée.",
                "possible_effect": "Un minimum exigible changerait la priorité.",
                "question": "Quel est le paiement minimum exigible ?",
                "fact_type": "debt_terms",
                "material_effects": ["Payer le minimum.", "Ne pas conclure de paiement."],
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 7})

    assert response.status_code == 200
    assert mock_generator.generate_advice.call_args.args[2].commitment_facts == []
    assert client.get("/api/advice/context/commitments").json() == {"facts": []}
