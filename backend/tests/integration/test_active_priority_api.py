"""Integration tests for active-priority context."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.active_priority import ActivePriority
from app.db.models.advice import Advice
from app.db.models.month import Month
from app.services.advice.models import AdviceResponse


def test_active_priority_can_be_stored_read_corrected_and_deleted(client: TestClient) -> None:
    """Active priority remains user-controlled through its public API."""
    created = client.put(
        "/api/advice/context/active-priority",
        json={
            "goal": "Constituer un fonds d'urgence",
            "target": "6 000 €",
            "deadline": "2027-06-30",
        },
    )

    assert created.status_code == 200
    assert set(created.json()["priority"]) == {
        "goal",
        "target",
        "deadline",
        "state",
        "last_confirmed_at",
        "valid_until",
    }
    assert created.json()["priority"]["state"] == "active"

    retrieved = client.get("/api/advice/context/active-priority")
    assert retrieved.status_code == 200
    assert retrieved.json()["priority"] == created.json()["priority"]

    corrected = client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Rembourser le prêt auto", "target": "4 500 €", "deadline": None},
    )
    assert corrected.status_code == 200
    assert corrected.json()["priority"]["goal"] == "Rembourser le prêt auto"
    assert corrected.json()["priority"]["state"] == "corrected"

    deleted = client.delete("/api/advice/context/active-priority")
    assert deleted.status_code == 204
    assert client.get("/api/advice/context/active-priority").json() == {"priority": None}


def test_expired_priority_stays_visible_but_invalidates_dependent_advice(
    client: TestClient,
    db_session: Session,
) -> None:
    """J+181 priority becomes inactive before dependent advice is read."""
    client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Fonds d'urgence", "target": "6 000 €", "deadline": None},
    )
    month = Month(
        year=2025,
        month=10,
        total_income=3000,
        total_core=1500,
        total_choice=900,
        total_compound=600,
        core_percentage=50,
        choice_percentage=30,
        compound_percentage=20,
        score=2,
        score_label="Okay",
    )
    db_session.add(month)
    db_session.flush()
    advice = AdviceResponse.model_validate(
        {
            "outputs": [
                {
                    "type": "recommendation",
                    "income_dependent": False,
                    "priority": "high",
                    "action": "Affecter l'épargne au fonds d'urgence.",
                    "trace": {
                        "summary": "La priorité déclarée oriente l'épargne.",
                        "details": {
                            "observations": [
                                {
                                    "fact": "600 € épargnés.",
                                    "period": "octobre 2025",
                                    "scope": "Transactions COMPOUND",
                                    "source": "observed_data",
                                }
                            ],
                            "declared_facts": [
                                {
                                    "fact_type": "active_priority",
                                    "goal": "Fonds d'urgence",
                                    "target": "6 000 €",
                                    "deadline": None,
                                    "state": "active",
                                    "last_confirmed_at": "2026-01-01T00:00:00",
                                    "valid_until": "2026-06-30T00:00:00",
                                    "can_correct": True,
                                    "can_delete": True,
                                }
                            ],
                        },
                    },
                }
            ]
        }
    )
    db_session.add(Advice(month_id=month.id, advice_text=advice.model_dump_json()))
    priority = db_session.get(ActivePriority, 1)
    assert priority is not None
    priority.last_confirmed_at = datetime.now() - timedelta(days=181)
    priority.valid_until = priority.last_confirmed_at + timedelta(days=180)
    db_session.commit()

    response = client.get("/api/advice/2025/10")

    assert response.status_code == 200
    assert response.json()["exists"] is False
    context = client.get("/api/advice/context/active-priority").json()["priority"]
    assert context["state"] == "to_confirm"
    assert context["goal"] == "Fonds d'urgence"


def test_correction_and_deletion_remove_dependent_advice(
    client: TestClient,
    db_session: Session,
) -> None:
    """Context mutations invalidate advice that depends on old priority."""
    client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Fonds d'urgence", "target": "6 000 €", "deadline": None},
    )
    month = Month(
        year=2025,
        month=10,
        total_income=3000,
        total_core=1500,
        total_choice=900,
        total_compound=600,
        core_percentage=50,
        choice_percentage=30,
        compound_percentage=20,
        score=2,
        score_label="Okay",
    )
    db_session.add(month)
    db_session.flush()
    dependent_advice = '{"outputs":[{"type":"clarification","fact_type":"active_priority"}]}'
    db_session.add(Advice(month_id=month.id, advice_text=dependent_advice))
    db_session.commit()

    client.put(
        "/api/advice/context/active-priority",
        json={"goal": "Prêt auto", "target": "4 500 €", "deadline": None},
    )

    assert db_session.query(Advice).count() == 0
    db_session.add(Advice(month_id=month.id, advice_text=dependent_advice))
    db_session.commit()

    client.delete("/api/advice/context/active-priority")

    assert db_session.query(Advice).count() == 0
