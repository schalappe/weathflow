"""Active-priority persistence."""

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.db.models.active_priority import ActivePriority
from app.db.models.base import utc_now


class ActivePriorityRepository:
    """Store singleton active priority.

    Attributes
    ----------
    _db : Session
        Bound transaction.
    """

    def __init__(self, db: Session) -> None:
        """Bind database session.

        Parameters
        ----------
        db : Session
            Database transaction.
        """
        self._db = db

    def get(self) -> ActivePriority | None:
        """Return current priority; expire stale value first.

        Returns
        -------
        ActivePriority | None
            Stored value, including `to_confirm`.
        """
        priority = self._db.get(ActivePriority, 1)
        if (
            priority is not None
            and priority.state != "to_confirm"
            and utc_now().replace(tzinfo=None) > priority.valid_until
        ):
            priority.state = "to_confirm"
            self._db.commit()
            self._db.refresh(priority)
        return priority

    def put(self, goal: str, target: str, deadline: date | None) -> ActivePriority:
        """Create or correct priority.

        Parameters
        ----------
        goal : str
            Current objective.
        target : str
            Objective target.
        deadline : date | None
            Optional objective date.

        Returns
        -------
        ActivePriority
            Stored active or corrected value.
        """
        now = utc_now().replace(tzinfo=None)
        valid_until = now + timedelta(days=180)
        if deadline is not None:
            valid_until = min(valid_until, datetime.combine(deadline, time.max))

        priority = self._db.get(ActivePriority, 1)
        if priority is None:
            priority = ActivePriority(
                id=1,
                goal=goal,
                target=target,
                deadline=deadline,
                state="active",
                last_confirmed_at=now,
                valid_until=valid_until,
            )
            self._db.add(priority)
        else:
            priority.goal = goal
            priority.target = target
            priority.deadline = deadline
            priority.state = "corrected"
            priority.last_confirmed_at = now
            priority.valid_until = valid_until

        self._db.commit()
        self._db.refresh(priority)
        return priority

    def mark_to_confirm(self) -> None:
        """Neutralize stored priority after session-only override."""
        priority = self._db.get(ActivePriority, 1)
        if priority is not None:
            priority.state = "to_confirm"
            self._db.commit()

    def delete(self) -> None:
        """Delete priority when present."""
        priority = self._db.get(ActivePriority, 1)
        if priority is not None:
            self._db.delete(priority)
            self._db.commit()
