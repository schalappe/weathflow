"""Integration tests for months API endpoints."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction


class TestListMonthsEndpoint:
    """Tests for GET /api/months endpoint."""

    def test_returns_list_with_correct_structure(self, client: TestClient, db_session: Session) -> None:
        """Should return list of months with correct response structure."""
        month = Month(
            year=2025,
            month=10,
            total_income=5000.0,
            total_core=2000.0,
            total_choice=1000.0,
            total_compound=2000.0,
            core_percentage=40.0,
            choice_percentage=20.0,
            compound_percentage=40.0,
            score=3,
            score_label="Great",
        )
        db_session.add(month)
        db_session.commit()

        # ##>: Add a transaction to verify transaction_count.
        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 1),
            description="Salary",
            amount=5000.0,
            money_map_type=MoneyMapType.INCOME.value,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months")

        assert response.status_code == 200
        data = response.json()
        assert "months" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["months"]) == 1

        month_data = data["months"][0]
        assert month_data["year"] == 2025
        assert month_data["month"] == 10
        assert month_data["score"] == 3
        assert month_data["score_label"] == "Great"
        assert month_data["transaction_count"] == 1

    def test_returns_empty_list_when_no_months(self, client: TestClient) -> None:
        """Should return empty list when no months exist."""
        response = client.get("/api/months")

        assert response.status_code == 200
        data = response.json()
        assert data["months"] == []
        assert data["total"] == 0


class TestGetMonthDetailEndpoint:
    """Tests for GET /api/months/{year}/{month} endpoint."""

    def test_returns_404_when_not_found(self, client: TestClient) -> None:
        """Should return 404 when month does not exist."""
        response = client.get("/api/months/2025/10")

        assert response.status_code == 404
        assert "2025-10" in response.json()["detail"]

    def test_returns_paginated_transactions(self, client: TestClient, db_session: Session) -> None:
        """Should return month detail with paginated transactions."""
        month = Month(
            year=2025,
            month=10,
            total_income=5000.0,
            total_core=2000.0,
            total_choice=1000.0,
            total_compound=2000.0,
            core_percentage=40.0,
            choice_percentage=20.0,
            compound_percentage=40.0,
            score=3,
            score_label="Great",
        )
        db_session.add(month)
        db_session.commit()

        # ##>: Add multiple transactions.
        for i in range(5):
            tx = Transaction(
                month_id=month.id,
                date=date(2025, 10, i + 1),
                description=f"Transaction {i + 1}",
                amount=100.0 * (i + 1),
                money_map_type=MoneyMapType.CORE.value,
            )
            db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10", params={"page": 1, "page_size": 2})

        assert response.status_code == 200
        data = response.json()

        # ##>: Verify month data.
        assert data["month"]["year"] == 2025
        assert data["month"]["month"] == 10
        assert data["month"]["transaction_count"] == 5

        # ##>: Verify pagination.
        assert len(data["transactions"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2
        assert data["pagination"]["total_items"] == 5
        assert data["pagination"]["total_pages"] == 3

    def test_filters_by_category(self, client: TestClient, db_session: Session) -> None:
        """Should filter transactions by category query parameter."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        # ##>: Add transactions with different categories.
        tx_income = Transaction(
            month_id=month.id,
            date=date(2025, 10, 1),
            description="Salary",
            amount=5000.0,
            money_map_type=MoneyMapType.INCOME.value,
        )
        tx_core = Transaction(
            month_id=month.id,
            date=date(2025, 10, 5),
            description="Rent",
            amount=-1500.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        tx_choice = Transaction(
            month_id=month.id,
            date=date(2025, 10, 10),
            description="Restaurant",
            amount=-50.0,
            money_map_type=MoneyMapType.CHOICE.value,
        )
        db_session.add_all([tx_income, tx_core, tx_choice])
        db_session.commit()

        response = client.get("/api/months/2025/10", params={"category": "CORE"})

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_items"] == 1
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["money_map_type"] == "CORE"

    def test_invalid_month_returns_422(self, client: TestClient) -> None:
        """Should return 422 for invalid month number (> 12)."""
        response = client.get("/api/months/2025/13")

        assert response.status_code == 422

    def test_invalid_category_is_silently_ignored(self, client: TestClient, db_session: Session) -> None:
        """Should ignore invalid category values and return all transactions."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 1),
            description="Test",
            amount=100.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        db_session.add(tx)
        db_session.commit()

        # ##>: Invalid category should be silently ignored.
        response = client.get("/api/months/2025/10", params={"category": "INVALID_TYPE"})

        assert response.status_code == 200
        data = response.json()
        # ##>: With only invalid categories, no filter is applied.
        assert data["pagination"]["total_items"] == 1

    def test_search_filter(self, client: TestClient, db_session: Session) -> None:
        """Should filter transactions by search query parameter."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx1 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 1),
            description="SALARY FROM COMPANY",
            amount=5000.0,
            money_map_type=MoneyMapType.INCOME.value,
        )
        tx2 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 5),
            description="CARREFOUR GROCERIES",
            amount=-150.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        response = client.get("/api/months/2025/10", params={"search": "carrefour"})

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_items"] == 1
        assert "CARREFOUR" in data["transactions"][0]["description"]

    def test_returns_404_with_contextual_message(self, client: TestClient) -> None:
        """Should return 404 with contextual error message including year and month."""
        response = client.get("/api/months/2025/10")

        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "2025-10" in detail
        assert "upload" in detail.lower()

    def test_date_range_filter(self, client: TestClient, db_session: Session) -> None:
        """Should filter transactions by start_date and end_date query parameters."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        # ##>: Add transactions on different days.
        for day in [1, 10, 20, 30]:
            tx = Transaction(
                month_id=month.id,
                date=date(2025, 10, day),
                description=f"Transaction on {day}th",
                amount=100.0,
                money_map_type=MoneyMapType.CORE.value,
            )
            db_session.add(tx)
        db_session.commit()

        response = client.get(
            "/api/months/2025/10",
            params={"start_date": "2025-10-05", "end_date": "2025-10-25"},
        )

        assert response.status_code == 200
        data = response.json()
        # ##>: Only transactions on 10th and 20th should match.
        assert data["pagination"]["total_items"] == 2

    def test_invalid_date_range_returns_400(self, client: TestClient, db_session: Session) -> None:
        """Should return 400 when start_date is after end_date."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get(
            "/api/months/2025/10",
            params={"start_date": "2025-10-20", "end_date": "2025-10-05"},
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "start_date" in detail
        assert "end_date" in detail

    def test_combined_filters(self, client: TestClient, db_session: Session) -> None:
        """Should apply multiple filters with AND logic via query parameters."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx1 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 5),
            description="GROCERY STORE",
            amount=-100.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        tx2 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="GROCERY MARKET",
            amount=-50.0,
            money_map_type=MoneyMapType.CHOICE.value,
        )
        tx3 = Transaction(
            month_id=month.id,
            date=date(2025, 10, 25),
            description="RESTAURANT",
            amount=-80.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        db_session.add_all([tx1, tx2, tx3])
        db_session.commit()

        # ##>: Filter by CORE category AND "grocery" search.
        response = client.get(
            "/api/months/2025/10",
            params={"category": "CORE", "search": "grocery"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_items"] == 1
        assert data["transactions"][0]["description"] == "GROCERY STORE"

    def test_returns_empty_transactions_for_month_with_no_transactions(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Should return month detail with empty transactions when month has no transactions."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10")

        assert response.status_code == 200
        data = response.json()
        assert data["month"]["transaction_count"] == 0
        assert data["transactions"] == []
        assert data["pagination"]["total_items"] == 0
        assert data["pagination"]["total_pages"] == 0

    def test_returns_empty_transactions_when_page_exceeds_total(self, client: TestClient, db_session: Session) -> None:
        """Should return empty transaction list when page number exceeds available pages."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        # ##>: Add only 2 transactions.
        for i in range(2):
            tx = Transaction(
                month_id=month.id,
                date=date(2025, 10, i + 1),
                description=f"Transaction {i + 1}",
                amount=100.0,
                money_map_type=MoneyMapType.CORE.value,
            )
            db_session.add(tx)
        db_session.commit()

        # ##>: Request page 10 with page_size=2 (only 1 page exists).
        response = client.get("/api/months/2025/10", params={"page": 10, "page_size": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 0
        assert data["pagination"]["total_items"] == 2
        assert data["pagination"]["total_pages"] == 1
