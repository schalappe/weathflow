"""Unit tests for advice service functions."""

import json
import unittest
from datetime import date

from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.advice import AdviceRepository
from app.services.advice import service as advice_service
from app.services.advice.models import AdviceResponse, ProblemArea
from tests.conftest import DatabaseTestCase


def _create_month(session: Session, year: int = 2025, month: int = 1) -> Month:
    """Create a test month record."""
    month_record = Month(
        year=year,
        month=month,
        total_income=3000.0,
        total_core=1500.0,
        total_choice=900.0,
        total_compound=600.0,
        core_percentage=50.0,
        choice_percentage=30.0,
        compound_percentage=20.0,
        score=3,
        score_label="Great",
    )
    session.add(month_record)
    session.commit()
    session.refresh(month_record)
    return month_record


def _create_advice_response() -> AdviceResponse:
    """Create a test AdviceResponse."""
    return AdviceResponse(
        analysis="Votre gestion financière est excellente ce mois-ci.",
        problem_areas=[
            ProblemArea(category="Subscriptions", amount=85.0, trend="+20%"),
            ProblemArea(category="Dining", amount=150.0, trend="+15%"),
            ProblemArea(category="Entertainment", amount=120.0, trend="N/A"),
        ],
        recommendations=[
            "Réduire les abonnements non utilisés.",
            "Limiter les repas au restaurant.",
            "Maintenir votre taux d'épargne actuel.",
        ],
        encouragement="Continuez sur cette lancée!",
    )


def _create_transaction(
    session: Session,
    month: Month,
    description: str,
    amount: float,
    money_map_type: str,
    subcategory: str | None = None,
) -> Transaction:
    """Create a test transaction."""
    tx = Transaction(
        month_id=month.id,
        date=date(month.year, month.month, 15),
        description=description,
        amount=amount,
        money_map_type=money_map_type,
        money_map_subcategory=subcategory,
    )
    session.add(tx)
    session.flush()
    return tx


class TestGetAdviceByMonthId(DatabaseTestCase):
    """Tests for get_advice_by_month_id function."""

    def test_returns_advice_when_exists(self) -> None:
        """Get advice returns advice record when it exists for the month."""
        month = _create_month(self.session)
        advice = Advice(month_id=month.id, advice_text='{"analysis": "test"}')
        self.session.add(advice)
        self.session.commit()

        advice_repo = AdviceRepository(self.session)
        result = advice_service.get_advice_by_month_id(advice_repo, month.id)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.month_id, month.id)
        self.assertEqual(result.advice_text, '{"analysis": "test"}')

    def test_returns_none_when_not_exists(self) -> None:
        """Get advice returns None when no advice exists for the month."""
        month = _create_month(self.session)

        advice_repo = AdviceRepository(self.session)
        result = advice_service.get_advice_by_month_id(advice_repo, month.id)

        self.assertIsNone(result)


class TestCreateOrUpdateAdvice(DatabaseTestCase):
    """Tests for create_or_update_advice function."""

    def test_creates_new_advice_record(self) -> None:
        """Create or update creates new advice when none exists."""
        month = _create_month(self.session)
        advice_text = '{"analysis": "new advice"}'

        advice_repo = AdviceRepository(self.session)
        result = advice_service.create_or_update_advice(advice_repo, month.id, advice_text)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.month_id, month.id)
        self.assertEqual(result.advice_text, advice_text)
        self.assertIsNotNone(result.generated_at)

    def test_updates_existing_advice_record(self) -> None:
        """Create or update updates existing advice when it exists."""
        month = _create_month(self.session)
        original_advice = Advice(month_id=month.id, advice_text='{"analysis": "old"}')
        self.session.add(original_advice)
        self.session.commit()
        original_id = original_advice.id
        original_time = original_advice.generated_at

        advice_repo = AdviceRepository(self.session)
        new_text = '{"analysis": "updated"}'
        result = advice_service.create_or_update_advice(advice_repo, month.id, new_text)

        self.assertEqual(result.id, original_id)
        self.assertEqual(result.advice_text, new_text)
        self.assertGreaterEqual(result.generated_at, original_time)

        count = self.session.query(Advice).filter(Advice.month_id == month.id).count()
        self.assertEqual(count, 1)


