"""Unit tests for advice storage services."""

import json
from datetime import date

from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.advice import AdviceRepository
from app.services.advice import service
from app.services.advice.models import AdviceResponse
from tests.conftest import DatabaseTestCase


def _month(session: Session) -> Month:
    """Create persisted month."""
    month = Month(
        year=2025,
        month=1,
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
    session.add(month)
    session.commit()
    session.refresh(month)
    return month


def _advice() -> AdviceResponse:
    """Build strict advice response."""
    return AdviceResponse.model_validate(
        {
            "outputs": [
                {
                    "type": "recommendation",
                    "income_dependent": False,
                    "priority": "high",
                    "action": "Réduire les repas au restaurant.",
                    "amount": 120,
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
            ]
        }
    )


def _transaction(session: Session, month: Month, description: str, amount: float, category: str) -> None:
    """Create persisted transaction."""
    session.add(
        Transaction(
            month_id=month.id,
            date=date(2025, 1, 15),
            description=description,
            amount=amount,
            money_map_type=category,
        )
    )
    session.commit()
    session.refresh(month)


class TestAdviceStorage(DatabaseTestCase):
    """Advice persistence contracts."""

    def test_create_update_and_get_advice(self) -> None:
        """Monthly advice upsert keeps one current record."""
        month = _month(self.session)
        repository = AdviceRepository(self.session)

        created = service.create_or_update_advice(repository, month.id, '{"outputs":[1]}')
        updated = service.create_or_update_advice(repository, month.id, '{"outputs":[2]}')
        retrieved = service.get_advice_by_month_id(repository, month.id)

        self.assertEqual(created.id, updated.id)
        self.assertEqual(retrieved, updated)
        self.assertEqual(updated.advice_text, '{"outputs":[2]}')
        self.assertEqual(self.session.query(Advice).count(), 1)

    def test_get_returns_none_without_advice(self) -> None:
        """Missing advice returns None."""
        month = _month(self.session)

        result = service.get_advice_by_month_id(AdviceRepository(self.session), month.id)

        self.assertIsNone(result)


class TestGenerationData(DatabaseTestCase):
    """Observed data conversion contracts."""

    def test_month_data_groups_expenses_and_excludes_income(self) -> None:
        """Generator input groups expenses and excludes income."""
        month = _month(self.session)
        _transaction(self.session, month, "Rent", -1000, "CORE")
        _transaction(self.session, month, "Restaurant", -45, "CHOICE")
        _transaction(self.session, month, "Salary", 3000, "INCOME")

        result = service.month_to_month_data(month)

        assert result.transactions is not None
        self.assertEqual([item.description for item in result.transactions["CORE"]], ["Rent"])
        self.assertEqual([item.description for item in result.transactions["CHOICE"]], ["Restaurant"])
        self.assertEqual(result.transactions["COMPOUND"], [])
        self.assertEqual(result.transactions["CORE"][0].amount, 1000)

    def test_month_data_sorts_largest_expense_first(self) -> None:
        """Generator input sorts each category by absolute amount."""
        month = _month(self.session)
        _transaction(self.session, month, "Small", -10, "CORE")
        _transaction(self.session, month, "Large", -500, "CORE")

        result = service.month_to_month_data(month)

        assert result.transactions is not None
        self.assertEqual([item.description for item in result.transactions["CORE"]], ["Large", "Small"])


class TestAdviceSerialization(DatabaseTestCase):
    """Decision JSON storage contract."""

    def test_serializes_only_decision_outputs(self) -> None:
        """Storage JSON contains new contract only."""
        payload = json.loads(service.advice_response_to_json(_advice()))

        self.assertEqual(set(payload), {"outputs"})
        self.assertEqual(payload["outputs"][0]["type"], "recommendation")
        self.assertNotIn("problem_areas", payload)
