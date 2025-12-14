"""Integration tests for cashflow API endpoint."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction


class TestGetCashFlowEndpoint:
    """Tests for GET /api/months/cashflow endpoint."""

    def test_returns_200_with_valid_data(self, client: TestClient, db_session: Session) -> None:
        """Should return 200 with cashflow data for existing months."""
        month = Month(
            year=2025,
            month=10,
            total_income=5000.0,
            total_core=2000.0,
            total_choice=1000.0,
            total_compound=2000.0,
            score=3,
            score_label="Great",
        )
        db_session.add(month)
        db_session.commit()

        tx_income = Transaction(
            month_id=month.id,
            date=date(2025, 10, 1),
            description="Salary",
            amount=5000.0,
            money_map_type=MoneyMapType.INCOME.value,
            money_map_subcategory="Job",
        )
        tx_core = Transaction(
            month_id=month.id,
            date=date(2025, 10, 5),
            description="Rent",
            amount=-1200.0,
            money_map_type=MoneyMapType.CORE.value,
            money_map_subcategory="Housing",
        )
        tx_choice = Transaction(
            month_id=month.id,
            date=date(2025, 10, 10),
            description="Restaurant",
            amount=-150.0,
            money_map_type=MoneyMapType.CHOICE.value,
            money_map_subcategory="Dining out",
        )
        db_session.add_all([tx_income, tx_core, tx_choice])
        db_session.commit()

        response = client.get("/api/months/cashflow")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "period_months" in data
        assert data["data"]["income_total"] == 5000.0
        assert data["data"]["core_total"] == 1200.0
        assert data["data"]["choice_total"] == 150.0
        assert len(data["data"]["core_breakdown"]) == 1
        assert len(data["data"]["choice_breakdown"]) == 1

    def test_months_zero_fetches_all_months(self, client: TestClient, db_session: Session) -> None:
        """Should return all months when months=0."""
        for m in range(1, 13):
            month = Month(year=2025, month=m, score=3, score_label="Great")
            db_session.add(month)
            db_session.commit()

            tx = Transaction(
                month_id=month.id,
                date=date(2025, m, 1),
                description="Salary",
                amount=5000.0,
                money_map_type=MoneyMapType.INCOME.value,
                money_map_subcategory="Job",
            )
            db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/cashflow", params={"months": 0})

        assert response.status_code == 200
        data = response.json()
        assert data["period_months"] == 0
        assert data["data"]["income_total"] == 60000.0

    def test_deficit_calculation_when_spending_exceeds_income(self, client: TestClient, db_session: Session) -> None:
        """Should calculate deficit when Core + Choice > Income."""
        month = Month(year=2025, month=10, score=0, score_label="Poor")
        db_session.add(month)
        db_session.commit()

        db_session.add(
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 1),
                description="Salary",
                amount=3000.0,
                money_map_type=MoneyMapType.INCOME.value,
                money_map_subcategory="Job",
            )
        )
        db_session.add(
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 5),
                description="Rent",
                amount=-2500.0,
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Housing",
            )
        )
        db_session.add(
            Transaction(
                month_id=month.id,
                date=date(2025, 10, 10),
                description="Shopping",
                amount=-1000.0,
                money_map_type=MoneyMapType.CHOICE.value,
                money_map_subcategory="Fancy clothing",
            )
        )
        db_session.commit()

        response = client.get("/api/months/cashflow")

        assert response.status_code == 200
        data = response.json()
        # Income=3000, Core=2500, Choice=1000. Deficit = 2500+1000-3000 = 500
        assert data["data"]["income_total"] == 3000.0
        assert data["data"]["core_total"] == 2500.0
        assert data["data"]["choice_total"] == 1000.0
        assert data["data"]["deficit"] == 500.0
        assert data["data"]["compound_total"] == 0.0

    def test_empty_response_when_no_months_exist(self, client: TestClient) -> None:
        """Should return empty data when no months exist."""
        response = client.get("/api/months/cashflow")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["income_total"] == 0.0
        assert data["data"]["core_total"] == 0.0
        assert data["data"]["choice_total"] == 0.0
        assert data["data"]["compound_total"] == 0.0
        assert data["data"]["deficit"] == 0.0
        assert data["data"]["core_breakdown"] == []
        assert data["data"]["choice_breakdown"] == []
        assert data["data"]["compound_breakdown"] == []
