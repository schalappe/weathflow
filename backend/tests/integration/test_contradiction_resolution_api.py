"""Integration tests for material contradiction resolution."""

from datetime import date
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.commitment_fact import CommitmentFact
from app.db.models.income_fact import IncomeFact
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.observation_fact import ObservationFactRepository
from app.services.advice.models import AdviceContext, MonthData, TransactionSample
from app.services.advice.service import _select_adverse_series


def _add_income_month(db: Session, year: int, month: int, amount: float) -> Month:
    """Add complete observed monthly income cycle."""
    record = Month(
        year=year,
        month=month,
        total_income=amount,
        total_core=1_800,
        total_choice=500,
        total_compound=max(0, amount - 2_300),
        core_percentage=1_800 / amount * 100,
        choice_percentage=500 / amount * 100,
        compound_percentage=max(0, amount - 2_300) / amount * 100,
        score=1,
        score_label="Need Improvement",
    )
    record.transactions.append(
        Transaction(
            date=date(year, month, 5),
            description="Salaire",
            amount=amount,
            account="Compte courant",
            money_map_type=MoneyMapType.INCOME.value,
            money_map_subcategory="Salaire",
        )
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _income_dependent_advice(*args: object) -> dict[str, object]:
    """Return independent and income-dependent outputs."""
    context = cast(AdviceContext, args[2])
    income = context.income_facts[0]
    month = cast(MonthData, args[0])
    period = f"{month.year}-{month.month:02d}"
    factors = {"weekly": 52 / 12, "biweekly": 26 / 12, "monthly": 1, "quarterly": 1 / 3, "yearly": 1 / 12}
    conversions = {
        "weekly": "weekly_x_52_div_12",
        "biweekly": "biweekly_x_26_div_12",
        "monthly": "monthly",
        "quarterly": "quarterly_div_3",
        "yearly": "yearly_div_12",
    }
    if income.fact_type == "expected_one_off_income":
        assert income.expected_date is not None
        factor: float = 1.0
        conversion = "one_off"
        decision_amount = income.amount
        normalization_period = income.expected_date.isoformat()
    else:
        frequency = income.frequency or "monthly"
        factor = factors[frequency]
        conversion = conversions[frequency]
        normalization_period = period
        decision_amount = max(0, income.amount * factor - 2_300)
    observation = {
        "fact": "Les dépenses essentielles atteignent 1 800 €.",
        "period": period,
        "scope": "Dépenses essentielles",
        "source": "observed_data",
        "evidence_type": "aggregate",
        "source_months": [period],
        "transaction_ids": [],
    }
    return {
        "outputs": [
            {
                "type": "no_action",
                "priority": "low",
                "conclusion": "Les dépenses essentielles restent stables.",
                "trace": {
                    "summary": "Aucun changement indépendant du revenu.",
                    "details": {"observations": [observation]},
                },
            },
            {
                "type": "recommendation",
                "priority": "high",
                "subject": "Montant soutenable",
                "action": "Affecter le montant soutenable à la priorité.",
                "income_dependent": True,
                "amount": decision_amount,
                "trace": {
                    "summary": "Le revenu déclaré borne le montant.",
                    "details": {
                        "observations": [observation],
                        "calculations": ["Le revenu normalisé borne le montant."],
                        "conventions": ["Conversion vers une fréquence mensuelle."],
                        "income_normalizations": [
                            {
                                "fact_type": income.fact_type,
                                "source_amount": income.amount,
                                "source_frequency": income.frequency,
                                "period": normalization_period,
                                "conversion": conversion,
                                "normalized_amount": income.amount * factor,
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
            },
        ]
    }


def _two_income_dependent_outputs(*args: object) -> dict[str, object]:
    """Return two outputs that cite the same income fact."""
    advice = _income_dependent_advice(*args)
    outputs = cast(list[dict[str, object]], advice["outputs"])
    outputs.append(
        {
            **outputs[1],
            "subject": "Trajectoire de réserve",
            "action": "Affecter le même montant à la réserve.",
        }
    )
    return advice


def _add_obligation_month(db: Session, year: int, month: int, amount: float) -> Month:
    """Add matched recurring-obligation cycle."""
    record = Month(
        year=year,
        month=month,
        total_income=3_000,
        total_core=1_800 + amount,
        total_choice=500,
        total_compound=700,
        core_percentage=(1_800 + amount) / 3_000 * 100,
        choice_percentage=500 / 3_000 * 100,
        compound_percentage=700 / 3_000 * 100,
        score=1,
        score_label="Need Improvement",
    )
    record.transactions.append(
        Transaction(
            date=date(year, month, 8),
            description="Loyer",
            amount=amount,
            account="Compte courant",
            money_map_type=MoneyMapType.CORE.value,
            money_map_subcategory="Logement",
        )
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _obligation_dependent_advice(*args: object) -> dict[str, object]:
    """Return output citing obligation."""
    context = cast(AdviceContext, args[2])
    fact = context.commitment_facts[0]
    return {
        "outputs": [
            {
                "type": "recommendation",
                "priority": "high",
                "subject": "Paiement du loyer",
                "action": "Réserver le montant mensuel du loyer.",
                "income_dependent": False,
                "amount": fact.amount,
                "trace": {
                    "summary": "Le loyer déclaré prime.",
                    "details": {
                        "observations": [
                            {
                                "fact": "Le budget courant est observé.",
                                "period": "2025-09 à 2025-10",
                                "scope": "Budget courant",
                                "source": "observed_data",
                                "evidence_type": "presence",
                                "source_months": ["2025-09", "2025-10"],
                                "transaction_ids": [],
                            }
                        ],
                        "calculations": [f"Loyer déclaré : {fact.amount:g} €."],
                        "declared_facts": [
                            {
                                **fact.model_dump(mode="json"),
                                "can_correct": True,
                                "can_delete": True,
                            }
                        ],
                    },
                },
            }
        ]
    }


@patch("app.api.deps.AdviceGenerator")
def test_material_income_drop_blocks_only_dependent_output(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Two matched 23% lower cycles show conflict before dependent advice."""
    september = _add_income_month(db_session, 2025, 9, 2_300)
    october = _add_income_month(db_session, 2025, 10, 2_300)
    months = ["2025-09", "2025-10"]
    ObservationFactRepository(db_session).put_period_coverage(months, True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    outputs = response.json()["advice"]["outputs"]
    assert [output["type"] for output in outputs] == ["no_action", "clarification"]
    conflict = outputs[1]["contradiction"]
    assert conflict == {
        "declared_value": 3_000,
        "frequency": "monthly",
        "last_confirmed_at": conflict["last_confirmed_at"],
        "signal": "recurring_income_lower",
        "observed_value": 2_300,
        "period": months,
        "scope": "Revenu disponible habituel mensuel",
        "affected_subject": "Montant soutenable",
        "transaction_ids": [september.transactions[0].id, october.transactions[0].id],
        "observation_keys": conflict["observation_keys"],
        "acknowledged_observations": [],
        "resolution_options": ["confirm", "correct", "session", "unknown", "skip", "delete"],
    }
    assert len(conflict["observation_keys"]) == 2
    assert outputs[1]["material_effects"] == [
        "Conserver 3 000 € pour le montant soutenable.",
        "Recalculer le montant soutenable depuis 2 300 €.",
    ]


@patch("app.api.deps.AdviceGenerator")
def test_material_income_drop_blocks_every_dependent_output(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """One clarification replaces every output citing its contested fact."""
    _add_income_month(db_session, 2025, 9, 2_300)
    october = _add_income_month(db_session, 2025, 10, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _two_income_dependent_outputs
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    assert [output["type"] for output in response.json()["advice"]["outputs"]] == [
        "no_action",
        "clarification",
    ]


@patch("app.api.deps.AdviceGenerator")
def test_missing_expected_income_cycle_counts_as_frequency_drop(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Complete expected cycle without income contributes zero."""
    _add_income_month(db_session, 2025, 8, 3_000)
    september = _add_income_month(db_session, 2025, 9, 3_000)
    october = _add_income_month(db_session, 2025, 10, 1)
    db_session.delete(october.transactions[0])
    october.total_income = 0
    db_session.commit()
    ObservationFactRepository(db_session).put_period_coverage(["2025-08", "2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    conflict = response.json()["advice"]["outputs"][1]["contradiction"]
    assert conflict["signal"] == "recurring_income_lower"
    assert conflict["observed_value"] == 1_500
    assert conflict["period"] == ["2025-09", "2025-10"]
    assert conflict["transaction_ids"] == [september.transactions[0].id]
    assert len(conflict["observation_keys"]) == 2


@patch("app.api.deps.AdviceGenerator")
def test_recurring_income_aggregates_each_complete_cycle(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Split deposits aggregate before recurring-income comparison."""
    records = [_add_income_month(db_session, 2025, month, 1_150) for month in (9, 10)]
    for record in records:
        record.total_income = 2_300
        record.transactions.append(
            Transaction(
                date=date(record.year, record.month, 6),
                description="Salaire complément",
                amount=1_150,
                account="Compte courant",
                money_map_type=MoneyMapType.INCOME.value,
                money_map_subcategory="Salaire",
            )
        )
    db_session.commit()
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": records[-1].year,
            "month": records[-1].month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    contradiction = response.json()["advice"]["outputs"][1]["contradiction"]
    assert contradiction["observed_value"] == 2_300
    assert len(contradiction["transaction_ids"]) == 4


@patch("app.api.deps.AdviceGenerator")
def test_nonrecurring_income_does_not_mask_recurring_series(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Unpaired one-off income stays outside recurring cycle totals."""
    _add_income_month(db_session, 2025, 9, 2_300)
    october = _add_income_month(db_session, 2025, 10, 2_300)
    october.transactions.append(
        Transaction(
            date=date(2025, 10, 20),
            description="Cadeau",
            amount=5_000,
            account="Compte courant",
            money_map_type=MoneyMapType.INCOME.value,
            money_map_subcategory="Autre revenu",
        )
    )
    db_session.commit()
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    conflict = response.json()["advice"]["outputs"][1]["contradiction"]
    assert conflict["signal"] == "recurring_income_lower"
    assert conflict["observed_value"] == 2_300


@patch("app.api.deps.AdviceGenerator")
def test_favorable_income_requires_three_complete_cycles(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Two favorable cycles stay silent; third opens clarification."""
    _add_income_month(db_session, 2025, 8, 3_700)
    september = _add_income_month(db_session, 2025, 9, 3_700)
    ObservationFactRepository(db_session).put_period_coverage(["2025-08", "2025-09"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    two_cycles = client.post(
        "/api/advice/generate",
        json={
            "year": september.year,
            "month": september.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )
    october = _add_income_month(db_session, 2025, 10, 3_700)
    ObservationFactRepository(db_session).put_period_coverage(
        ["2025-08", "2025-09", "2025-10"],
        True,
        [],
    )
    three_cycles = client.post(
        "/api/advice/generate",
        json={"year": october.year, "month": october.month, "regenerate": True},
    )

    assert two_cycles.status_code == 200
    assert [item["type"] for item in two_cycles.json()["advice"]["outputs"]] == [
        "no_action",
        "recommendation",
    ]
    assert three_cycles.status_code == 200
    outputs = three_cycles.json()["advice"]["outputs"]
    assert [item["type"] for item in outputs] == ["no_action", "clarification"]
    assert outputs[1]["contradiction"]["signal"] == "recurring_income_higher"
    assert outputs[1]["contradiction"]["period"] == ["2025-08", "2025-09", "2025-10"]


@patch("app.api.deps.AdviceGenerator")
def test_weekly_income_uses_complete_consecutive_cycles(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Two complete weekly cycles can contest weekly income."""
    october = _add_income_month(db_session, 2026, 10, 550)
    october.transactions[0].date = date(2026, 10, 12)
    october.transactions.append(
        Transaction(
            date=date(2026, 10, 19),
            description="Salaire",
            amount=550,
            account="Compte courant",
            money_map_type=MoneyMapType.INCOME.value,
            money_map_subcategory="Salaire",
        )
    )
    db_session.commit()
    ObservationFactRepository(db_session).put_period_coverage(["2026-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 750,
                "frequency": "weekly",
            },
        },
    )

    assert response.status_code == 200
    conflict = response.json()["advice"]["outputs"][1]["contradiction"]
    assert conflict["signal"] == "recurring_income_lower"
    assert conflict["period"] == ["2026-10-12", "2026-10-19"]


@patch("app.api.deps.AdviceGenerator")
def test_date_coincidence_does_not_pair_one_off_income(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Unrelated salary on the expected date cannot contest one-off income."""
    october = _add_income_month(db_session, 2026, 10, 2_000)
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "expected_one_off_income",
                "amount": 1_000,
                "expected_date": "2026-10-05",
            },
        },
    )

    assert response.status_code == 200
    assert all(output["type"] != "clarification" for output in response.json()["advice"]["outputs"])


@patch("app.api.deps.AdviceGenerator")
def test_non_salary_date_coincidence_does_not_pair_one_off_income(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Date and broad income taxonomy do not identify one declared event."""
    october = _add_income_month(db_session, 2026, 10, 800)
    october.transactions[0].description = "Prime annuelle"
    october.transactions[0].money_map_subcategory = "Prime"
    db_session.commit()
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "expected_one_off_income",
                "amount": 1_000,
                "expected_date": "2026-10-05",
            },
        },
    )

    assert response.status_code == 200
    assert all(output["type"] != "clarification" for output in response.json()["advice"]["outputs"])


@patch("app.api.deps.AdviceGenerator")
def test_labeled_one_off_income_opens_direct_clarification(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Exact expected label and date pair one-off income."""
    october = _add_income_month(db_session, 2026, 10, 750)
    october.transactions[0].description = "Prime annuelle"
    db_session.commit()
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "expected_one_off_income",
                "label": "Prime annuelle",
                "amount": 1_000,
                "expected_date": "2026-10-05",
            },
        },
    )

    assert response.status_code == 200
    conflict = response.json()["advice"]["outputs"][1]
    assert conflict["type"] == "clarification"
    assert conflict["contradiction"]["signal"] == "one_off_income_mismatch"
    assert conflict["contradiction"]["observed_value"] == 750


@patch("app.api.deps.AdviceGenerator")
def test_exact_twenty_percent_one_off_gap_is_ignored(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """One-off mismatch must exceed the twenty-percent boundary."""
    october = _add_income_month(db_session, 2026, 10, 800)
    october.transactions[0].description = "Prime annuelle"
    db_session.commit()
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "expected_one_off_income",
                "label": "Prime annuelle",
                "amount": 1_000,
                "expected_date": "2026-10-05",
            },
        },
    )

    assert response.status_code == 200
    assert all(output["type"] != "clarification" for output in response.json()["advice"]["outputs"])


@patch("app.api.deps.AdviceGenerator")
def test_exact_one_off_obligation_opens_direct_clarification(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Exact label and due date pair one-off obligation."""
    october = _add_obligation_month(db_session, 2026, 10, 1_250)
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _obligation_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "commitment_fact": {
                "fact_type": "one_off_obligation",
                "label": "Loyer",
                "amount": 1_000,
                "due_date": "2026-10-08",
            },
        },
    )

    assert response.status_code == 200
    conflict = response.json()["advice"]["outputs"][0]
    assert conflict["type"] == "clarification"
    assert conflict["contradiction"]["signal"] == "one_off_obligation_mismatch"
    assert conflict["contradiction"]["observed_value"] == 1_250


@patch("app.api.deps.AdviceGenerator")
def test_recurring_obligation_uses_two_adverse_cycles(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Two matched 25% higher obligations open clarification."""
    september = _add_obligation_month(db_session, 2025, 9, 1_250)
    october = _add_obligation_month(db_session, 2025, 10, 1_250)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _obligation_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "commitment_fact": {
                "fact_type": "recurring_obligation",
                "label": "Loyer",
                "amount": 1_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    conflict = response.json()["advice"]["outputs"][0]
    assert conflict["type"] == "clarification"
    assert conflict["contradiction"]["signal"] == "recurring_obligation_higher"
    assert conflict["contradiction"]["observed_value"] == 1_250
    assert conflict["contradiction"]["transaction_ids"] == [
        september.transactions[0].id,
        october.transactions[0].id,
    ]


@patch("app.api.deps.AdviceGenerator")
def test_obligation_correction_replaces_the_questioned_fact(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Correction updates the contradicted obligation even when its label changes."""
    _add_obligation_month(db_session, 2025, 9, 1_250)
    october = _add_obligation_month(db_session, 2025, 10, 1_250)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _obligation_dependent_advice
    mock_generator_class.return_value = mock_generator
    initial = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "commitment_fact": {
                "fact_type": "recurring_obligation",
                "label": "Loyer",
                "amount": 1_000,
                "frequency": "monthly",
            },
        },
    )
    assert initial.json()["advice"]["outputs"][0]["type"] == "clarification"

    corrected = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "commitment_fact": {
                "fact_type": "recurring_obligation",
                "label": "Crédit immobilier",
                "amount": 1_300,
                "frequency": "monthly",
            },
        },
    )

    assert corrected.status_code == 200
    db_session.expire_all()
    facts = db_session.query(CommitmentFact).all()
    assert [(fact.label, fact.amount) for fact in facts] == [("Crédit immobilier", 1_300)]


@patch("app.api.deps.AdviceGenerator")
def test_incomplete_coverage_cannot_contest_recurring_obligation(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Matched obligation cycles stay silent with incomplete coverage."""
    _add_obligation_month(db_session, 2025, 9, 1_250)
    october = _add_obligation_month(db_session, 2025, 10, 1_250)
    ObservationFactRepository(db_session).put_period_coverage(
        ["2025-09", "2025-10"],
        False,
        ["Compte joint"],
    )
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _obligation_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "commitment_fact": {
                "fact_type": "recurring_obligation",
                "label": "Loyer",
                "amount": 1_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["advice"]["outputs"][0]["type"] == "recommendation"


@patch("app.api.deps.AdviceGenerator")
def test_favorable_obligation_requires_three_cycles(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Two lower obligation cycles stay silent; third opens clarification."""
    _add_obligation_month(db_session, 2025, 8, 750)
    september = _add_obligation_month(db_session, 2025, 9, 750)
    ObservationFactRepository(db_session).put_period_coverage(["2025-08", "2025-09"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _obligation_dependent_advice
    mock_generator_class.return_value = mock_generator

    two_cycles = client.post(
        "/api/advice/generate",
        json={
            "year": september.year,
            "month": september.month,
            "commitment_fact": {
                "fact_type": "recurring_obligation",
                "label": "Loyer",
                "amount": 1_000,
                "frequency": "monthly",
            },
        },
    )
    october = _add_obligation_month(db_session, 2025, 10, 750)
    ObservationFactRepository(db_session).put_period_coverage(["2025-08", "2025-09", "2025-10"], True, [])
    three_cycles = client.post(
        "/api/advice/generate",
        json={"year": october.year, "month": october.month, "regenerate": True},
    )

    assert two_cycles.status_code == 200
    assert two_cycles.json()["advice"]["outputs"][0]["type"] == "recommendation"
    assert three_cycles.status_code == 200
    conflict = three_cycles.json()["advice"]["outputs"][0]
    assert conflict["type"] == "clarification"
    assert conflict["contradiction"]["signal"] == "recurring_obligation_lower"
    assert conflict["contradiction"]["period"] == ["2025-08", "2025-09", "2025-10"]


@patch("app.api.deps.AdviceGenerator")
def test_confirm_acknowledges_cycles_without_reopening(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Confirm keeps income active and same evidence cannot reopen."""
    _add_income_month(db_session, 2025, 9, 2_300)
    october = _add_income_month(db_session, 2025, 10, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator
    payload = {
        "year": october.year,
        "month": october.month,
        "income_fact": {
            "fact_type": "usual_disposable_income",
            "amount": 3_000,
            "frequency": "monthly",
        },
    }
    pending = client.post("/api/advice/generate", json=payload)

    confirmed = client.post("/api/advice/generate", json=payload)
    recalculated = client.post(
        "/api/advice/generate",
        json={"year": october.year, "month": october.month, "regenerate": True},
    )
    october.transactions[0].money_map_subcategory = "Revenu récurrent"
    db_session.commit()
    reclassified = client.post(
        "/api/advice/generate",
        json={"year": october.year, "month": october.month, "regenerate": True},
    )

    assert pending.status_code == 200
    assert pending.json()["advice"]["outputs"][1]["type"] == "clarification"
    assert confirmed.status_code == 200
    assert [item["type"] for item in confirmed.json()["advice"]["outputs"]] == [
        "no_action",
        "recommendation",
    ]
    assert confirmed.json()["advice"]["outputs"][1]["trace"]["details"]["transitions"] == [
        "Contradiction confirmée : fait maintenu actif et observations acquittées."
    ]
    assert recalculated.status_code == 200
    assert all(item["type"] != "clarification" for item in recalculated.json()["advice"]["outputs"])
    assert reclassified.status_code == 200
    assert all(item["type"] != "clarification" for item in reclassified.json()["advice"]["outputs"])
    fact = db_session.get(IncomeFact, "usual_disposable_income")
    assert fact is not None
    assert fact.state == "active"


@pytest.mark.parametrize(
    ("remember", "answer_amount", "expected_output_amount", "expected_state", "transition"),
    [
        (True, 2_400, 100, "corrected", "Contradiction corrigée : valeur remplacée et observations acquittées."),
        (False, 3_000, 700, "to_confirm", "Contradiction résolue pour cette session : ancien fait rendu à confirmer."),
    ],
)
@patch("app.api.deps.AdviceGenerator")
def test_correction_and_session_override_resolve_income_conflict(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
    remember: bool,
    answer_amount: float,
    expected_output_amount: float,
    expected_state: str,
    transition: str,
) -> None:
    """Correction persists; session override neutralizes old fact."""
    _add_income_month(db_session, 2025, 9, 2_300)
    october = _add_income_month(db_session, 2025, 10, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator
    client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    resolved = client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": answer_amount,
                "frequency": "monthly",
            },
            "remember_fact": remember,
        },
    )

    assert resolved.status_code == 200
    output = resolved.json()["advice"]["outputs"][1]
    assert output["type"] == "recommendation"
    assert output["amount"] == expected_output_amount
    assert output["trace"]["details"]["transitions"] == [transition]
    fact = db_session.get(IncomeFact, "usual_disposable_income")
    assert fact is not None
    assert fact.amount == (2_400 if remember else 3_000)
    assert fact.state == expected_state


@pytest.mark.parametrize(
    ("action", "transition", "expected_state"),
    [
        ("skip", "Contradiction passée : fait rendu à confirmer et neutralisé.", "to_confirm"),
        ("unknown", "Contradiction inconnue : fait rendu à confirmer et neutralisé.", "to_confirm"),
        ("delete", "Contradiction supprimée : fait supprimé sans ancienne valeur réactivable.", None),
    ],
)
@patch("app.api.deps.AdviceGenerator")
def test_abstention_neutralizes_contested_income(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
    action: str,
    transition: str,
    expected_state: str | None,
) -> None:
    """Abstention neutralizes; deletion removes the contested fact."""
    _add_income_month(db_session, 2025, 9, 2_300)
    october = _add_income_month(db_session, 2025, 10, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator
    client.post(
        "/api/advice/generate",
        json={
            "year": october.year,
            "month": october.month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    resolved = client.post(
        "/api/advice/generate",
        json={"year": october.year, "month": october.month, "clarification_action": action},
    )

    assert resolved.status_code == 200
    outputs = resolved.json()["advice"]["outputs"]
    assert [output["type"] for output in outputs] == ["no_action", "unresolved"]
    assert all(output["trace"]["details"]["transitions"] == [transition] for output in outputs)
    evidence = outputs[1]["trace"]["details"]["observations"][0]
    assert evidence["period"] == "2025-09 à 2025-10"
    assert evidence["source_months"] == ["2025-09", "2025-10"]
    fact = db_session.get(IncomeFact, "usual_disposable_income")
    if expected_state is None:
        assert fact is None
    else:
        assert fact is not None
        assert fact.state == expected_state


@patch("app.api.deps.AdviceGenerator")
def test_only_fully_post_confirmation_series_reopens_income_conflict(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """New adverse series reopens only after two post-confirmation cycles."""
    _add_income_month(db_session, 2025, 9, 2_300)
    october_2025 = _add_income_month(db_session, 2025, 10, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(["2025-09", "2025-10"], True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator
    payload = {
        "year": october_2025.year,
        "month": october_2025.month,
        "income_fact": {
            "fact_type": "usual_disposable_income",
            "amount": 3_000,
            "frequency": "monthly",
        },
    }
    client.post("/api/advice/generate", json=payload)
    client.post("/api/advice/generate", json=payload)

    september_2026 = _add_income_month(db_session, 2026, 9, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(
        ["2025-09", "2025-10", "2026-09"],
        True,
        [],
    )
    one_new_cycle = client.post(
        "/api/advice/generate",
        json={"year": september_2026.year, "month": september_2026.month},
    )
    october_2026 = _add_income_month(db_session, 2026, 10, 2_300)
    ObservationFactRepository(db_session).put_period_coverage(
        ["2025-10", "2026-09", "2026-10"],
        True,
        [],
    )
    two_new_cycles = client.post(
        "/api/advice/generate",
        json={"year": october_2026.year, "month": october_2026.month},
    )

    assert one_new_cycle.status_code == 200
    assert all(item["type"] != "clarification" for item in one_new_cycle.json()["advice"]["outputs"])
    assert two_new_cycles.status_code == 200
    conflict = two_new_cycles.json()["advice"]["outputs"][1]["contradiction"]
    assert conflict["period"] == ["2026-09", "2026-10"]
    assert len(conflict["acknowledged_observations"]) == 2


@pytest.mark.parametrize(
    ("months", "observed_amount"),
    [
        ([(2025, 9), (2025, 10)], 2_700),
        ([(2025, 9), (2025, 10)], 2_400),
        ([(2025, 8), (2025, 10)], 2_300),
    ],
)
@patch("app.api.deps.AdviceGenerator")
def test_income_gap_or_subthreshold_difference_is_ignored(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
    months: list[tuple[int, int]],
    observed_amount: float,
) -> None:
    """Subthreshold amount or nonconsecutive months cannot contest income."""
    records = [_add_income_month(db_session, year, month, observed_amount) for year, month in months]
    coverage_months = [f"{year:04d}-{month:02d}" for year, month in months]
    ObservationFactRepository(db_session).put_period_coverage(coverage_months, True, [])
    mock_generator = MagicMock()
    mock_generator.generate_advice.side_effect = _income_dependent_advice
    mock_generator_class.return_value = mock_generator

    response = client.post(
        "/api/advice/generate",
        json={
            "year": records[-1].year,
            "month": records[-1].month,
            "income_fact": {
                "fact_type": "usual_disposable_income",
                "amount": 3_000,
                "frequency": "monthly",
            },
        },
    )

    assert response.status_code == 200
    assert all(item["type"] != "clarification" for item in response.json()["advice"]["outputs"])


def test_incomplete_trailing_cycle_does_not_hide_complete_series() -> None:
    """Latest incomplete cycle cannot suppress prior complete evidence."""
    samples = [
        TransactionSample(
            transaction_id=index,
            description="Salaire",
            amount=2_300,
            date=date(2025, month, 5),
        )
        for index, month in enumerate((9, 10, 11), start=1)
    ]

    series = _select_adverse_series(
        samples,
        "monthly",
        3_000,
        {"2025-09", "2025-10"},
        [(2, "lower", "recurring_income_lower")],
    )

    assert series is not None
    assert series[3] == ["2025-09", "2025-10"]
