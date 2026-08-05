"""Integration tests for declared decision constraints."""

from datetime import date, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.constraint_fact import ConstraintFact
from app.db.models.month import Month
from app.services.advice.models import AdviceContext, FinancialLimitContext


def _create_month(db: Session, year: int, month: int) -> None:
    """Create eligible observed month."""
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


def test_financial_limit_is_user_controlled_for_ninety_days(
    client: TestClient,
    db_session: Session,
) -> None:
    """Financial limit stays scoped, fresh, correctable, and deletable."""
    created = client.post(
        "/api/advice/context/constraints",
        json={
            "fact_type": "financial_limit",
            "scope_type": "expense",
            "scope": "Budget transports",
            "limit_type": "sustainable_amount",
            "amount": 120,
        },
    )

    assert created.status_code == 200
    fact = created.json()["fact"]
    assert fact["state"] == "active"
    assert fact["scope"] == "Budget transports"
    assert datetime.fromisoformat(fact["valid_until"]) - datetime.fromisoformat(
        fact["last_confirmed_at"]
    ) == timedelta(days=90)

    listed = client.get("/api/advice/context/constraints")
    assert listed.status_code == 200
    assert listed.json()["facts"] == [fact]

    corrected = client.put(
        f"/api/advice/context/constraints/{fact['fact_id']}",
        json={
            "fact_type": "financial_limit",
            "scope_type": "expense",
            "scope": "Budget transports",
            "limit_type": "sustainable_amount",
            "amount": 90,
        },
    )
    assert corrected.status_code == 200
    assert corrected.json()["fact"]["state"] == "corrected"
    assert corrected.json()["fact"]["amount"] == 90
    stored = db_session.get(ConstraintFact, fact["fact_id"])
    assert stored is not None
    stored.valid_until = utc_now().replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()
    expired = client.get("/api/advice/context/constraints").json()["facts"][0]
    assert expired["state"] == "to_confirm"

    deleted = client.delete(f"/api/advice/context/constraints/{fact['fact_id']}")
    assert deleted.status_code == 204
    assert client.get("/api/advice/context/constraints").json() == {"facts": []}


@pytest.mark.normative_scenarios("V-CHOICE")
@patch("app.api.deps.AdviceGenerator")
def test_observed_behavior_never_contests_choices_or_constraints(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Observed spending leaves declared floor and constraints active."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    client.put(
        "/api/advice/context/emergency-fund/safety_floor",
        json={"amount": 5_400},
    )
    client.post(
        "/api/advice/context/constraints",
        json={
            "fact_type": "financial_limit",
            "scope_type": "expense",
            "scope": "Logement",
            "limit_type": "floor",
            "amount": 1_000,
        },
    )
    client.post(
        "/api/advice/context/constraints",
        json={
            "fact_type": "action_unavailability",
            "action": "Déménager",
            "review_date": (date.today() + timedelta(days=30)).isoformat(),
        },
    )
    mock_generator = MagicMock()

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        assert [(fact.fact_type, fact.state) for fact in context.emergency_fund_facts] == [
            ("safety_floor", "active")
        ]
        assert {fact.fact_type: fact.state for fact in context.constraint_facts} == {
            "financial_limit": "active",
            "action_unavailability": "active",
        }
        return {
            "outputs": [
                {
                    "type": "no_action",
                    "priority": "low",
                    "conclusion": "Le comportement observé ne modifie aucun choix déclaré.",
                    "trace": {
                        "summary": "Les choix déclarés restent présumés vrais.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "Les dépenses observées diffèrent des choix déclarés.",
                                    "period": "2025-09 à 2025-10",
                                    "scope": "Dépenses du foyer",
                                    "source": "observed_data",
                                    "evidence_type": "presence",
                                    "source_months": ["2025-09", "2025-10"],
                                    "transaction_ids": [],
                                }
                            ],
                        },
                    },
                }
            ]
        }

    mock_generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 200
    assert [output["type"] for output in response.json()["advice"]["outputs"]] == ["no_action"]
    assert {fact["state"] for fact in client.get("/api/advice/context/emergency-fund").json()["facts"]} == {
        "active"
    }
    assert {fact["state"] for fact in client.get("/api/advice/context/constraints").json()["facts"]} == {
        "active"
    }


