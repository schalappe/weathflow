"""Integration tests for observed-evidence validity."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.categorization.models import CategorizationResult
from tests.integration.fixtures.csv_builder import CSVBuilder, combine_csvs

MOCK_API_KEY_ENV = {"ANTHROPIC_API_KEY": "test-key-for-integration-tests"}


def _create_month(db: Session, year: int, month: int) -> None:
    """Create advice-eligible month."""
    db.add(
        Month(
            year=year,
            month=month,
            total_income=3000,
            total_core=1800,
            total_choice=500,
            total_compound=700,
            core_percentage=60,
            choice_percentage=16.7,
            compound_percentage=23.3,
            score=1,
            score_label="Need Improvement",
        )
    )
    db.commit()


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_incomplete_period_answer_reaches_generation_with_exact_scope(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Incomplete coverage stays scoped and blocks aggregate conclusions."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    mock_generator = MagicMock()
    final_response = {
        "outputs": [
            {
                "type": "unresolved",
                "priority": "high",
                "conclusion": "La comparaison reste non conclue.",
                "trace": {
                    "summary": "Le compte joint manque sur la période.",
                    "details": {
                        "observations": [
                            {
                                "fact": "Des opérations sont présentes.",
                                "period": "2025-09 à 2025-10",
                                "scope": "Comptes importés",
                                "source": "observed_data",
                                "evidence_type": "presence",
                                "source_months": ["2025-09", "2025-10"],
                                "transaction_ids": [],
                            }
                        ],
                        "limits": ["Compte joint absent."],
                        "declared_facts": [
                            {
                                "fact_type": "period_coverage",
                                "coverage_months": ["2025-09", "2025-10"],
                                "accounts": [],
                                "complete": False,
                                "missing_elements": ["Compte joint"],
                                "state": "active",
                                "last_confirmed_at": "2026-08-04T12:00:00",
                                "valid_until": None,
                                "can_correct": True,
                                "can_delete": True,
                            }
                        ],
                    },
                },
            }
        ]
    }
    mock_generator_class.return_value = mock_generator
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Couverture de la période",
                "observation": "La couverture change la comparaison.",
                "possible_effect": "La hausse peut disparaître.",
                "question": "Ces deux mois sont-ils complets ?",
                "fact_type": "period_coverage",
                "coverage_months": ["2025-09", "2025-10"],
                "material_effects": ["Conserver la hausse.", "Ne pas conclure."],
            }
        ]
    }
    pending = client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    assert pending.status_code == 200
    mock_generator.generate_advice.return_value = final_response

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "period_coverage": {
                "coverage_months": ["2025-09", "2025-10"],
                "complete": False,
                "missing_elements": ["Compte joint"],
            },
        },
    )

    assert response.status_code == 200
    context = mock_generator.generate_advice.call_args.args[2]
    assert [fact.model_dump(mode="json") for fact in context.period_coverages] == [
        {
            "coverage_months": ["2025-09", "2025-10"],
            "accounts": [],
            "complete": False,
            "missing_elements": ["Compte joint"],
            "state": "active",
            "last_confirmed_at": context.period_coverages[0].last_confirmed_at.isoformat(),
            "valid_until": None,
            "provenance_issues": [],
        }
    ]


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_aggregate_on_incomplete_coverage_becomes_unresolved_without_question(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Incomplete scope rejects aggregate evidence without another question."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    mock_generator = MagicMock()
    recommendation = {
        "outputs": [
            {
                "type": "recommendation",
                "priority": "high",
                "subject": "Dépenses discrétionnaires",
                "action": "Réduire les dépenses de 100 €.",
                "amount": 100,
                "income_dependent": False,
                "trace": {
                    "summary": "Les dépenses ont augmenté.",
                    "details": {
                        "observations": [
                            {
                                "fact": "Hausse de 100 € entre les deux mois.",
                                "period": "2025-09 à 2025-10",
                                "scope": "Tous les comptes",
                                "source": "observed_data",
                                "evidence_type": "comparison",
                                "source_months": ["2025-09", "2025-10"],
                                "transaction_ids": [],
                            }
                        ],
                        "calculations": ["600 € - 500 € = 100 €."],
                        "limits": [],
                        "declared_facts": [
                            {
                                "fact_type": "period_coverage",
                                "coverage_months": ["2025-09", "2025-10"],
                                "accounts": [],
                                "complete": False,
                                "missing_elements": ["Compte joint"],
                                "state": "active",
                                "last_confirmed_at": "2026-08-04T12:00:00",
                                "valid_until": None,
                                "can_correct": True,
                                "can_delete": True,
                            }
                        ],
                    },
                },
            }
        ]
    }
    mock_generator_class.return_value = mock_generator
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Couverture de la période",
                "observation": "La couverture change la comparaison.",
                "possible_effect": "La hausse peut disparaître.",
                "question": "Ces deux mois sont-ils complets ?",
                "fact_type": "period_coverage",
                "coverage_months": ["2025-09", "2025-10"],
                "material_effects": ["Conserver la hausse.", "Ne pas conclure."],
            }
        ]
    }
    pending = client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    assert pending.status_code == 200
    out_of_scope = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "period_coverage": {
                "coverage_months": ["2025-10"],
                "complete": False,
                "missing_elements": ["Compte joint"],
            },
        },
    )
    assert out_of_scope.status_code == 422
    mock_generator.generate_advice.return_value = recommendation

    response = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "period_coverage": {
                "coverage_months": ["2025-09", "2025-10"],
                "complete": False,
                "missing_elements": ["Compte joint"],
            },
        },
    )

    assert response.status_code == 200
    output = response.json()["advice"]["outputs"][0]
    assert output["type"] == "unresolved"
    assert "incomplète" in output["conclusion"]
    assert all(item["type"] != "clarification" for item in response.json()["advice"]["outputs"])


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
@patch("app.services.upload.service.TransactionCategorizer")
def test_truncated_import_can_trigger_scoped_coverage_clarification(
    mock_categorizer_class: MagicMock,
    mock_generator_class: MagicMock,
    client: TestClient,
) -> None:
    """Truncated import provenance reaches material advice clarification."""
    categorizer = MagicMock()
    categorizer.categorize.side_effect = lambda inputs: (
        [
            CategorizationResult(
                id=index,
                money_map_type=MoneyMapType.CORE,
                money_map_subcategory="Housing",
                confidence=0.95,
            )
            for index, _ in enumerate(inputs, start=1)
        ],
        1,
    )
    mock_categorizer_class.return_value = categorizer
    csv = combine_csvs(
        CSVBuilder("2025-09").add_grocery("Loyer", 900).build(),
        CSVBuilder("2025-10").add_grocery("Loyer", 900).build(),
    )
    imported = client.post(
        "/api/categorize",
        files={"file": ("partial.csv", csv, "text/csv")},
        params={
            "months_to_process": "all",
            "import_mode": "replace",
            "coverage_issue": "truncated_statement",
        },
    )
    assert imported.status_code == 200

    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Évolution des dépenses",
                "observation": "Le relevé importé est tronqué.",
                "possible_effect": "La comparaison peut disparaître avec les opérations manquantes.",
                "question": "Ces deux mois couvrent-ils tous les comptes et toutes les dates ?",
                "fact_type": "period_coverage",
                "coverage_months": ["2025-09", "2025-10"],
                "material_effects": ["Réduire les dépenses.", "Ne conclure aucune hausse."],
            }
        ]
    }
    mock_generator_class.return_value = mock_generator

    response = client.post("/api/advice/generate", json={"year": 2025, "month": 10})

    assert response.status_code == 200
    context = mock_generator.generate_advice.call_args.args[2]
    assert context.coverage_signals[0].provenance_issues == ["truncated_statement"]
    assert response.json()["advice"]["outputs"][0]["fact_type"] == "period_coverage"


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_new_counter_entry_reopens_only_confirmed_transaction_occurrence(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """New structural link can contest confirmed occurrence meaning."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    current_month = db_session.query(Month).filter_by(year=2025, month=10).one()
    debit = Transaction(
        month_id=current_month.id,
        date=date(2025, 10, 5),
        description="Paiement carte",
        amount=-120,
        account="Compte courant",
        bankin_category="Achats",
        bankin_subcategory="Divers",
        money_map_type="CORE",
        money_map_subcategory="Other necessities",
    )
    other = Transaction(
        month_id=current_month.id,
        date=date(2025, 10, 6),
        description="Autre achat",
        amount=-40,
        account="Compte courant",
        bankin_category="Achats",
        bankin_subcategory="Divers",
        money_map_type="CORE",
        money_map_subcategory="Other necessities",
    )
    db_session.add_all([debit, other])
    db_session.commit()
    db_session.refresh(debit)
    db_session.refresh(other)
    decided = {
        "type": "no_action",
        "priority": "medium",
        "conclusion": "Le paiement est une dépense ponctuelle confirmée.",
        "trace": {
            "summary": "Nature confirmée pour cette occurrence.",
            "details": {
                "observations": [
                    {
                        "fact": "Paiement de 120 €.",
                        "period": "2025-10",
                        "scope": "Transaction confirmée",
                        "source": "observed_data",
                        "evidence_type": "presence",
                        "source_months": ["2025-10"],
                        "transaction_ids": [debit.id],
                    }
                ],
                "declared_facts": [
                    {
                        "fact_id": 1,
                        "fact_type": "transaction_nature",
                        "transaction_ids": [debit.id],
                        "source_months": ["2025-10"],
                        "nature": "expense",
                        "scope": "occurrence",
                        "state": "active",
                        "last_confirmed_at": "2026-08-04T12:00:00",
                        "valid_until": None,
                        "can_correct": True,
                        "can_delete": True,
                    }
                ],
            },
        },
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Paiement carte du 5 octobre",
                "observation": "La nature de cette opération change le conseil.",
                "possible_effect": "La dépense peut être conservée ou exclue.",
                "question": "Quelle est la nature de cette opération précise ?",
                "fact_type": "transaction_nature",
                "transaction_ids": [debit.id, other.id],
                "linked_transaction_ids": [999_998],
                "material_effects": ["Conserver la dépense.", "Exclure la dépense."],
            }
        ]
    }
    mock_generator_class.return_value = mock_generator
    pending = client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    assert pending.status_code == 200

    out_of_scope = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "transaction_nature": {
                "transaction_ids": [999_999],
                "nature": "expense",
                "scope": "occurrence",
            },
        },
    )
    assert out_of_scope.status_code == 422

    mock_generator.generate_advice.return_value = {"outputs": [decided]}
    confirmed = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "transaction_nature": {
                "transaction_ids": [debit.id],
                "nature": "expense",
                "scope": "occurrence",
            },
        },
    )
    assert confirmed.status_code == 200

    credit = Transaction(
        month_id=current_month.id,
        date=date(2025, 10, 8),
        description="Annulation carte",
        amount=120,
        account="Compte courant",
        bankin_category="Entrées d'argent",
        bankin_subcategory="Remboursements",
        money_map_type="INCOME",
        money_map_subcategory="Reimbursements",
    )
    db_session.add(credit)
    db_session.commit()
    db_session.refresh(credit)
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Paiement carte du 5 octobre",
                "observation": "Une contre-écriture de 120 € est apparue le 8 octobre.",
                "possible_effect": "Le paiement peut être annulé plutôt que dépensé.",
                "question": "Quelle est la nature de cette opération précise ?",
                "fact_type": "transaction_nature",
                "transaction_ids": [debit.id],
                "linked_transaction_ids": [credit.id],
                "material_effects": ["Conserver la dépense.", "Retirer la dépense annulée."],
            }
        ]
    }

    reopened = client.post(
        "/api/advice/generate",
        json={"year": 2025, "month": 10, "regenerate": True},
    )

    assert reopened.status_code == 200
    context = mock_generator.generate_advice.call_args.args[2]
    assert context.transaction_natures[0].state == "to_confirm"
    assert context.transaction_nature_signals[0].signal_type == "counter_entry"
    assert reopened.json()["advice"]["outputs"][0]["transaction_ids"] == [debit.id]


