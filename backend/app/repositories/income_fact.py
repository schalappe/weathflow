"""Declared income persistence."""

from datetime import datetime, time, timedelta
from typing import Any, Literal, cast

from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.income_fact import IncomeFact

IncomeFactType = Literal["usual_disposable_income", "expected_one_off_income"]


class IncomeFactRepository:
    """Store singleton habitual and expected income.

    Attributes
    ----------
    _db : Session
        Database transaction.
    """

    def __init__(self, db: Session) -> None:
        """Bind database session.

        Parameters
        ----------
        db : Session
            Database transaction.
        """
        self._db = db

    def get_all(self) -> list[IncomeFact]:
        """Return facts; stale facts become inactive.

        Returns
        -------
        list[IncomeFact]
            Stored facts, including stale values.
        """
        facts = self._db.query(IncomeFact).order_by(IncomeFact.fact_type).all()
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

    def put(self, values: dict[str, Any]) -> IncomeFact:
        """Create, correct, or reconfirm income.

        Parameters
        ----------
        values : dict[str, Any]
            Validated income fields.

        Returns
        -------
        IncomeFact
            Stored fact.

        Raises
        ------
        KeyError
            Expected income omits its date.
        """
        fact_type = cast(IncomeFactType, values["fact_type"])
        now = utc_now().replace(tzinfo=None)
        fact = self._db.get(IncomeFact, fact_type)
        if fact is None:
            fact = IncomeFact(state="active", **values)
            self._db.add(fact)
        else:
            unchanged = all(
                getattr(fact, field) == values.get(field)
                for field in ("amount", "label", "frequency", "expected_date")
            )
            for field in ("amount", "label", "frequency", "expected_date"):
                setattr(fact, field, values.get(field))
            fact.state = "active" if unchanged else "corrected"
        fact.last_confirmed_at = now
        fact.valid_until = (
            now + timedelta(days=90)
            if fact_type == "usual_disposable_income"
            else datetime.combine(values["expected_date"], time.max)
        )
        if fact.valid_until < now:
            fact.state = "to_confirm"
        self._db.commit()
        self._db.refresh(fact)
        return fact

    def delete(self, fact_type: IncomeFactType) -> None:
        """Delete fact when present.

        Parameters
        ----------
        fact_type : IncomeFactType
            Fact key.
        """
        fact = self._db.get(IncomeFact, fact_type)
        if fact is not None:
            self._db.delete(fact)
            self._db.commit()

    def mark_to_confirm(self, fact_type: IncomeFactType) -> None:
        """Neutralize stored fact after session override.

        Parameters
        ----------
        fact_type : IncomeFactType
            Fact key.
        """
        fact = self._db.get(IncomeFact, fact_type)
        if fact is not None:
            fact.state = "to_confirm"
            self._db.commit()
