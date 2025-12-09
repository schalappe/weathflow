"""Service functions for retrieving month and transaction data."""

import logging
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.exceptions import MonthQueryError, TransactionQueryError

logger = logging.getLogger(__name__)


def _escape_like_pattern(search: str) -> str:
    """
    Escape SQL LIKE wildcards to treat them as literal characters.

    Parameters
    ----------
    search : str
        The search string to escape.

    Returns
    -------
    str
        Search string with %, _, and \\ escaped.
    """
    # ##>: Escape backslash first, then wildcards, to avoid double-escaping.
    return search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_all_months_with_counts(db: Session) -> list[Any]:
    """
    Retrieve all months with transaction counts, ordered by date (newest first).

    Uses a single query with LEFT JOIN to avoid N+1 queries.

    Parameters
    ----------
    db : Session
        Database session.

    Returns
    -------
    list[Any]
        List of (Month, transaction_count) rows ordered by year desc, month desc.

    Raises
    ------
    MonthQueryError
        If database query fails.
    """
    try:
        result = (
            db.query(Month, func.count(Transaction.id).label("tx_count"))
            .outerjoin(Transaction, Month.id == Transaction.month_id)
            .group_by(Month.id)
            .order_by(Month.year.desc(), Month.month.desc())
            .all()
        )
        logger.info("Retrieved %d months with transaction counts", len(result))
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving months: %s", str(error))
        raise MonthQueryError(str(error)) from error


def get_month_by_year_month(db: Session, year: int, month: int) -> Month | None:
    """
    Retrieve a single month by year and month number.

    Parameters
    ----------
    db : Session
        Database session.
    year : int
        Year (e.g., 2025).
    month : int
        Month number (1-12).

    Returns
    -------
    Month | None
        Month record or None if not found.

    Raises
    ------
    MonthQueryError
        If database query fails.
    """
    try:
        result = db.query(Month).filter(Month.year == year, Month.month == month).first()
        if result:
            logger.info("Found month: %d-%02d (id=%d)", year, month, result.id)
        else:
            logger.info("Month not found: %d-%02d", year, month)
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving month %d-%02d: %s", year, month, str(error))
        raise MonthQueryError(str(error)) from error


def get_transactions_filtered(
    db: Session,
    month_id: int,
    *,
    category_type: str | None = None,
    search: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Transaction], int]:
    """
    Retrieve filtered and paginated transactions for a month.

    Parameters
    ----------
    db : Session
        Database session.
    month_id : int
        Month ID to filter transactions.
    category_type : str | None
        Filter by money_map_type (e.g., "INCOME", "CORE").
    search : str | None
        Case-insensitive partial match on description.
    start_date : date | None
        Filter transactions on or after this date.
    end_date : date | None
        Filter transactions on or before this date.
    page : int
        Page number (1-indexed).
    page_size : int
        Number of items per page (max 100).

    Returns
    -------
    tuple[list[Transaction], int]
        (transactions, total_count) for pagination.

    Raises
    ------
    TransactionQueryError
        If database query fails.

    Notes
    -----
    All filters are applied with AND logic. Transactions must match all provided
    criteria to be included in the results.
    """
    try:
        query = db.query(Transaction).filter(Transaction.month_id == month_id)

        # ##>: Apply optional filters with AND logic.
        if category_type is not None:
            query = query.filter(Transaction.money_map_type == category_type)

        if search is not None and search.strip():
            escaped_search = _escape_like_pattern(search.strip())
            query = query.filter(Transaction.description.ilike(f"%{escaped_search}%", escape="\\"))

        if start_date is not None:
            query = query.filter(Transaction.date >= start_date)

        if end_date is not None:
            query = query.filter(Transaction.date <= end_date)

        # ##>: Get total count before pagination.
        total_count = query.count()

        # ##>: Apply ordering and pagination.
        transactions = query.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()

        logger.info(
            "Retrieved %d/%d transactions for month_id=%d (page=%d, filters: category=%s, search=%s)",
            len(transactions),
            total_count,
            month_id,
            page,
            category_type,
            search[:20] if search else None,
        )

        return transactions, total_count
    except SQLAlchemyError as error:
        logger.error("Database error retrieving transactions for month_id=%d: %s", month_id, str(error))
        raise TransactionQueryError(month_id, str(error)) from error
