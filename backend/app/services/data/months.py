"""Service functions for retrieving month and transaction data."""

from datetime import date
from typing import Any

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.month import MonthRepository
from app.repositories.transaction import TransactionRepository
from app.responses._types import ScoreTrendLiteral
from app.responses.history import HistorySummary, MonthReference
from app.services.exceptions import InvalidCategoryTypeError, MonthQueryError, TransactionQueryError


def get_all_months_with_counts(month_repo: MonthRepository) -> list[Any]:
    """
    Retrieve all months with transaction counts, ordered by date (newest first).

    Uses a single query with LEFT JOIN to avoid N+1 queries.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.

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
        result = month_repo.get_all_with_transaction_counts()
        logger.info("Retrieved %d months with transaction counts", len(result))
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving months: %s", str(error))
        raise MonthQueryError(str(error)) from error


def get_month_by_year_month(month_repo: MonthRepository, year: int, month: int) -> Month | None:
    """
    Retrieve a single month by year and month number.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
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
        result = month_repo.get_by_year_month(year, month)
        if result:
            logger.info("Found month: %d-%02d (id=%d)", year, month, result.id)
        else:
            logger.info("Month not found: %d-%02d", year, month)
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving month %d-%02d: %s", year, month, str(error))
        raise MonthQueryError(str(error)) from error


def get_transactions_filtered(
    transaction_repo: TransactionRepository,
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
    transaction_repo : TransactionRepository
        Repository for transaction data access.
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
    InvalidCategoryTypeError
        If any invalid category types are provided.
    TransactionQueryError
        If database query fails.

    Notes
    -----
    All filters are applied with AND logic. Transactions must match all provided
    criteria to be included in the results.
    """
    try:
        # ##>: Validate category types before querying.
        if category_types is not None and len(category_types) > 0:
            valid_types = {e.value for e in MoneyMapType}
            invalid_types = [c for c in category_types if c not in valid_types]
            if invalid_types:
                logger.warning("Invalid category_types received: %s", invalid_types)
                raise InvalidCategoryTypeError(invalid_types, list(valid_types))

        transactions, total_count = transaction_repo.get_filtered(
            month_id,
            category_types=category_types,
            search=search,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

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
    except InvalidCategoryTypeError:
        raise
    except SQLAlchemyError as error:
        logger.error("Database error retrieving transactions for month_id=%d: %s", month_id, str(error))
        raise TransactionQueryError(month_id, str(error)) from error


def get_all_transactions_for_month(transaction_repo: TransactionRepository, month_id: int) -> list[Transaction]:
    """
    Retrieve all transactions for a month without pagination.

    Used for export functionality where all transactions are needed.

    Parameters
    ----------
    transaction_repo : TransactionRepository
        Repository for transaction data access.
    month_id : int
        Month ID to filter transactions.

    Returns
    -------
    list[Transaction]
        All transactions for the month, ordered by date descending.

    Raises
    ------
    TransactionQueryError
        If database query fails.
    """
    try:
        result = transaction_repo.get_all_for_month(month_id)
        logger.info("Retrieved %d transactions for export (month_id=%d)", len(result), month_id)
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving transactions for export (month_id=%d): %s", month_id, str(error))
        raise TransactionQueryError(month_id, str(error)) from error


def get_months_history(month_repo: MonthRepository, limit: int) -> list[Month]:
    """
    Retrieve months for historical data, ordered chronologically (oldest first).

    Fetches the most recent N months then reverses for chronological order.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
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
        result = month_repo.get_recent(limit)
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
