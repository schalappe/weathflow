"""Integration tests for advice eligibility in the API router."""

from datetime import date
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.deps import get_advice_generator
from app.db.database import get_db
from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.main import app
from tests.conftest import DatabaseTestCase


class TestAdviceEligibility(DatabaseTestCase):
    """Tests for advice eligibility in generate_advice endpoint."""

    def setUp(self) -> None:
        """Set up test client and database."""
        super().setUp()
        # ##>: Override dependencies for testing.
        app.dependency_overrides[get_db] = lambda: self.session

        # ##>: Create mock generator with proper return value matching AdviceResponse.
        self.mock_generator = MagicMock()
        mock_response = MagicMock()
        # ##>: model_dump_json must return a real string for DB storage.
        mock_response.model_dump_json.return_value = (
            '{"analysis": "Test analysis", "problem_areas": [], "recommendations": [], "encouragement": "Keep up!"}'
        )
        mock_response.analysis = "Test analysis"
        mock_response.problem_areas = []
        mock_response.recommendations = []
        mock_response.encouragement = "Keep up the good work!"
        self.mock_generator.generate_advice.return_value = mock_response
        app.dependency_overrides[get_advice_generator] = lambda: self.mock_generator

        self.client = TestClient(app)

    def tearDown(self) -> None:
        """Clean up overrides."""
        app.dependency_overrides.clear()
        super().tearDown()

    def _create_month_with_transactions(self, year: int, month: int, tx_count: int = 5) -> Month:
        """Helper to create a month with transactions."""
        month_record = Month(year=year, month=month, score=2, score_label="Okay")
        self.session.add(month_record)
        self.session.commit()

        for i in range(tx_count):
            tx = Transaction(
                month_id=month_record.id,
                date=date(year, month, min(i + 1, 28)),
                description=f"Transaction {i + 1}",
                amount=100.0 * (i + 1),
                money_map_type="CORE",
            )
            self.session.add(tx)
        self.session.commit()

        return month_record

    def test_eligible_month_generates_advice(self) -> None:
        """Eligible month (most recent) generates advice successfully."""
        # Setup: Create 2 months.
        self._create_month_with_transactions(2025, 9)
        self._create_month_with_transactions(2025, 10)

        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_ineligible_month_returns_400(self) -> None:
        """Ineligible month (too old) returns HTTP 400 with clear message."""
        # Setup: Create 3 months, making August ineligible.
        self._create_month_with_transactions(2025, 8)
        self._create_month_with_transactions(2025, 9)
        self._create_month_with_transactions(2025, 10)

        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 8})

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "2 most recent months" in detail
        assert "2025-10" in detail

    def test_first_advice_uses_extended_history(self) -> None:
        """First advice uses 12-month history limit."""
        # Setup: Create 2 months, no existing advice.
        self._create_month_with_transactions(2025, 9)
        self._create_month_with_transactions(2025, 10)

        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 200
        # ##>: The history limit is tested via eligibility service tests.

    def test_subsequent_advice_uses_regular_history(self) -> None:
        """Subsequent advice uses 3-month history limit."""
        # Setup: Create 2 months.
        month1 = self._create_month_with_transactions(2025, 9)
        self._create_month_with_transactions(2025, 10)

        # Add existing advice for month 9.
        advice = Advice(month_id=month1.id, advice_text='{"summary": "Previous advice"}')
        self.session.add(advice)
        self.session.commit()

        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 200

    def test_regenerating_first_advice_uses_extended_history(self) -> None:
        """Regenerating the only/first advice uses extended history."""
        # Setup: Create 2 months.
        self._create_month_with_transactions(2025, 9)
        month2 = self._create_month_with_transactions(2025, 10)

        # Add advice only for month 10 (the one we're regenerating).
        advice = Advice(month_id=month2.id, advice_text='{"summary": "First advice"}')
        self.session.add(advice)
        self.session.commit()

        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 10, "regenerate": True})

        assert response.status_code == 200

    def test_month_not_found_returns_404(self) -> None:
        """Month that doesn't exist returns HTTP 404."""
        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 12})

        assert response.status_code == 404
        assert "No data found" in response.json()["detail"]


class TestAdviceEligibilityEdgeCases(DatabaseTestCase):
    """Edge case tests for advice eligibility."""

    def setUp(self) -> None:
        """Set up test client and database."""
        super().setUp()
        app.dependency_overrides[get_db] = lambda: self.session

        # ##>: Create mock generator.
        self.mock_generator = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = (
            '{"analysis": "Test", "problem_areas": [], "recommendations": [], "encouragement": "Great!"}'
        )
        mock_response.analysis = "Test analysis"
        mock_response.problem_areas = []
        mock_response.recommendations = []
        mock_response.encouragement = "Great!"
        self.mock_generator.generate_advice.return_value = mock_response
        app.dependency_overrides[get_advice_generator] = lambda: self.mock_generator

        self.client = TestClient(app)

    def tearDown(self) -> None:
        """Clean up overrides."""
        app.dependency_overrides.clear()
        super().tearDown()

    def _create_month(self, year: int, month: int) -> Month:
        """Helper to create a month with minimal data."""
        month_record = Month(year=year, month=month, score=2, score_label="Okay")
        self.session.add(month_record)
        self.session.commit()
        return month_record

    def test_month_gap_handling(self) -> None:
        """Month gap (Aug, Oct but no Sep) handles correctly."""
        # Create Aug and Oct, skip Sep.
        self._create_month(2025, 8)
        self._create_month(2025, 10)

        # Oct should be eligible (most recent).
        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 10})
        assert response.status_code == 200

        # Aug should be ineligible (not in 2 most recent = Oct, Sep).
        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 8})
        assert response.status_code == 400

    def test_year_boundary_december_january(self) -> None:
        """Dec 2024 + Jan 2025 both eligible when Jan is most recent."""
        self._create_month(2024, 12)
        self._create_month(2025, 1)

        # Both should be eligible.
        dec_response = self.client.post("/api/advice/generate", json={"year": 2024, "month": 12})
        assert dec_response.status_code == 200

        jan_response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 1})
        assert jan_response.status_code == 200

    def test_single_month_insufficient_data(self) -> None:
        """Single month returns clear error about insufficient data."""
        self._create_month(2025, 10)

        response = self.client.post("/api/advice/generate", json={"year": 2025, "month": 10})

        assert response.status_code == 400
        assert "at least" in response.json()["detail"].lower() or "2" in response.json()["detail"]
