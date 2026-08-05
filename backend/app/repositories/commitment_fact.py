"""Obligation and debt context persistence."""

from datetime import date, datetime, time, timedelta
from typing import Any, Literal, cast

from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.commitment_fact import CommitmentFact

CommitmentFactType = Literal[
    "recurring_obligation",
    "one_off_obligation",
    "debt_position",
    "debt_terms",
]

FRESHNESS_DAYS: dict[CommitmentFactType, int] = {
    "recurring_obligation": 90,
    "debt_position": 30,
    "debt_terms": 90,
}


class CommitmentFactRepository:
    """Store independently fresh obligation and debt facts.

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

    def get(self, fact_id: int) -> CommitmentFact | None:
        """Return fact by id.

        Parameters
        ----------
        fact_id : int
            Stored fact id.

        Returns
        -------
        CommitmentFact | None
            Stored fact when present.
        """
        return self._db.get(CommitmentFact, fact_id)

    def get_all(self) -> list[CommitmentFact]:
        """Return facts after expiring stale values.

        Returns
        -------
        list[CommitmentFact]
            Stored facts, including inactive values.
        """
        facts = self._db.query(CommitmentFact).order_by(CommitmentFact.id).all()
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

    def put(self, values: dict[str, Any], fact_id: int | None = None) -> CommitmentFact:
        """Create, correct, or reconfirm one fact.

        Parameters
        ----------
        values : dict[str, Any]
            Validated fact fields.
        fact_id : int | None
            Fact to replace.

        Returns
        -------
        CommitmentFact
            Stored fact.
        """
        now = utc_now().replace(tzinfo=None)
        fact = self._db.get(CommitmentFact, fact_id) if fact_id is not None else None
        if fact is None:
            fact = CommitmentFact(state="active", **values)
            self._db.add(fact)
        else:
            unchanged = all(getattr(fact, field) == value for field, value in values.items())
            for field, value in values.items():
                setattr(fact, field, value)
            fact.state = "active" if unchanged else "corrected"
        fact.last_confirmed_at = now
        fact.valid_until = self._valid_until(values, now)
        self._db.commit()
        self._db.refresh(fact)
        return fact

    def delete(self, fact_id: int) -> CommitmentFactType | None:
        """Delete fact.

        Parameters
        ----------
        fact_id : int
            Stored fact id.

        Returns
        -------
        CommitmentFactType | None
            Deleted type when present.
        """
        fact = self._db.get(CommitmentFact, fact_id)
        if fact is None:
            return None
        fact_type = cast(CommitmentFactType, fact.fact_type)
        self._db.delete(fact)
        self._db.commit()
        return fact_type

    def mark_to_confirm(self, fact_id: int) -> None:
        """Neutralize stored fact after session override.

        Parameters
        ----------
        fact_id : int
            Stored fact id.
        """
        fact = self._db.get(CommitmentFact, fact_id)
        if fact is not None:
            fact.state = "to_confirm"
            self._db.commit()

    @staticmethod
    def _valid_until(values: dict[str, Any], now: datetime) -> datetime:
        """Calculate dated or freshness expiry.

        Parameters
        ----------
        values : dict[str, Any]
            Validated fact fields.
        now : datetime
            Confirmation time.

        Returns
        -------
        datetime
            Reuse cutoff.

        Raises
        ------
        ValueError
            One-off due date is absent.
        """
        fact_type: CommitmentFactType = values["fact_type"]
        explicit_date: date | None = values.get("due_date") or values.get("end_date")
        if fact_type == "one_off_obligation":
            if explicit_date is None:
                raise ValueError("one_off_obligation requires due_date")
            return datetime.combine(explicit_date, time.max)
        valid_until = now + timedelta(days=FRESHNESS_DAYS[fact_type])
        if explicit_date is not None:
            valid_until = min(valid_until, datetime.combine(explicit_date, time.max))
        return valid_until
