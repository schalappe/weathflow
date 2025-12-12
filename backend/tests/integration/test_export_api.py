"""Integration tests for export API endpoints."""

import csv
from datetime import date
from io import StringIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.exceptions import TransactionQueryError


class TestExportJsonEndpoint:
    """Tests for GET /api/months/{year}/{month}/export/json endpoint."""

    def test_returns_valid_json_structure(self, client: TestClient, db_session: Session) -> None:
        """Should return valid JSON with correct structure."""
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

        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 200
        data = response.json()

        # ##>: Verify top-level structure.
        assert "exported_at" in data
        assert "month" in data
        assert "transactions" in data
        assert "transaction_count" in data

        # ##>: Verify month data.
        assert data["month"]["year"] == 2025
        assert data["month"]["month"] == 10
        assert data["month"]["score"] == 3
        assert data["month"]["score_label"] == "Great"
        assert data["transaction_count"] == 0

    def test_includes_all_transactions(self, client: TestClient, db_session: Session) -> None:
        """Should include all transactions in export (no pagination)."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        # ##>: Add multiple transactions.
        for i in range(5):
            tx = Transaction(
                month_id=month.id,
                date=date(2025, 10, i + 1),
                description=f"Transaction {i + 1}",
                amount=100.0 * (i + 1),
                account="Main Account",
                bankin_category="Test Category",
                bankin_subcategory="Test Subcategory",
                money_map_type=MoneyMapType.CORE.value,
                money_map_subcategory="Groceries",
                is_manually_corrected=False,
            )
            db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_count"] == 5
        assert len(data["transactions"]) == 5

    def test_includes_month_summary(self, client: TestClient, db_session: Session) -> None:
        """Should include all month summary fields."""
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

        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 200
        data = response.json()

        month_data = data["month"]
        assert month_data["total_income"] == 5000.0
        assert month_data["total_core"] == 2000.0
        assert month_data["total_choice"] == 1000.0
        assert month_data["total_compound"] == 2000.0
        assert month_data["core_percentage"] == 40.0
        assert month_data["choice_percentage"] == 20.0
        assert month_data["compound_percentage"] == 40.0

    def test_returns_404_for_missing_month(self, client: TestClient) -> None:
        """Should return 404 when month does not exist."""
        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 404
        assert "2025-10" in response.json()["detail"]

    def test_content_disposition_header(self, client: TestClient, db_session: Session) -> None:
        """Should set Content-Disposition header with correct filename."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        assert response.headers["Content-Disposition"] == "attachment; filename=moneymap-2025-10.json"

    def test_content_type_header(self, client: TestClient, db_session: Session) -> None:
        """Should set correct Content-Type header."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 200
        assert "application/json" in response.headers["Content-Type"]

    def test_transaction_fields_are_complete(self, client: TestClient, db_session: Session) -> None:
        """Should include all transaction fields in export."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="CB Carrefour",
            amount=-125.50,
            account="Main Account",
            bankin_category="Alimentation",
            bankin_subcategory="Supermarchés",
            money_map_type=MoneyMapType.CORE.value,
            money_map_subcategory="Groceries",
            is_manually_corrected=True,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 200
        data = response.json()
        tx_data = data["transactions"][0]

        assert tx_data["date"] == "2025-10-15"
        assert tx_data["description"] == "CB Carrefour"
        assert tx_data["amount"] == -125.50
        assert tx_data["account"] == "Main Account"
        assert tx_data["bankin_category"] == "Alimentation"
        assert tx_data["bankin_subcategory"] == "Supermarchés"
        assert tx_data["money_map_type"] == "CORE"
        assert tx_data["money_map_subcategory"] == "Groceries"
        assert tx_data["is_manually_corrected"] is True

    def test_filename_format_with_single_digit_month(self, client: TestClient, db_session: Session) -> None:
        """Should zero-pad single-digit months in filename."""
        month = Month(year=2025, month=3, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/3/export/json")

        assert response.status_code == 200
        assert response.headers["Content-Disposition"] == "attachment; filename=moneymap-2025-03.json"


class TestExportCsvEndpoint:
    """Tests for GET /api/months/{year}/{month}/export/csv endpoint."""

    def test_returns_valid_csv_format(self, client: TestClient, db_session: Session) -> None:
        """Should return valid CSV with correct format."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test Transaction",
            amount=-100.0,
            account="Main",
            bankin_category="Test",
            bankin_subcategory="Sub",
            money_map_type=MoneyMapType.CORE.value,
            money_map_subcategory="Groceries",
            is_manually_corrected=False,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(StringIO(content), delimiter=";")
        rows = list(reader)

        # ##>: Header row + 1 data row.
        assert len(rows) == 2

    def test_has_correct_headers(self, client: TestClient, db_session: Session) -> None:
        """Should have correct CSV headers."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(StringIO(content), delimiter=";")
        headers = next(reader)

        expected_headers = [
            "Date",
            "Description",
            "Account",
            "Amount",
            "Bankin Category",
            "Bankin Subcategory",
            "Money Map Type",
            "Money Map Subcategory",
            "Manually Corrected",
        ]
        assert headers == expected_headers

    def test_uses_semicolon_delimiter(self, client: TestClient, db_session: Session) -> None:
        """Should use semicolon as delimiter."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test",
            amount=-100.0,
            money_map_type=MoneyMapType.CORE.value,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        # ##>: Count semicolons in header row (should be 8 for 9 columns).
        first_line = response.text.split("\n")[0]
        assert first_line.count(";") == 8

    def test_returns_404_for_missing_month(self, client: TestClient) -> None:
        """Should return 404 when month does not exist."""
        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 404
        assert "2025-10" in response.json()["detail"]

    def test_content_disposition_header(self, client: TestClient, db_session: Session) -> None:
        """Should set Content-Disposition header with correct filename."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        assert response.headers["Content-Disposition"] == "attachment; filename=moneymap-2025-10.csv"

    def test_content_type_header(self, client: TestClient, db_session: Session) -> None:
        """Should set correct Content-Type header."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]

    def test_includes_all_transactions(self, client: TestClient, db_session: Session) -> None:
        """Should include all transactions in export (no pagination)."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        for i in range(5):
            tx = Transaction(
                month_id=month.id,
                date=date(2025, 10, i + 1),
                description=f"Transaction {i + 1}",
                amount=100.0,
                money_map_type=MoneyMapType.CORE.value,
            )
            db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(StringIO(content), delimiter=";")
        rows = list(reader)

        # ##>: Header + 5 data rows.
        assert len(rows) == 6

    def test_transaction_data_values(self, client: TestClient, db_session: Session) -> None:
        """Should export correct transaction data values."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="CB Carrefour",
            amount=-125.50,
            account="Main Account",
            bankin_category="Alimentation",
            bankin_subcategory="Supermarchés",
            money_map_type=MoneyMapType.CORE.value,
            money_map_subcategory="Groceries",
            is_manually_corrected=True,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(StringIO(content), delimiter=";")
        next(reader)  # Skip header.
        row = next(reader)

        assert row[0] == "2025-10-15"
        assert row[1] == "CB Carrefour"
        assert row[2] == "Main Account"
        assert row[3] == "-125.5"
        assert row[4] == "Alimentation"
        assert row[5] == "Supermarchés"
        assert row[6] == "CORE"
        assert row[7] == "Groceries"
        assert row[8] == "true"

    def test_handles_null_values(self, client: TestClient, db_session: Session) -> None:
        """Should handle null values in transaction fields."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="Test",
            amount=-100.0,
            account=None,
            bankin_category=None,
            bankin_subcategory=None,
            money_map_type=None,
            money_map_subcategory=None,
            is_manually_corrected=False,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        # ##>: Should not raise an error when handling None values.

    def test_filename_format_with_single_digit_month(self, client: TestClient, db_session: Session) -> None:
        """Should zero-pad single-digit months in filename."""
        month = Month(year=2025, month=3, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/3/export/csv")

        assert response.status_code == 200
        assert response.headers["Content-Disposition"] == "attachment; filename=moneymap-2025-03.csv"

    def test_returns_only_headers_when_no_transactions(self, client: TestClient, db_session: Session) -> None:
        """Should return CSV with only headers when month has no transactions."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(StringIO(content), delimiter=";")
        rows = list(reader)

        # ##>: Only header row.
        assert len(rows) == 1

    def test_sanitizes_csv_injection_characters(self, client: TestClient, db_session: Session) -> None:
        """Should sanitize fields starting with =, +, -, @ to prevent CSV injection."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        # ##>: Create transaction with potentially dangerous description.
        tx = Transaction(
            month_id=month.id,
            date=date(2025, 10, 15),
            description="=1+1",
            amount=-100.0,
            account="+DANGEROUS",
            bankin_category="-Malicious",
            bankin_subcategory="@Formula",
            money_map_type=MoneyMapType.CORE.value,
            money_map_subcategory="Normal",
            is_manually_corrected=False,
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(StringIO(content), delimiter=";")
        next(reader)  # Skip header.
        row = next(reader)

        # ##>: Dangerous characters should be prefixed with single quote.
        assert row[1] == "'=1+1"
        assert row[2] == "'+DANGEROUS"
        assert row[4] == "'-Malicious"
        assert row[5] == "'@Formula"
        # ##>: Normal subcategory should not be prefixed.
        assert row[7] == "Normal"


class TestExportValidation:
    """Tests for export endpoint validation (422 responses)."""

    def test_json_invalid_month_above_12_returns_422(self, client: TestClient) -> None:
        """Should return 422 for month number greater than 12."""
        response = client.get("/api/months/2025/13/export/json")

        assert response.status_code == 422

    def test_json_invalid_month_below_1_returns_422(self, client: TestClient) -> None:
        """Should return 422 for month number less than 1."""
        response = client.get("/api/months/2025/0/export/json")

        assert response.status_code == 422

    def test_json_invalid_year_below_2000_returns_422(self, client: TestClient) -> None:
        """Should return 422 for year below valid range."""
        response = client.get("/api/months/1999/10/export/json")

        assert response.status_code == 422

    def test_json_invalid_year_above_2100_returns_422(self, client: TestClient) -> None:
        """Should return 422 for year above valid range."""
        response = client.get("/api/months/2101/10/export/json")

        assert response.status_code == 422

    def test_csv_invalid_month_above_12_returns_422(self, client: TestClient) -> None:
        """Should return 422 for month number greater than 12."""
        response = client.get("/api/months/2025/13/export/csv")

        assert response.status_code == 422

    def test_csv_invalid_month_below_1_returns_422(self, client: TestClient) -> None:
        """Should return 422 for month number less than 1."""
        response = client.get("/api/months/2025/0/export/csv")

        assert response.status_code == 422

    def test_csv_invalid_year_below_2000_returns_422(self, client: TestClient) -> None:
        """Should return 422 for year below valid range."""
        response = client.get("/api/months/1999/10/export/csv")

        assert response.status_code == 422

    def test_csv_invalid_year_above_2100_returns_422(self, client: TestClient) -> None:
        """Should return 422 for year above valid range."""
        response = client.get("/api/months/2101/10/export/csv")

        assert response.status_code == 422


class TestExportDatabaseErrors:
    """Tests for export endpoint database error handling (503 responses)."""

    def test_json_returns_503_on_database_error(self, client: TestClient, db_session: Session) -> None:
        """Should return 503 when database query fails during JSON export."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        with patch(
            "app.services.export.months_service.get_all_transactions_for_month",
            side_effect=TransactionQueryError(month.id, "Connection refused"),
        ):
            response = client.get("/api/months/2025/10/export/json")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    def test_csv_returns_503_on_database_error(self, client: TestClient, db_session: Session) -> None:
        """Should return 503 when database query fails during CSV export."""
        month = Month(year=2025, month=10, score=3, score_label="Great")
        db_session.add(month)
        db_session.commit()

        with patch(
            "app.services.export.months_service.get_all_transactions_for_month",
            side_effect=TransactionQueryError(month.id, "Connection refused"),
        ):
            response = client.get("/api/months/2025/10/export/csv")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