class TestMonthToMonthData(DatabaseTestCase):
    """Tests for month_to_month_data conversion function."""

    def test_converts_month_to_month_data(self) -> None:
        """Month to MonthData converts all fields correctly."""
        month = _create_month(self.session, year=2025, month=10)

        result = advice_service.month_to_month_data(month)

        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.total_income, 3000.0)
        self.assertEqual(result.total_core, 1500.0)
        self.assertEqual(result.total_choice, 900.0)
        self.assertEqual(result.total_compound, 600.0)
        self.assertEqual(result.core_percentage, 50.0)
        self.assertEqual(result.choice_percentage, 30.0)
        self.assertEqual(result.compound_percentage, 20.0)
        self.assertEqual(result.score, 3)
        self.assertEqual(result.score_label, "Great")
        self.assertIsNone(result.category_breakdown)


class TestAdviceResponseToJson(DatabaseTestCase):
    """Tests for advice_response_to_json serialization function."""

    def test_serializes_advice_response_to_json(self) -> None:
        """Advice response to JSON serializes all fields."""
        advice = _create_advice_response()

        result = advice_service.advice_response_to_json(advice)

        self.assertIn("analysis", result)
        self.assertIn("problem_areas", result)
        self.assertIn("recommendations", result)
        self.assertIn("encouragement", result)
        self.assertIn("Subscriptions", result)
        self.assertIn("+20%", result)


class TestExtractAllTransactions(DatabaseTestCase):
    """Tests for _extract_all_transactions function."""

    def test_groups_transactions_by_category(self) -> None:
        """Should group transactions into CORE, CHOICE, COMPOUND categories."""
        month = _create_month(self.session)
        _create_transaction(self.session, month, "Rent", -1000.0, "CORE", "Housing")
        _create_transaction(self.session, month, "Netflix", -15.99, "CHOICE", "Subscriptions")
        _create_transaction(self.session, month, "Savings", -500.0, "COMPOUND", "Savings")
        self.session.commit()
        self.session.refresh(month)

        result = advice_service._extract_all_transactions(month.transactions)

        self.assertIn("CORE", result)
        self.assertIn("CHOICE", result)
        self.assertIn("COMPOUND", result)
        self.assertEqual(len(result["CORE"]), 1)
        self.assertEqual(len(result["CHOICE"]), 1)
        self.assertEqual(len(result["COMPOUND"]), 1)
        self.assertEqual(result["CORE"][0].description, "Rent")
        self.assertEqual(result["CHOICE"][0].description, "Netflix")
        self.assertEqual(result["COMPOUND"][0].description, "Savings")

    def test_excludes_income_and_excluded_transactions(self) -> None:
        """Should not include INCOME or EXCLUDED transactions."""
        month = _create_month(self.session)
        _create_transaction(self.session, month, "Salary", 3000.0, "INCOME")
        _create_transaction(self.session, month, "Transfer", -100.0, "EXCLUDED")
        _create_transaction(self.session, month, "Groceries", -150.0, "CORE", "Food")
        self.session.commit()
        self.session.refresh(month)

        result = advice_service._extract_all_transactions(month.transactions)

        self.assertEqual(len(result["CORE"]), 1)
        self.assertEqual(len(result["CHOICE"]), 0)
        self.assertEqual(len(result["COMPOUND"]), 0)
        # ##>: INCOME and EXCLUDED should not appear in any category.
        all_descriptions = [tx.description for txs in result.values() for tx in txs]
        self.assertNotIn("Salary", all_descriptions)
        self.assertNotIn("Transfer", all_descriptions)

    def test_sorts_transactions_by_absolute_amount_descending(self) -> None:
        """Should sort transactions by absolute amount, largest first."""
        month = _create_month(self.session)
        _create_transaction(self.session, month, "Small", -10.0, "CORE")
        _create_transaction(self.session, month, "Large", -500.0, "CORE")
        _create_transaction(self.session, month, "Medium", -100.0, "CORE")
        self.session.commit()
        self.session.refresh(month)

        result = advice_service._extract_all_transactions(month.transactions)

        self.assertEqual(result["CORE"][0].description, "Large")
        self.assertEqual(result["CORE"][1].description, "Medium")
        self.assertEqual(result["CORE"][2].description, "Small")

    def test_returns_empty_dict_for_empty_transactions(self) -> None:
        """Should return dict with empty lists when no transactions."""
        result = advice_service._extract_all_transactions([])

        self.assertEqual(result["CORE"], [])
        self.assertEqual(result["CHOICE"], [])
        self.assertEqual(result["COMPOUND"], [])

    def test_converts_to_transaction_sample_with_absolute_amount(self) -> None:
        """Should convert amounts to absolute values in TransactionSample."""
        month = _create_month(self.session)
        _create_transaction(self.session, month, "Expense", -150.0, "CHOICE", "Dining")
        self.session.commit()
        self.session.refresh(month)

        result = advice_service._extract_all_transactions(month.transactions)

        tx_sample = result["CHOICE"][0]
        self.assertEqual(tx_sample.description, "Expense")
        self.assertEqual(tx_sample.amount, 150.0)  # Absolute value.
        self.assertEqual(tx_sample.subcategory, "Dining")


