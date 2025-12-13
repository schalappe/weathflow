"""Repository for Advice data access operations."""

from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.base import utc_now


class AdviceRepository:
    """
    Repository for Advice data access operations.

    Encapsulates all database queries related to Advice entities,
    providing a clean interface for services to access advice data
    without direct SQLAlchemy coupling.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Parameters
        ----------
        db : Session
            SQLAlchemy database session.
        """
        self._db = db

    def get_by_month_id(self, month_id: int) -> Advice | None:
        """
        Get advice for a specific month.

        Parameters
        ----------
        month_id : int
            Month ID to look up.

        Returns
        -------
        Advice | None
            Advice record or None if not found.
        """
        return self._db.query(Advice).filter(Advice.month_id == month_id).first()

    def upsert(self, month_id: int, advice_text: str) -> Advice:
        """
        Create or update advice for a month.

        If advice exists for the month, updates the text and timestamp.
        Otherwise creates a new advice record.

        Parameters
        ----------
        month_id : int
            Month ID for the advice.
        advice_text : str
            JSON-serialized advice content.

        Returns
        -------
        Advice
            Created or updated advice record.

        Notes
        -----
        Uses flush() for visibility. Caller is responsible for commit().
        """
        existing = self.get_by_month_id(month_id)

        if existing:
            existing.advice_text = advice_text
            existing.generated_at = utc_now()
            self._db.flush()
            return existing

        advice = Advice(month_id=month_id, advice_text=advice_text)
        self._db.add(advice)
        self._db.flush()
        return advice

    def delete(self, advice: Advice) -> None:
        """
        Delete an advice record.

        Parameters
        ----------
        advice : Advice
            Advice record to delete.

        Notes
        -----
        Uses flush() after delete. Caller is responsible for commit().
        """
        self._db.delete(advice)
        self._db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._db.rollback()

    def refresh(self, advice: Advice) -> None:
        """Refresh advice from database to get updated values."""
        self._db.refresh(advice)
