"""Decision-constraint persistence."""

from datetime import date, datetime, time, timedelta
from typing import Any, Literal, cast

from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.constraint_fact import ConstraintFact

ConstraintFactType = Literal["financial_limit", "action_unavailability"]


class ConstraintFactRepository:
    """Store scoped financial limits and unavailable actions.

    Attributes
    ----------
    _db : Session
        Database transaction.
    """

    def __init__(self, db: Session) -> None:
        """Bind database transaction.

        Parameters
        ----------
        db : Session
            Database transaction.
        """
        self._db = db

    def get(self, fact_id: int) -> ConstraintFact | None:
        """Return fact by identifier.

        Parameters
        ----------
        fact_id : int
            Stored fact identifier.

        Returns
        -------
        ConstraintFact | None
            Fact when present.
        """
        return self._db.get(ConstraintFact, fact_id)

    def get_all(self) -> list[ConstraintFact]:
        """Return facts after expiring stale values.

        Returns
        -------
        list[ConstraintFact]
            Stored constraints.
        """
        facts = self._db.query(ConstraintFact).order_by(ConstraintFact.id).all()
        now = utc_now().replace(tzinfo=None)
        expired = False
        for fact in facts:
            if fact.state != "to_confirm" and now > fact.valid_until:
                fact.state = "to_confirm"
                expired = True
        if expired:
            self._db.commit()
            for fact in facts:
                self._db.refresh(fact)
        return facts

    def put(self, values: dict[str, Any], fact_id: int | None = None) -> ConstraintFact:
        """Create, correct, or reconfirm one constraint.

        Parameters
        ----------
        values : dict[str, Any]
            Constraint fields.
        fact_id : int | None
            Fact to replace.

        Returns
        -------
        ConstraintFact
            Persisted constraint.
        """
        now = utc_now().replace(tzinfo=None)
        fact = self._db.get(ConstraintFact, fact_id) if fact_id is not None else None
        if fact is None:
            fact = ConstraintFact(state="active", **values)
            self._db.add(fact)
        else:
            for field in ("scope_type", "scope", "limit_type", "amount", "action", "review_date"):
                setattr(fact, field, None)
            for field, value in values.items():
                setattr(fact, field, value)
            fact.state = "corrected"
        fact.last_confirmed_at = now
        fact.valid_until = self._valid_until(values, now)
        if now >= fact.valid_until:
            fact.state = "to_confirm"
        self._db.commit()
        self._db.refresh(fact)
        return fact

    def delete(self, fact_id: int) -> ConstraintFactType | None:
        """Delete fact and return its type.

        Parameters
        ----------
        fact_id : int
            Stored fact identifier.

        Returns
        -------
        ConstraintFactType | None
            Deleted type when present.
        """
        fact = self._db.get(ConstraintFact, fact_id)
        if fact is None:
            return None
        fact_type = cast(ConstraintFactType, fact.fact_type)
        self._db.delete(fact)
        self._db.commit()
        return fact_type

    def mark_to_confirm(self, fact_id: int) -> None:
        """Neutralize stored fact after session override.

        Parameters
        ----------
        fact_id : int
            Stored fact identifier.
        """
        fact = self._db.get(ConstraintFact, fact_id)
        if fact is not None:
            fact.state = "to_confirm"
            self._db.commit()

    @staticmethod
    def _valid_until(values: dict[str, Any], now: datetime) -> datetime:
        """Calculate freshness or explicit review cutoff.

        Parameters
        ----------
        values : dict[str, Any]
            Constraint fields.
        now : datetime
            Confirmation timestamp.

        Returns
        -------
        datetime
            Constraint cutoff.
        """
        if values["fact_type"] == "financial_limit":
            return now + timedelta(days=90)
        review_date = cast(date, values["review_date"])
        return datetime.combine(review_date, time.min)