def test_unavailability_expires_on_its_review_date(client: TestClient) -> None:
    """Review date makes unavailable action immediately inactive."""
    response = client.post(
        "/api/advice/context/constraints",
        json={
            "fact_type": "action_unavailability",
            "action": "Renégocier le loyer",
            "review_date": date.today().isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json()["fact"]["state"] == "to_confirm"


@patch("app.api.deps.AdviceGenerator")
def test_financial_limit_caps_generated_amount_and_is_traced(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Declared sustainable amount caps generated advice."""
    today = date.today()
    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    _create_month(db_session, today.year, today.month)

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        limit = context.constraint_facts[0]
        assert isinstance(limit, FinancialLimitContext)
        return {
            "outputs": [
                {
                    "type": "recommendation",
                    "priority": "medium",
                    "subject": "Budget transports",
                    "action": "Limiter le budget transports au montant soutenable.",
                    "income_dependent": False,
                    "amount": limit.amount,
                    "trace": {
                        "summary": "La limite déclarée borne le budget transports.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "Les dépenses de transport sont observées.",
                                    "period": f"{today.year}-{today.month:02d}",
                                    "scope": "Budget transports",
                                    "source": "observed_data",
                                    "evidence_type": "presence",
                                    "source_months": ["2025-01"],
                                    "transaction_ids": [],
                                }
                            ],
                            "calculations": ["300 € observés, plafonnés à 90 € déclarés."],
                            "declared_facts": [
                                {
                                    **limit.model_dump(mode="json"),
                                    "can_correct": True,
                                    "can_delete": True,
                                }
                            ],
                        },
                    },
                }
            ]
        }

    generator = MagicMock()
    generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": today.year,
            "month": today.month,
            "constraint_fact": {
                "fact_type": "financial_limit",
                "scope_type": "expense",
                "scope": "Budget transports",
                "limit_type": "sustainable_amount",
                "amount": 90,
            },
        },
    )

    assert response.status_code == 200
    output = response.json()["advice"]["outputs"][0]
    assert output["amount"] == 90
    assert output["trace"]["details"]["declared_facts"][0]["scope"] == "Budget transports"


@patch("app.api.deps.AdviceGenerator")
def test_generator_cannot_exceed_declared_limit(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Over-limit generated amount is rejected."""
    today = date.today()
    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    _create_month(db_session, today.year, today.month)
    client.post(
        "/api/advice/context/constraints",
        json={
            "fact_type": "financial_limit",
            "scope_type": "action",
            "scope": "Épargne mensuelle",
            "limit_type": "cap",
            "amount": 90,
        },
    )

    def generated_advice(*args: object) -> dict[str, object]:
        return {
            "outputs": [
                {
                    "type": "recommendation",
                    "subject": "Épargne mensuelle",
                    "priority": "medium",
                    "action": "Épargner 120 €.",
                    "income_dependent": False,
                    "amount": 120,
                    "trace": {
                        "summary": "Montant conseillé.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "Une capacité est observée.",
                                    "period": f"{today.year}-{today.month:02d}",
                                    "scope": "Épargne mensuelle",
                                    "source": "observed_data",
                                    "evidence_type": "presence",
                                    "source_months": ["2025-01"],
                                    "transaction_ids": [],
                                }
                            ],
                            "calculations": ["120 € calculés."],
                            "declared_facts": [],
                        },
                    },
                }
            ]
        }

    generator = MagicMock()
    generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = generator

    response = client.post(
        "/api/advice/generate",
        json={"year": today.year, "month": today.month},
    )

    assert response.status_code == 503


@patch("app.api.deps.AdviceGenerator")
def test_unavailable_action_yields_traced_unresolved_subject_until_review(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Unavailable action stays inactive and blocks guessed alternatives."""
    today = date.today()
    review_date = today + timedelta(days=10)
    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    _create_month(db_session, today.year, today.month)
    created = client.post(
        "/api/advice/context/constraints",
        json={
            "fact_type": "action_unavailability",
            "action": "Renégocier le loyer",
            "review_date": review_date.isoformat(),
        },
    ).json()["fact"]
    assert created["valid_until"] == f"{review_date.isoformat()}T00:00:00"

    def generated_advice(*args: object) -> dict[str, object]:
        unavailable = cast(AdviceContext, args[2]).constraint_facts[0]
        trace = {
            "summary": "L'action déclarée est indisponible.",
            "details": {
                "observations": [
                    {
                        "fact": "Le logement dépasse le repère générique.",
                        "period": f"{today.year}-{today.month:02d}",
                        "scope": "Logement",
                        "source": "observed_data",
                        "evidence_type": "presence",
                        "source_months": ["2025-01"],
                        "transaction_ids": [],
                    }
                ],
                "declared_facts": [
                    {
                        **unavailable.model_dump(mode="json"),
                        "can_correct": True,
                        "can_delete": True,
                    }
                ],
            },
        }
        if generator.generate_advice.call_count > 2:
            return {
                "outputs": [
                    {
                        "type": "recommendation",
                        "priority": "medium",
                        "subject": "Logement",
                        "action": "Renégocier le loyer",
                        "income_dependent": False,
                        "trace": {
                            "summary": "Action proposée sans sa contrainte.",
                            "details": {
                                "observations": [
                                    {
                                        "fact": "Le logement dépasse le repère générique.",
                                        "period": f"{today.year}-{today.month:02d}",
                                        "scope": "Logement",
                                        "source": "observed_data",
                                        "evidence_type": "presence",
                                        "source_months": ["2025-01"],
                                        "transaction_ids": [],
                                    }
                                ],
                            },
                        },
                    }
                ]
            }
        if generator.generate_advice.call_count > 1:
            return {
                "outputs": [
                    {
                        "type": "recommendation",
                        "priority": "medium",
                        "action": "Déménager à la place.",
                        "income_dependent": False,
                        "trace": trace,
                    }
                ]
            }
        return {
            "outputs": [
                {
                    "type": "unresolved",
                    "priority": "medium",
                    "conclusion": "Aucune action faisable n'est étayée avant le réexamen.",
                    "trace": trace,
                }
            ]
        }

    generator = MagicMock()
    generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = generator

    response = client.post(
        "/api/advice/generate",
        json={"year": today.year, "month": today.month},
    )

    assert response.status_code == 200
    output = response.json()["advice"]["outputs"][0]
    assert output["type"] == "unresolved"
    assert output["trace"]["details"]["declared_facts"][0]["action"] == "Renégocier le loyer"
    rejected_alternative = client.post(
        "/api/advice/generate",
        json={"year": today.year, "month": today.month, "regenerate": True},
    )
    assert rejected_alternative.status_code == 503
    untraced_unavailable_action = client.post(
        "/api/advice/generate",
        json={"year": today.year, "month": today.month, "regenerate": True},
    )
    assert untraced_unavailable_action.status_code == 503

    stored = db_session.get(ConstraintFact, created["fact_id"])
    assert stored is not None
    stored.valid_until = utc_now().replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()
    expired = client.get("/api/advice/context/constraints").json()["facts"][0]
    assert expired["state"] == "to_confirm"
