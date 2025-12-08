"""Integration tests for upload and categorize API endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.services.exceptions import CategorizationError
from app.services.schemas.categorization import CategorizationResult
from tests.integration.fixtures.csv_builder import CSVBuilder, combine_csvs


def _create_mock_categorizer(money_map_types: list[MoneyMapType] | None = None) -> MagicMock:
    """
    Create a mock categorizer that returns deterministic results.

    Parameters
    ----------
    money_map_types : list[MoneyMapType] | None
        Types to assign to each transaction. If None, uses INCOME for all.

    Returns
    -------
    MagicMock
        Mock categorizer instance.
    """
    mock_categorizer = MagicMock()

    def categorize_side_effect(inputs):
        types = money_map_types or [MoneyMapType.INCOME] * len(inputs)
        return [
            CategorizationResult(
                id=i + 1,
                money_map_type=types[i % len(types)],
                money_map_subcategory="",
                confidence=0.95,
            )
            for i in range(len(inputs))
        ]

    mock_categorizer.categorize.side_effect = categorize_side_effect
    return mock_categorizer


class TestCategorizeReplaceMode:
    """Integration tests for replace mode categorization."""

    @patch("app.services.upload.TransactionCategorizer")
    def test_upload_categorize_creates_month_with_transactions(
        self, mock_categorizer_class, client: TestClient, db_session: Session
    ) -> None:
        """
        Full upload → categorize → verify database flow in replace mode.

        Verifies that:
        1. POST /api/categorize succeeds with 200
        2. Month record is created with correct year/month
        3. Transactions are persisted with correct Money Map types
        4. Score is calculated and returned
        """
        mock_categorizer_class.return_value = _create_mock_categorizer(
            [MoneyMapType.INCOME, MoneyMapType.CORE, MoneyMapType.CHOICE, MoneyMapType.COMPOUND]
        )

        csv = (
            CSVBuilder("2025-01")
            .add_income("Salary January", 3000)
            .add_grocery("CARREFOUR", 150)
            .add_dining("MCDONALDS", 25)
            .add_savings("Epargne mensuelle", 500)
            .build()
        )

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", csv, "text/csv")},
            params={"months_to_process": "2025-01", "import_mode": "replace"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["months_processed"]) == 1
        assert data["months_processed"][0]["transactions_categorized"] == 4
        assert data["total_api_calls"] >= 1

        # ##>: Verify database state.
        db_session.expire_all()
        month = db_session.query(Month).filter_by(year=2025, month=1).first()
        assert month is not None
        assert len(month.transactions) == 4
        assert month.total_income == 3000.0
        assert month.total_core == 150.0
        assert month.total_choice == 25.0
        # ##>: Compound is derived as income - core - choice (what remains after spending).
        assert month.total_compound == 3000.0 - 150.0 - 25.0
        assert month.score is not None

    @patch("app.services.upload.TransactionCategorizer")
    def test_replace_mode_deletes_existing_data(
        self, mock_categorizer_class, client: TestClient, db_session: Session
    ) -> None:
        """Replace mode deletes existing month data before import."""
        mock_categorizer_class.return_value = _create_mock_categorizer([MoneyMapType.INCOME])

        csv_first = CSVBuilder("2025-02").add_income("Old Salary", 2000).build()
        csv_second = CSVBuilder("2025-02").add_income("New Salary", 3500).build()

        # ##>: First upload.
        client.post(
            "/api/categorize",
            files={"file": ("first.csv", csv_first, "text/csv")},
            params={"months_to_process": "2025-02", "import_mode": "replace"},
        )

        # ##>: Second upload replaces first.
        response = client.post(
            "/api/categorize",
            files={"file": ("second.csv", csv_second, "text/csv")},
            params={"months_to_process": "2025-02", "import_mode": "replace"},
        )

        assert response.status_code == 200
        db_session.expire_all()
        month = db_session.query(Month).filter_by(year=2025, month=2).first()
        assert month.total_income == 3500.0
        assert len(month.transactions) == 1


class TestCategorizeMergeMode:
    """Integration tests for merge mode categorization."""

    @patch("app.services.upload.TransactionCategorizer")
    def test_merge_mode_skips_duplicate_transactions(
        self, mock_categorizer_class, client: TestClient, db_session: Session
    ) -> None:
        """
        Full upload → categorize → verify database flow in merge mode.

        Verifies that:
        1. First upload creates transactions
        2. Second upload with same data skips duplicates
        3. Total transaction count remains unchanged
        """
        mock_categorizer_class.return_value = _create_mock_categorizer([MoneyMapType.INCOME, MoneyMapType.CORE])

        csv = CSVBuilder("2025-03").add_income("Salary March", 3000).add_grocery("AUCHAN", 200).build()

        # ##>: First upload with replace mode.
        client.post(
            "/api/categorize",
            files={"file": ("test.csv", csv, "text/csv")},
            params={"months_to_process": "2025-03", "import_mode": "replace"},
        )

        # ##>: Second upload with merge mode (same data).
        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", csv, "text/csv")},
            params={"months_to_process": "2025-03", "import_mode": "merge"},
        )

        assert response.status_code == 200
        # ##>: No new transactions should be added (all duplicates).
        assert response.json()["months_processed"][0]["transactions_categorized"] == 0

        db_session.expire_all()
        month = db_session.query(Month).filter_by(year=2025, month=3).first()
        assert len(month.transactions) == 2

    @patch("app.services.upload.TransactionCategorizer")
    def test_merge_mode_adds_new_transactions(
        self, mock_categorizer_class, client: TestClient, db_session: Session
    ) -> None:
        """Merge mode adds new transactions while preserving existing ones."""
        mock_categorizer_class.return_value = _create_mock_categorizer([MoneyMapType.INCOME])

        csv_first = CSVBuilder("2025-04").add_income("Salary", 3000).build()

        # ##>: First upload.
        client.post(
            "/api/categorize",
            files={"file": ("first.csv", csv_first, "text/csv")},
            params={"months_to_process": "2025-04", "import_mode": "replace"},
        )

        # ##>: Reset mock for second upload with different type.
        mock_categorizer_class.return_value = _create_mock_categorizer([MoneyMapType.CORE])
        csv_second = CSVBuilder("2025-04").add_grocery("LIDL", 120).build()

        # ##>: Second upload merges new data.
        response = client.post(
            "/api/categorize",
            files={"file": ("second.csv", csv_second, "text/csv")},
            params={"months_to_process": "2025-04", "import_mode": "merge"},
        )

        assert response.status_code == 200
        assert response.json()["months_processed"][0]["transactions_categorized"] == 1

        db_session.expire_all()
        month = db_session.query(Month).filter_by(year=2025, month=4).first()
        assert len(month.transactions) == 2
        assert month.total_income == 3000.0
        assert month.total_core == 120.0


class TestMultiMonthProcessing:
    """Integration tests for multi-month file processing."""

    @patch("app.services.upload.TransactionCategorizer")
    def test_processes_all_months_in_csv(
        self, mock_categorizer_class, client: TestClient, db_session: Session
    ) -> None:
        """
        Multi-month file processing end-to-end.

        Verifies that months_to_process='all' processes every month in the CSV.
        """
        mock_categorizer_class.return_value = _create_mock_categorizer(
            [MoneyMapType.INCOME, MoneyMapType.CORE, MoneyMapType.CHOICE]
        )

        # ##>: Build CSV with two months of data.
        csv_june = CSVBuilder("2025-06").add_income("Salary Jun", 3000).add_grocery("CARREFOUR", 180).build()
        csv_july = CSVBuilder("2025-07").add_income("Salary Jul", 3100).add_dining("Restaurant", 45).build()
        combined = combine_csvs(csv_june, csv_july)

        response = client.post(
            "/api/categorize",
            files={"file": ("multi.csv", combined, "text/csv")},
            params={"months_to_process": "all", "import_mode": "replace"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["months_processed"]) == 2

        db_session.expire_all()
        months = db_session.query(Month).all()
        assert len(months) == 2

        june = db_session.query(Month).filter_by(year=2025, month=6).first()
        july = db_session.query(Month).filter_by(year=2025, month=7).first()
        assert june is not None
        assert july is not None


class TestPartialFailure:
    """Integration tests for partial success scenarios."""

    @patch("app.services.upload.TransactionCategorizer")
    def test_api_error_mid_processing(self, mock_categorizer_class, client: TestClient, db_session: Session) -> None:
        """
        Partial success: API error on second month while first succeeds.

        Simulates Claude API failing mid-processing. The request should fail
        with 502 when the second month's categorization fails.
        """
        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        call_count = [0]

        def categorize_side_effect(inputs):
            call_count[0] += 1
            if call_count[0] == 1:
                # ##>: First month succeeds.
                return [
                    CategorizationResult(
                        id=i + 1,
                        money_map_type=MoneyMapType.INCOME,
                        money_map_subcategory="",
                        confidence=0.95,
                    )
                    for i in range(len(inputs))
                ]
            else:
                # ##>: Second month fails.
                raise CategorizationError("Claude API unavailable")

        mock_categorizer.categorize.side_effect = categorize_side_effect

        # ##>: Build CSV with two months.
        csv_aug = CSVBuilder("2025-08").add_income("Salary Aug", 3000).build()
        csv_sep = CSVBuilder("2025-09").add_income("Salary Sep", 3100).build()
        combined = combine_csvs(csv_aug, csv_sep)

        response = client.post(
            "/api/categorize",
            files={"file": ("multi.csv", combined, "text/csv")},
            params={"months_to_process": "all", "import_mode": "replace"},
        )

        # ##>: Request fails because second month errored.
        assert response.status_code == 502
        assert "unavailable" in response.json()["detail"].lower()


class TestErrorHandling:
    """Integration tests for error handling scenarios."""

    @patch("app.services.upload.TransactionCategorizer")
    def test_claude_api_failure_returns_502(
        self, mock_categorizer_class, client: TestClient, db_session: Session
    ) -> None:
        """
        Claude API mock failure handling.

        When the categorization service fails, the endpoint should return 502.
        Note: The month record may still be created due to the replace mode flow
        (month is created before categorization), but no transactions are added.
        """
        mock_categorizer = MagicMock()
        mock_categorizer_class.return_value = mock_categorizer
        mock_categorizer.categorize.side_effect = CategorizationError("API connection failed")

        csv = CSVBuilder("2025-10").add_income("Salary", 3000).build()

        response = client.post(
            "/api/categorize",
            files={"file": ("test.csv", csv, "text/csv")},
            params={"months_to_process": "2025-10", "import_mode": "replace"},
        )

        assert response.status_code == 502
        assert "unavailable" in response.json()["detail"].lower()
