"""Integration tests for declared income context."""

from datetime import date, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.income_fact import IncomeFact
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.advice.models import AdviceContext


def _create_month(db: Session, year: int, month: int) -> Month:
    """Create canonical observed month."""
    record = Month(
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
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_income_facts_keep_fields_and_expire_at_their_own_cutoffs(
    client: TestClient,
    db_session: Session,
) -> None:
    """Income facts stay visible but inactive after 90 days or expected date."""
    expected_date = date.today() + timedelta(days=10)
    usual = client.put(
        "/api/advice/context/income",
        json={
            "fact_type": "usual_disposable_income",
            "amount": 3_200,
            "frequency": "monthly",
        },
    )
    one_off = client.put(
        "/api/advice/context/income",
        json={
            "fact_type": "expected_one_off_income",
            "amount": 1_500,
            "expected_date": expected_date.isoformat(),
        },
    )

    assert usual.status_code == 200
    assert one_off.status_code == 200
    usual_fact = usual.json()["fact"]
    one_off_fact = one_off.json()["fact"]
    assert datetime.fromisoformat(usual_fact["valid_until"]) - datetime.fromisoformat(
        usual_fact["last_confirmed_at"]
    ) == timedelta(days=90)
    assert one_off_fact["valid_until"].startswith(expected_date.isoformat())

    stored_usual = db_session.get(IncomeFact, "usual_disposable_income")
    stored_one_off = db_session.get(IncomeFact, "expected_one_off_income")
    assert stored_usual is not None
    assert stored_one_off is not None
    stored_usual.valid_until = utc_now().replace(tzinfo=None) - timedelta(seconds=1)
    stored_one_off.valid_until = utc_now().replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()

    facts = client.get("/api/advice/context/income").json()["facts"]

    assert {fact["fact_type"]: fact["state"] for fact in facts} == {
        "usual_disposable_income": "to_confirm",
        "expected_one_off_income": "to_confirm",
    }
    assert {fact["fact_type"]: fact["amount"] for fact in facts} == {
        "usual_disposable_income": 3_200,
        "expected_one_off_income": 1_500,
    }


@patch("app.api.deps.AdviceGenerator")
def test_usual_income_changes_sustainable_amount_and_trace(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Habitual income changes decision amount and remains auditable."""
    today = date.today()
    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    _create_month(db_session, today.year, today.month)

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        income = context.income_facts[0]
        amount = income.amount - 1_800 - 500
        return {
            "outputs": [
                {
                    "type": "recommendation",
                    "income_dependent": True,
                    "priority": "medium",
                    "action": "Affecter la capacité soutenable à la priorité.",
                    "amount": amount,
                    "trace": {
                        "summary": "Le revenu habituel borne le montant.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "2 300 € de dépenses sont observées.",
                                    "period": f"{today.year}-{today.month:02d}",
                                    "scope": "Dépenses essentielles et discrétionnaires",
                                    "source": "observed_data",
                                }
                            ],
                            "calculations": [f"{income.amount:g} € mensuels - 1 800 € - 500 € = {amount:g} €."],
                            "conventions": ["Fréquence mensuelle, revenu disponible."],
                            "income_normalizations": [
                                {
                                    "fact_type": "usual_disposable_income",
                                    "source_amount": income.amount,
                                    "source_frequency": income.frequency,
                                    "period": f"{today.year}-{today.month:02d}",
                                    "conversion": "monthly",
                                    "normalized_amount": income.amount,
                                }
                            ],
                            "declared_facts": [
                                {
                                    **income.model_dump(mode="json"),
                                    "can_correct": True,
                                    "can_delete": True,
                                }
                            ],
                        },
                    },
                }
            ]
        }

    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = mock_generator

    first = client.post(
        "/api/advice/generate",
        json={
            "year": today.year,
            "month": today.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )
    corrected = client.post(
        "/api/advice/generate",
        json={
            "year": today.year,
            "month": today.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_600,
                "frequency": "monthly",
            },
        },
    )

    assert first.status_code == 200
    assert corrected.status_code == 200
    assert first.json()["advice"]["outputs"][0]["amount"] == 700
    corrected_output = corrected.json()["advice"]["outputs"][0]
    assert corrected_output["amount"] == 1_300
    assert corrected_output["trace"]["details"]["declared_facts"][0]["frequency"] == "monthly"
    assert "3600 € mensuels" in corrected_output["trace"]["details"]["calculations"][0]
    stored_income = db_session.get(IncomeFact, "usual_disposable_income")
    assert stored_income is not None
    stored_income.valid_until = utc_now().replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()
    expired = client.get(f"/api/advice/{today.year}/{today.month}")
    assert expired.status_code == 200
    assert expired.json()["exists"] is False


@patch("app.api.deps.AdviceGenerator")
def test_expected_income_is_matched_to_observed_transaction_once(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Exact dated observed entry marks expected income as already observed."""
    today = date.today()
    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    current = _create_month(db_session, today.year, today.month)
    db_session.add_all(
        [
            Transaction(
                month_id=current.id,
                date=today,
                description="Prime exceptionnelle A",
                amount=1_500,
                money_map_type="INCOME",
            ),
            Transaction(
                month_id=current.id,
                date=today,
                description="Prime exceptionnelle B",
                amount=1_500,
                money_map_type="INCOME",
            ),
        ]
    )
    db_session.commit()
    mock_generator = MagicMock()

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        income = context.income_facts[0]
        return {
            "outputs": [
                {
                    "type": "no_action",
                    "priority": "low",
                    "conclusion": "L'entrée attendue est déjà observée.",
                    "trace": {
                        "summary": "La prime compte une seule fois.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "La prime déclarée correspond à une opération observée.",
                                    "period": today.isoformat(),
                                    "scope": "Revenus observés",
                                    "source": "observed_data",
                                }
                            ],
                            "calculations": ["1 500 € déclarés = 1 500 € observés ; contribution totale 1 500 €."],
                            "conventions": ["Correspondance exacte par montant et date."],
                            "income_normalizations": [
                                {
                                    "fact_type": "expected_one_off_income",
                                    "source_amount": income.amount,
                                    "source_frequency": None,
                                    "period": today.isoformat(),
                                    "conversion": "one_off",
                                    "normalized_amount": income.amount,
                                }
                            ],
                            "declared_facts": [
                                {
                                    **income.model_dump(mode="json"),
                                    "can_correct": True,
                                    "can_delete": True,
                                }
                            ],
                        },
                    },
                }
            ]
        }

    mock_generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": today.year,
            "month": today.month,
            "income_fact": {
                "fact_type": "expected_one_off_income",
                "amount": 1_500,
                "expected_date": today.isoformat(),
            },
        },
    )

    assert response.status_code == 200
    context = mock_generator.generate_advice.call_args.args[2]
    assert context.income_facts[0].matched_transaction is True
    current_data = mock_generator.generate_advice.call_args.args[0]
    assert current_data.total_income == 1_500
    assert current_data.core_percentage == 120
    assert current_data.choice_percentage == 33.3
    assert current_data.compound_percentage == -53.3
    assert current_data.score == 0
    assert current_data.score_label == "Poor"
    assert current_data.transactions is not None
    assert [transaction.description for transaction in current_data.transactions["INCOME"]] == [
        "Prime exceptionnelle B"
    ]
    assert (
        response.json()["advice"]["outputs"][0]["trace"]["details"]["declared_facts"][0]["matched_transaction"] is True
    )


