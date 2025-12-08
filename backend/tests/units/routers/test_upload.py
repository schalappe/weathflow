"""Unit tests for upload router endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.exceptions import (
    CategorizationError,
    InvalidFormatError,
    InvalidMonthFormatError,
    MissingColumnsError,
)

# ##>: Create test client.
client = TestClient(app)


class TestUploadEndpoint:
    """Tests for POST /api/upload endpoint."""

    @patch("app.routers.upload.UploadService")
    def test_valid_csv_returns_200_with_summaries(self, mock_service_class: MagicMock) -> None:
        """Valid CSV upload returns 200 with month summaries."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_upload_preview.return_value = {
            "success": True,
            "total_transactions": 5,
            "months_detected": [
                {
                    "year": 2025,
                    "month": 1,
                    "transaction_count": 5,
                    "total_income": 3000.0,
                    "total_expenses": 500.0,
                }
            ],
            "preview_by_month": {
                "2025-01": [
                    {"date": "2025-01-15", "description": "Salary", "amount": 3000.0},
                ]
            },
        }

        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", b"csv content", "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_transactions"] == 5
        assert len(data["months_detected"]) == 1
        assert data["months_detected"][0]["year"] == 2025

    @patch("app.routers.upload.UploadService")
    def test_invalid_csv_format_returns_400(self, mock_service_class: MagicMock) -> None:
        """Invalid CSV format returns 400."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_upload_preview.side_effect = InvalidFormatError("File is empty")

        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", b"", "text/csv")},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @patch("app.routers.upload.UploadService")
    def test_missing_columns_returns_400(self, mock_service_class: MagicMock) -> None:
        """Missing required columns returns 400."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_upload_preview.side_effect = MissingColumnsError(["Date", "Montant"])

        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", b"invalid;headers", "text/csv")},
        )

        assert response.status_code == 400
        assert "Missing" in response.json()["detail"]


class TestCategorizeEndpoint:
    """Tests for POST /api/categorize endpoint."""

    @patch("app.routers.upload.UploadService")
    @patch("app.routers.upload.get_db")
    def test_valid_request_returns_200_with_results(
        self, mock_get_db: MagicMock, mock_service_class: MagicMock
    ) -> None:
        """Valid categorize request returns 200 with month results."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process_categorization.return_value = {
            "success": True,
            "months_processed": [
                {
                    "year": 2025,
                    "month": 1,
                    "transactions_categorized": 10,
                    "low_confidence_count": 2,
                    "score": 2,
                    "score_label": "Okay",
                }
            ],
            "total_api_calls": 1,
        }

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", b"csv content", "text/csv")},
            params={"months_to_process": "2025-01", "import_mode": "replace"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["months_processed"]) == 1
        assert data["months_processed"][0]["score"] == 2
        assert data["total_api_calls"] == 1

    @patch("app.routers.upload.UploadService")
    @patch("app.routers.upload.get_db")
    def test_invalid_month_format_returns_400(self, mock_get_db: MagicMock, mock_service_class: MagicMock) -> None:
        """Invalid month format returns 400."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process_categorization.side_effect = InvalidMonthFormatError("2025-13")

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", b"csv content", "text/csv")},
            params={"months_to_process": "2025-13", "import_mode": "replace"},
        )

        assert response.status_code == 400
        assert "Invalid month format" in response.json()["detail"]

    def test_invalid_import_mode_returns_422(self) -> None:
        """Invalid import mode returns 422 (Pydantic validation)."""
        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", b"csv content", "text/csv")},
            params={"months_to_process": "2025-01", "import_mode": "invalid"},
        )

        assert response.status_code == 422

    @patch("app.routers.upload.UploadService")
    @patch("app.routers.upload.get_db")
    def test_claude_api_error_returns_502(self, mock_get_db: MagicMock, mock_service_class: MagicMock) -> None:
        """Claude API error returns 502."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process_categorization.side_effect = CategorizationError("API failed")

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", b"csv content", "text/csv")},
            params={"months_to_process": "2025-01", "import_mode": "replace"},
        )

        assert response.status_code == 502
        assert "unavailable" in response.json()["detail"].lower()

    @patch("app.routers.upload.UploadService")
    @patch("app.routers.upload.get_db")
    def test_all_months_selection(self, mock_get_db: MagicMock, mock_service_class: MagicMock) -> None:
        """months_to_process='all' processes all months."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process_categorization.return_value = {
            "success": True,
            "months_processed": [
                {
                    "year": 2025,
                    "month": 1,
                    "transactions_categorized": 5,
                    "low_confidence_count": 0,
                    "score": 3,
                    "score_label": "Great",
                },
                {
                    "year": 2025,
                    "month": 2,
                    "transactions_categorized": 3,
                    "low_confidence_count": 1,
                    "score": 2,
                    "score_label": "Okay",
                },
            ],
            "total_api_calls": 1,
        }

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", b"csv content", "text/csv")},
            params={"months_to_process": "all", "import_mode": "replace"},
        )

        assert response.status_code == 200
        # ##>: Verify service was called with ["all"].
        mock_service.process_categorization.assert_called_once()
        call_args = mock_service.process_categorization.call_args
        assert call_args.kwargs["months_to_process"] == ["all"]

    @patch("app.routers.upload.UploadService")
    @patch("app.routers.upload.get_db")
    def test_comma_separated_months(self, mock_get_db: MagicMock, mock_service_class: MagicMock) -> None:
        """Comma-separated months are parsed correctly."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process_categorization.return_value = {
            "success": True,
            "months_processed": [],
            "total_api_calls": 0,
        }

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", b"csv content", "text/csv")},
            params={"months_to_process": "2025-01,2025-02,2025-03", "import_mode": "merge"},
        )

        assert response.status_code == 200
        call_args = mock_service.process_categorization.call_args
        assert call_args.kwargs["months_to_process"] == ["2025-01", "2025-02", "2025-03"]
