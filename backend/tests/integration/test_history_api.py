"""Integration tests for history API endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.month import Month
from app.services.exceptions import MonthQueryError


class TestGetHistoryEndpoint:
    """Tests for GET /api/months/history endpoint."""

    def test_history_returns_correct_months_count(self, client: TestClient, db_session: Session) -> None:
        """Should return the requested number of months."""
        # ##>: Create 6 months.
        for i in range(1, 7):
            month = Month(
                year=2025,
                month=i,
                total_income=1000.0,
                total_core=500.0,
                total_choice=300.0,
                total_compound=200.0,
                core_percentage=50.0,
                choice_percentage=30.0,
                compound_percentage=20.0,
                score=i % 4,
                score_label="Okay",
            )
            db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/history", params={"months": 3})

        assert response.status_code == 200
        data = response.json()
        assert len(data["months"]) == 3
        assert data["summary"]["total_months"] == 3

    def test_history_chronological_order(self, client: TestClient, db_session: Session) -> None:
        """Should return months in chronological order (oldest first)."""
        # ##>: Create months in non-chronological order.
        month_oct = Month(year=2025, month=10, score=3, score_label="Great")
        month_jan = Month(year=2025, month=1, score=2, score_label="Okay")
        month_jul = Month(year=2025, month=7, score=1, score_label="Need Improvement")
        db_session.add_all([month_oct, month_jan, month_jul])
        db_session.commit()

        response = client.get("/api/months/history", params={"months": 12})

        assert response.status_code == 200
        data = response.json()
        months = data["months"]

        # ##>: Should be sorted: Jan, Jul, Oct.
        assert months[0]["month"] == 1
        assert months[1]["month"] == 7
        assert months[2]["month"] == 10

    def test_history_default_limit_is_12(self, client: TestClient, db_session: Session) -> None:
        """Should return 12 months by default when no param provided."""
        # ##>: Create 15 months.
        for i in range(1, 16):
            year = 2024 if i <= 3 else 2025
            month_num = i if i <= 3 else i - 3
            month = Month(year=year, month=month_num, score=2, score_label="Okay")
            db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/history")

        assert response.status_code == 200
        data = response.json()
        # ##>: Default limit is 12.
        assert len(data["months"]) == 12

    def test_history_max_limit_24(self, client: TestClient, db_session: Session) -> None:
        """Should return 422 when months > 24."""
        response = client.get("/api/months/history", params={"months": 25})

        assert response.status_code == 422

    def test_history_empty_database(self, client: TestClient) -> None:
        """Should return empty response when no months exist."""
        response = client.get("/api/months/history")

        assert response.status_code == 200
        data = response.json()
        assert data["months"] == []
        assert data["summary"]["total_months"] == 0
        assert data["summary"]["average_score"] == 0.0
        assert data["summary"]["score_trend"] == "stable"
        assert data["summary"]["best_month"] is None
        assert data["summary"]["worst_month"] is None

    def test_history_summary_structure(self, client: TestClient, db_session: Session) -> None:
        """Should return correctly structured summary with all fields."""
        # ##>: Create enough months for trend calculation.
        scores = [1, 1, 1, 3, 3, 3]  # Previous avg=1, Recent avg=3 -> improving.
        for i, score in enumerate(scores, start=1):
            month = Month(
                year=2025,
                month=i,
                total_income=1000.0,
                total_core=500.0,
                total_choice=300.0,
                total_compound=200.0,
                core_percentage=50.0,
                choice_percentage=30.0,
                compound_percentage=20.0,
                score=score,
                score_label="Okay" if score < 3 else "Great",
            )
            db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/history", params={"months": 12})

        assert response.status_code == 200
        data = response.json()
        summary = data["summary"]

        assert summary["total_months"] == 6
        assert summary["average_score"] == 2.0
        assert summary["score_trend"] == "improving"
        assert summary["best_month"] is not None
        assert summary["worst_month"] is not None
        # ##>: Best month should be most recent with score 3 (month 6).
        assert summary["best_month"]["month"] == 6
        assert summary["best_month"]["score"] == 3
        # ##>: Worst month should be most recent with score 1 (month 3).
        assert summary["worst_month"]["month"] == 3
        assert summary["worst_month"]["score"] == 1

    def test_history_returns_503_on_database_error(self, client: TestClient) -> None:
        """Should return 503 when database query fails."""
        with patch(
            "app.services.months.get_months_history",
            side_effect=MonthQueryError("Connection refused"),
        ):
            response = client.get("/api/months/history")

        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]

    def test_history_min_limit_1(self, client: TestClient) -> None:
        """Should return 422 when months < 1."""
        response = client.get("/api/months/history", params={"months": 0})

        assert response.status_code == 422

    def test_history_cross_year_boundary_order(self, client: TestClient, db_session: Session) -> None:
        """Should correctly order months spanning year boundary."""
        # ##>: Create months in non-chronological order across year boundary.
        month_dec = Month(year=2024, month=12, score=2, score_label="Okay")
        month_jan = Month(year=2025, month=1, score=3, score_label="Great")
        month_feb = Month(year=2025, month=2, score=1, score_label="Need Improvement")
        db_session.add_all([month_jan, month_dec, month_feb])  # Add out of order
        db_session.commit()

        response = client.get("/api/months/history", params={"months": 12})

        assert response.status_code == 200
        data = response.json()
        months = data["months"]

        # ##>: Should be: Dec 2024, Jan 2025, Feb 2025.
        assert months[0]["year"] == 2024
        assert months[0]["month"] == 12
        assert months[1]["year"] == 2025
        assert months[1]["month"] == 1
        assert months[2]["year"] == 2025
        assert months[2]["month"] == 2
