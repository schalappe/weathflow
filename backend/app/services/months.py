"""Service functions for retrieving month and transaction data."""

import logging
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.responses._types import ScoreTrendLiteral
from app.responses.history import HistorySummary, MonthReference
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
    category_types: list[str] | None = None,
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
    category_types : list[str] | None
        Filter by money_map_type (e.g., ["INCOME", "CORE"]).
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
        if category_types is not None and len(category_types) > 0:
            # ##>: Validate category types and log warnings for invalid values.
            valid_types = {e.value for e in MoneyMapType}
            invalid_types = [c for c in category_types if c not in valid_types]
            if invalid_types:
                logger.warning("Invalid category_types ignored: %s", invalid_types)
            valid_categories = [c for c in category_types if c in valid_types]
            if valid_categories:
                query = query.filter(Transaction.money_map_type.in_(valid_categories))

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
            "Retrieved %d/%d transactions for month_id=%d (page=%d, filters: categories=%s, search=%s)",
            len(transactions),
            total_count,
            month_id,
            page,
            category_types,
            search[:20] if search else None,
        )

        return transactions, total_count
    except SQLAlchemyError as error:
        logger.error("Database error retrieving transactions for month_id=%d: %s", month_id, str(error))
        raise TransactionQueryError(month_id, str(error)) from error


def get_months_history(db: Session, limit: int) -> list[Month]:
    """
    Retrieve months for historical data, ordered chronologically (oldest first).

    Fetches the most recent N months then reverses for chronological order.

    Parameters
    ----------
    db : Session
        Database session.
    limit : int
        Maximum number of months to return (1-24).

    Returns
    -------
    list[Month]
        List of Month records ordered by year asc, month asc.

    Raises
    ------
    MonthQueryError
        If database query fails.
    """
    try:
        result = db.query(Month).order_by(Month.year.desc(), Month.month.desc()).limit(limit).all()
        # ##>: Reverse to get chronological order (oldest first).
        result.reverse()
        logger.info("Retrieved %d months for history", len(result))
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving months for history: %s", str(error))
        raise MonthQueryError(str(error)) from error


def _calculate_score_trend(months: list[Month]) -> ScoreTrendLiteral:
    """
    Calculate score trend comparing recent vs previous periods.

    Compares average score of last 3 months against average of previous 3 months.

    Parameters
    ----------
    months : list[Month]
        Months in chronological order (oldest first).

    Returns
    -------
    ScoreTrendLiteral
        "improving", "declining", or "stable".

    Notes
    -----
    Returns "stable" if fewer than 6 months of data or averages are equal.
    """
    if len(months) < 6:
        return "stable"

    # ##>: Last 3 months vs previous 3 months (months are oldest first).
    recent_scores = [m.score for m in months[-3:]]
    previous_scores = [m.score for m in months[-6:-3]]

    recent_avg = sum(recent_scores) / 3
    previous_avg = sum(previous_scores) / 3

    if recent_avg > previous_avg:
        return "improving"
    if recent_avg < previous_avg:
        return "declining"
    return "stable"


def calculate_history_summary(months: list[Month]) -> HistorySummary:
    """
    Calculate summary statistics for historical data.

    Parameters
    ----------
    months : list[Month]
        Months in chronological order (oldest first).

    Returns
    -------
    HistorySummary
        Summary with total_months, average_score, score_trend, best_month, worst_month.

    Notes
    -----
    - Returns zeroed summary if months list is empty.
    - Tie-break for best/worst: most recent month wins.
    """
    if not months:
        return HistorySummary(
            total_months=0,
            average_score=0.0,
            score_trend="stable",
            best_month=None,
            worst_month=None,
        )

    total_months = len(months)
    average_score = round(sum(m.score for m in months) / total_months, 2)
    score_trend = _calculate_score_trend(months)

    # ##>: Find best/worst with tie-break (most recent wins).
    # Iterate forward (oldest first), use >= and <= so later months (more recent) win ties.
    best = months[0]
    worst = months[0]

    for month in months:
        if month.score >= best.score:
            best = month
        if month.score <= worst.score:
            worst = month

    best_ref = MonthReference(year=best.year, month=best.month, score=best.score)
    worst_ref = MonthReference(year=worst.year, month=worst.month, score=worst.score)

    return HistorySummary(
        total_months=total_months,
        average_score=average_score,
        score_trend=score_trend,
        best_month=best_ref,
        worst_month=worst_ref,
    )