@patch.dict("os.environ", MOCK_API_KEY_ENV)
@patch("app.api.deps.AdviceGenerator")
def test_category_merchant_frequency_and_volume_do_not_expand_or_contest_series(
    mock_generator_class: MagicMock,
    client: TestClient,
    db_session: Session,
) -> None:
    """Non-structural signals leave explicit series scope active."""
    _create_month(db_session, 2025, 9)
    _create_month(db_session, 2025, 10)
    current_month = db_session.query(Month).filter_by(year=2025, month=10).one()
    confirmed_series = [
        Transaction(
            month_id=current_month.id,
            date=date(2025, 10, day),
            description="CAFE CENTRAL",
            amount=-20,
            account="Compte courant",
            bankin_category="Restaurants",
            bankin_subcategory="Cafés",
            money_map_type="CORE",
            money_map_subcategory="Groceries",
        )
        for day in (2, 9)
    ]
    db_session.add_all(confirmed_series)
    db_session.commit()
    for transaction in confirmed_series:
        db_session.refresh(transaction)
    transaction_ids = [transaction.id for transaction in confirmed_series]
    output = {
        "type": "no_action",
        "priority": "low",
        "conclusion": "La série confirmée reste une dépense.",
        "trace": {
            "summary": "Deux occurrences explicitement confirmées.",
            "details": {
                "observations": [
                    {
                        "fact": "Deux paiements confirmés.",
                        "period": "2025-10",
                        "scope": "Deux transactions",
                        "source": "observed_data",
                        "evidence_type": "presence",
                        "source_months": ["2025-10"],
                        "transaction_ids": transaction_ids,
                    }
                ],
                "declared_facts": [
                    {
                        "fact_id": 1,
                        "fact_type": "transaction_nature",
                        "transaction_ids": transaction_ids,
                        "source_months": ["2025-10"],
                        "nature": "expense",
                        "scope": "series",
                        "state": "active",
                        "last_confirmed_at": "2026-08-04T12:00:00",
                        "valid_until": None,
                        "can_correct": True,
                        "can_delete": True,
                    }
                ],
            },
        },
    }
    mock_generator = MagicMock()
    mock_generator.generate_advice.return_value = {
        "outputs": [
            {
                "type": "clarification",
                "priority": "high",
                "subject": "Série de paiements",
                "observation": "La nature de cette série change le conseil.",
                "possible_effect": "La série peut être conservée ou exclue.",
                "question": "Quelle est la nature de cette série précise ?",
                "fact_type": "transaction_nature",
                "transaction_ids": transaction_ids,
                "linked_transaction_ids": [999_998],
                "material_effects": ["Conserver la série.", "Exclure la série."],
            }
        ]
    }
    mock_generator_class.return_value = mock_generator
    pending = client.post("/api/advice/generate", json={"year": 2025, "month": 10})
    assert pending.status_code == 200
    mock_generator.generate_advice.return_value = {"outputs": [output]}
    confirmed = client.post(
        "/api/advice/generate",
        json={
            "year": 2025,
            "month": 10,
            "transaction_nature": {
                "transaction_ids": transaction_ids,
                "nature": "expense",
                "scope": "series",
            },
        },
    )
    assert confirmed.status_code == 200

    recategorized = client.patch(
        f"/api/transactions/{confirmed_series[0].id}",
        json={"money_map_type": "CHOICE", "money_map_subcategory": "Dining out"},
    )
    assert recategorized.status_code == 200
    db_session.add_all(
        [
            Transaction(
                month_id=current_month.id,
                date=date(2025, 10, 16),
                description="CAFE CENTRAL",
                amount=-400,
                account="Compte courant",
                bankin_category="Restaurants",
                bankin_subcategory="Cafés",
                money_map_type="CHOICE",
                money_map_subcategory="Dining out",
            ),
            Transaction(
                month_id=current_month.id,
                date=date(2025, 10, 17),
                description="Vente occasionnelle",
                amount=20,
                account="Compte courant",
                bankin_category="Entrées d'argent",
                bankin_subcategory="Autres",
                money_map_type="INCOME",
                money_map_subcategory="Other",
            ),
        ]
    )
    db_session.commit()

    regenerated = client.post(
        "/api/advice/generate",
        json={"year": 2025, "month": 10, "regenerate": True},
    )

    assert regenerated.status_code == 200
    context = mock_generator.generate_advice.call_args.args[2]
    assert context.transaction_natures[0].state == "active"
    assert context.transaction_natures[0].transaction_ids == transaction_ids
    assert context.transaction_nature_signals == []
