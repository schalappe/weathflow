"""Unit tests for advice router responses."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.main import app
from app.services.advice.eligibility import EligibilityResult

client = TestClient(app)


def _month() -> Month:
    """Build mocked month."""
    month = MagicMock(spec=Month)
    month.id = 1
    month.year = 2025
    month.month = 10
    return month


def _advice_text() -> str:
    """Build strict stored advice JSON."""
    return json.dumps(
        {
            "outputs": [
                {
                    "type": "unresolved",
                    "priority": "medium",
                    "conclusion": "La réserve liquide ne peut pas être conclue.",
                    "trace": {
                        "summary": "Les transactions ne donnent pas le solde disponible.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "Aucun solde de compte importé.",
                                    "period": "2025-10",
                                    "scope": "Transactions importées",
                                    "source": "observed_data",
                                }
                            ],
                            "calculations": [],
                            "conventions": [],
                            "limits": ["Solde non observé."],
                        },
                    },
                }
            ]
        }
    )


@patch("app.api.advice.check_eligibility")
@patch("app.api.advice.advice_service")
@patch("app.api.advice.months_service")
def test_get_returns_valid_cached_decision_output(
    months_service: MagicMock,
    advice_service: MagicMock,
    check_eligibility: MagicMock,
) -> None:
    """GET exposes cached decision output with validity state."""
    months_service.get_month_by_year_month.return_value = _month()
    check_eligibility.return_value = EligibilityResult(True, 3, False)
    record = MagicMock(spec=Advice)
    record.advice_text = _advice_text()
    record.generated_at = datetime(2025, 10, 15, tzinfo=UTC)
    advice_service.get_advice_by_month_id.return_value = record

    response = client.get("/api/advice/2025/10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["exists"] is True
    assert payload["is_valid"] is True
    assert payload["advice"]["outputs"][0]["type"] == "unresolved"


@patch("app.api.advice.check_eligibility")
@patch("app.api.advice.advice_service")
@patch("app.api.advice.months_service")
def test_get_marks_missing_advice_invalid(
    months_service: MagicMock,
    advice_service: MagicMock,
    check_eligibility: MagicMock,
) -> None:
    """GET reports absent advice as not valid."""
    months_service.get_month_by_year_month.return_value = _month()
    check_eligibility.return_value = EligibilityResult(True, 3, True)
    advice_service.get_advice_by_month_id.return_value = None

    response = client.get("/api/advice/2025/10")

    assert response.status_code == 200
    assert response.json()["exists"] is False
    assert response.json()["is_valid"] is False


@patch("app.api.advice.check_eligibility")
@patch("app.api.advice.advice_service")
@patch("app.api.advice.months_service")
def test_get_rejects_historical_cached_contract(
    months_service: MagicMock,
    advice_service: MagicMock,
    check_eligibility: MagicMock,
) -> None:
    """GET never exposes historical cached advice."""
    months_service.get_month_by_year_month.return_value = _month()
    check_eligibility.return_value = EligibilityResult(True, 3, False)
    record = MagicMock(spec=Advice)
    record.advice_text = '{"analysis":"old","problem_areas":[],"recommendations":[],"encouragement":"old"}'
    record.generated_at = datetime(2025, 10, 15, tzinfo=UTC)
    advice_service.get_advice_by_month_id.return_value = record

    response = client.get("/api/advice/2025/10")

    assert response.status_code == 500
    assert "regenerate" in response.json()["detail"].lower()


@patch("app.api.advice.months_service")
def test_get_unknown_month_returns_not_found(months_service: MagicMock) -> None:
    """GET returns not found for unknown month."""
    months_service.get_month_by_year_month.return_value = None

    response = client.get("/api/advice/2025/10")

    assert response.status_code == 404