class TestExtractRecommendationsFromAdvice(unittest.TestCase):
    """Tests for extract_recommendations_from_advice function."""

    def test_extracts_recommendations_from_valid_json(self) -> None:
        """Should extract recommendations list from valid JSON."""
        advice_text = json.dumps(
            {
                "analysis": "Test",
                "recommendations": ["Rec 1", "Rec 2", "Rec 3"],
                "encouragement": "Good job!",
            }
        )

        result = advice_service.extract_recommendations_from_advice(advice_text)

        self.assertEqual(result, ["Rec 1", "Rec 2", "Rec 3"])

    def test_returns_empty_list_for_invalid_json(self) -> None:
        """Should return empty list when JSON is invalid."""
        result = advice_service.extract_recommendations_from_advice("not valid json {{{")

        self.assertEqual(result, [])

    def test_returns_empty_list_when_key_missing(self) -> None:
        """Should return empty list when recommendations key is missing."""
        advice_text = json.dumps({"analysis": "Test", "encouragement": "Good job!"})

        result = advice_service.extract_recommendations_from_advice(advice_text)

        self.assertEqual(result, [])

    def test_returns_empty_list_when_not_a_list(self) -> None:
        """Should return empty list when recommendations is not a list."""
        advice_text = json.dumps({"recommendations": "not a list"})

        result = advice_service.extract_recommendations_from_advice(advice_text)

        self.assertEqual(result, [])

    def test_converts_non_string_items_to_strings(self) -> None:
        """Should convert non-string items to strings."""
        advice_text = json.dumps({"recommendations": [1, 2.5, True, "text"]})

        result = advice_service.extract_recommendations_from_advice(advice_text)

        self.assertEqual(result, ["1", "2.5", "True", "text"])


class TestMonthToMonthDataWithNewFields(DatabaseTestCase):
    """Tests for month_to_month_data with transactions and past_advice fields."""

    def test_includes_past_advice_when_provided(self) -> None:
        """Should include past_advice in MonthData when provided."""
        month = _create_month(self.session)
        past_advice = ["Reduce spending", "Save more"]

        result = advice_service.month_to_month_data(month, past_advice)

        self.assertEqual(result.past_advice, ["Reduce spending", "Save more"])

    def test_past_advice_is_none_when_not_provided(self) -> None:
        """Should have None past_advice when not provided."""
        month = _create_month(self.session)

        result = advice_service.month_to_month_data(month)

        self.assertIsNone(result.past_advice)

    def test_includes_transactions_grouped_by_category(self) -> None:
        """Should include transactions grouped by category."""
        month = _create_month(self.session)
        _create_transaction(self.session, month, "Rent", -1200.0, "CORE", "Housing")
        _create_transaction(self.session, month, "Uber Eats", -45.0, "CHOICE", "Food Delivery")
        self.session.commit()
        self.session.refresh(month)

        result = advice_service.month_to_month_data(month)

        self.assertIsNotNone(result.transactions)
        assert result.transactions is not None
        self.assertEqual(len(result.transactions["CORE"]), 1)
        self.assertEqual(len(result.transactions["CHOICE"]), 1)
        self.assertEqual(result.transactions["CORE"][0].description, "Rent")
        self.assertEqual(result.transactions["CHOICE"][0].description, "Uber Eats")

    def test_handles_month_with_no_transactions(self) -> None:
        """Should handle month with empty transactions list."""
        month = _create_month(self.session)

        result = advice_service.month_to_month_data(month)

        self.assertIsNotNone(result.transactions)
        assert result.transactions is not None
        self.assertEqual(result.transactions["CORE"], [])
        self.assertEqual(result.transactions["CHOICE"], [])
        self.assertEqual(result.transactions["COMPOUND"], [])
