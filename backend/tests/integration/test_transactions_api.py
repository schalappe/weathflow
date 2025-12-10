"""Integration tests for PATCH /api/transactions/{id} endpoint."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction


def _create_month_with_transaction(db: Session) -> tuple[Month, Transaction]:
    """Create a month with a test transaction for integration testing."""
    month = Month(
        year=2025,
        month=1,
        total_income=1000.0,
        total_core=500.0,
        total_choice=300.0,
        total_compound=200.0,
        core_percentage=50.0,
        choice_percentage=30.0,
        compound_percentage=20.0,
        score=3,
        score_label="Great",
    )
    db.add(month)
    db.flush()

    transaction = Transaction(
        month_id=month.id,
        date=date(2025, 1, 15),
        description="Test Transaction",
        amount=-50.0,
        money_map_type=MoneyMapType.CHOICE.value,
        money_map_subcategory="Dining out",
        is_manually_corrected=False,
    )
    db.add(transaction)
    db.commit()

    return month, transaction


class TestUpdateTransactionEndpoint:
    """Tests for PATCH /api/transactions/{transaction_id} endpoint."""

    def test_valid_update_returns_200_with_updated_data(self, client: TestClient, db_session: Session) -> None:
        """Valid update returns 200 with updated transaction data."""
        _, transaction = _create_month_with_transaction(db_session)

        response = client.patch(
            f"/api/transactions/{transaction.id}",
            json={
                "money_map_type": "CORE",
                "money_map_subcategory": "Groceries",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["transaction"]["money_map_type"] == "CORE"
        assert data["transaction"]["money_map_subcategory"] == "Groceries"
        assert data["transaction"]["is_manually_corrected"] is True

    def test_nonexistent_transaction_returns_404(self, client: TestClient, db_session: Session) -> None:
        """Non-existent transaction ID returns 404 error."""
        _create_month_with_transaction(db_session)

        response = client.patch(
            "/api/transactions/99999",
            json={
                "money_map_type": "CORE",
                "money_map_subcategory": "Groceries",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "99999" in data["detail"]

    def test_invalid_category_type_returns_400(self, client: TestClient, db_session: Session) -> None:
        """Invalid MoneyMapType returns 400 validation error."""
        _, transaction = _create_month_with_transaction(db_session)

        response = client.patch(
            f"/api/transactions/{transaction.id}",
            json={
                "money_map_type": "INVALID_TYPE",
                "money_map_subcategory": "Groceries",
            },
        )

        assert response.status_code == 422

    def test_invalid_subcategory_returns_422(self, client: TestClient, db_session: Session) -> None:
        """Invalid subcategory for type returns 422 validation error."""
        _, transaction = _create_month_with_transaction(db_session)

        response = client.patch(
            f"/api/transactions/{transaction.id}",
            json={
                "money_map_type": "CORE",
                "money_map_subcategory": "Invalid Subcategory",
            },
        )

        # ##>: Pydantic model validation returns 422 (FastAPI convention for validation errors).
        assert response.status_code == 422
        data = response.json()
        assert "Invalid subcategory" in str(data["detail"])

    def test_response_includes_recalculated_month_stats(self, client: TestClient, db_session: Session) -> None:
        """Response includes updated month statistics after recalculation."""
        month, transaction = _create_month_with_transaction(db_session)
        original_choice_pct = month.choice_percentage

        response = client.patch(
            f"/api/transactions/{transaction.id}",
            json={
                "money_map_type": "CORE",
                "money_map_subcategory": "Groceries",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # ##>: Verify month stats structure is included.
        assert "updated_month_stats" in data
        month_stats = data["updated_month_stats"]

        assert "id" in month_stats
        assert "year" in month_stats
        assert "month" in month_stats
        assert "total_income" in month_stats
        assert "total_core" in month_stats
        assert "total_choice" in month_stats
        assert "core_percentage" in month_stats
        assert "choice_percentage" in month_stats
        assert "score" in month_stats

        # ##>: Verify stats were recalculated (CHOICE expense moved to CORE).
        assert month_stats["choice_percentage"] != original_choice_pct