@patch("app.api.deps.AdviceGenerator")
def test_expired_session_expected_income_is_inactive(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Past session-only expected income cannot influence advice."""
    today = date.today()
    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    _create_month(db_session, today.year, today.month)
    mock_generator = MagicMock()

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        assert context.income_facts[0].state == "to_confirm"
        return {
            "outputs": [
                {
                    "type": "no_action",
                    "priority": "low",
                    "conclusion": "L'entrée expirée est ignorée.",
                    "trace": {
                        "summary": "Aucune entrée active.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "La date attendue est passée.",
                                    "period": (today - timedelta(days=1)).isoformat(),
                                    "scope": "Entrée exceptionnelle",
                                    "source": "observed_data",
                                }
                            ]
                        },
                    },
                }
            ]
        }

    mock_generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": today.year,
            "month": today.month,
            "remember_fact": False,
            "income_fact": {
                "fact_type": "expected_one_off_income",
                "amount": 1_500,
                "expected_date": (today - timedelta(days=1)).isoformat(),
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["advice"]["outputs"][0]["type"] == "no_action"


@patch("app.api.deps.AdviceGenerator")
def test_session_correction_and_deletion_recalculate_income_dependent_output(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Each income lifecycle mutation recalculates dependent advice."""
    today = date.today()

    previous = date(today.year - (today.month == 1), today.month - 1 or 12, 1)
    _create_month(db_session, previous.year, previous.month)
    _create_month(db_session, today.year, today.month)
    client.put(
        "/api/advice/context/income",
        json={
            "fact_type": "usual_disposable_income",
            "amount": 3_000,
            "frequency": "monthly",
        },
    )

    def generated_advice(*args: object) -> dict[str, object]:
        context = cast(AdviceContext, args[2])
        active = next((fact for fact in context.income_facts if fact.state != "to_confirm"), None)
        if active is None:
            return {
                "outputs": [
                    {
                        "type": "clarification",
                        "priority": "medium",
                        "subject": "Montant soutenable",
                        "observation": "Les dépenses mensuelles sont connues.",
                        "possible_effect": "Le revenu change le montant soutenable.",
                        "question": "Quel est votre revenu disponible habituel ?",
                        "fact_type": "usual_disposable_income",
                        "material_effects": ["Conseiller un montant dérivé.", "Ne conseiller aucun montant."],
                    }
                ]
            }
        amount = active.amount - 2_300
        return {
            "outputs": [
                {
                    "type": "recommendation",
                    "income_dependent": True,
                    "priority": "medium",
                    "action": "Affecter la capacité calculée.",
                    "amount": amount,
                    "trace": {
                        "summary": "Le revenu actif borne la capacité.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "2 300 € de dépenses sont observées.",
                                    "period": f"{today.year}-{today.month:02d}",
                                    "scope": "Dépenses du mois",
                                    "source": "observed_data",
                                }
                            ],
                            "calculations": [f"{active.amount:g} € - 2 300 € = {amount:g} €."],
                            "conventions": ["Revenu disponible mensuel."],
                            "income_normalizations": [
                                {
                                    "fact_type": "usual_disposable_income",
                                    "source_amount": active.amount,
                                    "source_frequency": active.frequency,
                                    "period": f"{today.year}-{today.month:02d}",
                                    "conversion": "monthly",
                                    "normalized_amount": active.amount,
                                }
                            ],
                            "declared_facts": [
                                {
                                    **active.model_dump(mode="json"),
                                    "can_correct": True,
                                    "can_delete": True,
                                }
                            ],
                        },
                    },
                }
            ]
        }

    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = generated_advice
    mock_generator_class.return_value = mock_generator

    session = client.post(
        "/api/advice/generate",
        json={
            "year": today.year,
            "month": today.month,
            "remember_fact": False,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_500,
                "frequency": "monthly",
            },
        },
    )
    stored_after_session = client.get("/api/advice/context/income").json()["facts"][0]
    corrected = client.put(
        "/api/advice/context/income",
        json={
            "fact_type": "usual_disposable_income",
            "amount": 3_600,
            "frequency": "monthly",
        },
    )
    regenerated = client.post(
        "/api/advice/generate",
        json={"year": today.year, "month": today.month},
    )
    deleted = client.delete("/api/advice/context/income/usual_disposable_income")
    after_delete = client.post(
        "/api/advice/generate",
        json={"year": today.year, "month": today.month},
    )

    assert session.status_code == 200
    assert session.json()["advice"]["outputs"][0]["amount"] == 1_200
    assert stored_after_session["amount"] == 3_000
    assert stored_after_session["state"] == "to_confirm"
    assert corrected.json()["fact"]["state"] == "corrected"
    assert regenerated.json()["advice"]["outputs"][0]["amount"] == 1_300
    assert deleted.status_code == 204
    assert after_delete.json()["advice"]["outputs"][0]["type"] == "clarification"
