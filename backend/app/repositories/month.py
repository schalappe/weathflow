"""Repository for Month data access operations."""

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.db.models.month import Month
from app.db.models.transaction import Transaction


class MonthRepository:
    """
    Repository for Month data access operations.

    Encapsulates all database queries related to Month entities,
    providing a clean interface for services to access month data
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

    def get_by_id(self, month_id: int) -> Month | None:
        """
        Get month by primary key.

        Parameters
        ----------
        month_id : int
            Primary key of the month.

        Returns
        -------
        Month | None
            Month record or None if not found.
        """
        return self._db.get(Month, month_id)

    def get_by_year_month(self, year: int, month: int) -> Month | None:
        """
        Get month by year and month number.

        Parameters
        ----------
        year : int
            Year (e.g., 2025).
        month : int
            Month number (1-12).

        Returns
        -------
        Month | None
            Month record or None if not found.
        """
        return self._db.query(Month).filter(Month.year == year, Month.month == month).first()

    def get_most_recent(self) -> Month | None:
        """
        Get the most recent month by year and month.

        Returns
        -------
        Month | None
            The newest month record, or None if no months exist.
        """
        return self._db.query(Month).order_by(Month.year.desc(), Month.month.desc()).first()

    def get_by_year_month_with_transactions(self, year: int, month: int) -> Month | None:
        """
        Get month by year and month number with transactions eager-loaded.

        Uses selectinload to fetch all transactions in a single additional query,
        avoiding N+1 queries when accessing month.transactions.

        Parameters
        ----------
        year : int
            Year (e.g., 2025).
        month : int
            Month number (1-12).

        Returns
        -------
        Month | None
            Month record with transactions loaded, or None if not found.
        """
        return (
            self._db.query(Month)
            .options(selectinload(Month.transactions))
            .filter(Month.year == year, Month.month == month)
            .first()
        )

    def get_all_with_transaction_counts(self) -> list[Any]:
        """
        Get all months with transaction counts using optimized JOIN.

        Uses a single LEFT JOIN query to avoid N+1 queries when
        displaying months with their transaction counts.

        Returns
        -------
        list[Any]
            List of (Month, transaction_count) tuples ordered by date descending.
        """
        return (
            self._db.query(Month, func.count(Transaction.id).label("tx_count"))
            .outerjoin(Transaction, Month.id == Transaction.month_id)
            .group_by(Month.id)
            .order_by(Month.year.desc(), Month.month.desc())
            .all()
        )

    def get_recent(self, limit: int) -> list[Month]:
        """
        Get most recent N months ordered chronologically (oldest first).

        Fetches the most recent months then reverses for chronological order.

        Parameters
        ----------
        limit : int
            Maximum number of months to return. Use 0 to return all months.

        Returns
        -------
        list[Month]
            List of Month records ordered by year asc, month asc.
        """
        query = self._db.query(Month).order_by(Month.year.desc(), Month.month.desc())
        # ##>: limit=0 means "all data", so skip the limit clause.
        if limit > 0:
            query = query.limit(limit)
        result = query.all()
        # ##>: Reverse to get chronological order (oldest first).
        result.reverse()
        return result

    def get_recent_with_transactions(self, limit: int) -> list[Month]:
        """
        Get most recent N months with transactions eager-loaded.

        Uses selectinload to fetch all transactions in a single additional query,
        avoiding N+1 queries when accessing month.transactions.

        Parameters
        ----------
        limit : int
            Maximum number of months to return.

        Returns
        -------
        list[Month]
            List of Month records with transactions loaded, ordered chronologically.
        """
        result = (
            self._db.query(Month)
            .options(selectinload(Month.transactions))
            .order_by(Month.year.desc(), Month.month.desc())
            .limit(limit)
            .all()
        )
        result.reverse()
        return result

    def create(self, year: int, month: int) -> Month:
        """
        Create a new month record.

        Parameters
        ----------
        year : int
            Year (e.g., 2025).
        month : int
            Month number (1-12).

        Returns
        -------
        Month
            Newly created month record with ID populated.

        Notes
        -----
        Uses flush() to get ID without committing. Caller is responsible
        for commit() when ready to persist the transaction.
        """
        month_record = Month(year=year, month=month)
        self._db.add(month_record)
        self._db.flush()
        return month_record

    def update(self, month: Month, **fields: Any) -> Month:
        """
        Update month fields.

        Parameters
        ----------
        month : Month
            Month record to update.
        **fields : Any
            Field names and values to update.

        Returns
        -------
        Month
            Updated month record.

        Notes
        -----
        Does NOT commit. Caller is responsible for commit().
        """
        for field, value in fields.items():
            setattr(month, field, value)
        return month

    def delete(self, month: Month) -> None:
        """
        Delete a month record.

        Cascades to transactions and advice due to relationship config.

        Parameters
        ----------
        month : Month
            Month record to delete.

        Notes
        -----
        Uses flush() to execute delete. Caller is responsible for commit().
        """
        self._db.delete(month)
        self._db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()

    def refresh(self, month: Month) -> None:
        """Refresh month from database to get updated values."""
        self._db.refresh(month)

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._db.rollback()

    def flush(self) -> None:
        """Flush pending changes to database without committing."""
        self._db.flush()
