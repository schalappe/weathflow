"""Emergency-fund context persistence."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.emergency_fund_fact import EmergencyFundFact, EmergencyFundFactType

FRESHNESS_DAYS: dict[EmergencyFundFactType, int] = {
    "liquid_reserve": 30,
    "safety_floor": 180,
    "priority_allocation": 30,
}


class EmergencyFundFactRepository:
    """Store independent emergency-fund amounts.

    Attributes
    ----------
    _db : Session
        Database transaction.
    """

    def __init__(self, db: Session) -> None:
        """Bind transaction.

        Parameters
        ----------
        db : Session
            Database transaction.
        """
        self._db = db

    def get_all(self) -> list[EmergencyFundFact]:
        """Return all facts after expiring stale values.

        Returns
        -------
        list[EmergencyFundFact]
            Stored facts, including inactive values.
        """
        facts = self._db.query(EmergencyFundFact).all()
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

    def put(self, fact_type: EmergencyFundFactType, amount: float) -> EmergencyFundFact:
        """Create, correct, or reconfirm amount.

        Parameters
        ----------
        fact_type : EmergencyFundFactType
            Closed-catalog fact key.
        amount : float
            Declared euro amount.

        Returns
        -------
        EmergencyFundFact
            Stored lifecycle value.
        """
        now = utc_now().replace(tzinfo=None)
        fact = self._db.get(EmergencyFundFact, fact_type)
        if fact is None:
            fact = EmergencyFundFact(
                fact_type=fact_type,
                amount=amount,
                state="active",
                last_confirmed_at=now,
                valid_until=now + timedelta(days=FRESHNESS_DAYS[fact_type]),
            )
            self._db.add(fact)
        else:
            fact.amount = amount
            fact.state = "corrected"
            fact.last_confirmed_at = now
            fact.valid_until = now + timedelta(days=FRESHNESS_DAYS[fact_type])
        self._db.commit()
        self._db.refresh(fact)
        return fact

    def delete(self, fact_type: EmergencyFundFactType) -> None:
        """Delete amount when present.

        Parameters
        ----------
        fact_type : EmergencyFundFactType
            Closed-catalog fact key.
        """
        fact = self._db.get(EmergencyFundFact, fact_type)
        if fact is not None:
            self._db.delete(fact)
            self._db.commit()

    def mark_to_confirm(self, fact_type: EmergencyFundFactType) -> None:
        """Neutralize stored amount after session override.

        Parameters
        ----------
        fact_type : EmergencyFundFactType
            Closed-catalog fact key.
        """
        fact = self._db.get(EmergencyFundFact, fact_type)
        if fact is not None:
            fact.state = "to_confirm"
            self._db.commit()
