"""FastAPI router for Monthly Data API endpoints."""

import logging
from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.enums import MoneyMapType
from app.responses.months import (
    MonthDetailResponse,
    MonthsListResponse,
    MonthSummary,
    PaginationInfo,
    TransactionResponse,
)
from app.services import months as months_service
from app.services.exceptions import MonthDataError

# ruff: noqa: B008

router = APIRouter(prefix="/api", tags=["months"])
logger = logging.getLogger(__name__)


def _http_detail_for_db_error(error: MonthDataError) -> str:
    """
    Map database error to user-friendly HTTP error message.

    Parameters
    ----------
    error : MonthDataError
        Database error from month service.

    Returns
    -------
    str
        User-friendly error message for HTTP response.
    """
    error_str = str(error).lower()
    if "connection" in error_str or "timeout" in error_str:
        return "Database temporarily unavailable. Please try again in a moment."
    return "An error occurred while retrieving data. Please try again or contact support."


@router.get("/months", response_model=MonthsListResponse)
def list_months(db: Session = Depends(get_db)) -> MonthsListResponse:
    """
    List all months with summary data.

    Returns all imported months ordered by date (most recent first).
    Each month includes totals, percentages, score, and transaction count.

    Returns
    -------
    MonthsListResponse
        List of months with summary data and total count.

    Raises
    ------
    HTTPException 503
        If database is temporarily unavailable.
    """
    try:
        # ##>: Use optimized query with JOIN to avoid N+1 queries.
        months_with_counts = months_service.get_all_months_with_counts(db)
        month_summaries = [MonthSummary.from_model(m, tx_count) for m, tx_count in months_with_counts]

        return MonthsListResponse(months=month_summaries, total=len(month_summaries))
    except MonthDataError as error:
        logger.exception("Database error in list_months")
        raise HTTPException(status_code=503, detail=_http_detail_for_db_error(error)) from error
    except Exception as error:
        logger.exception("Unexpected error in list_months: error_type=%s", type(error).__name__)
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.") from error


@router.get("/months/{year}/{month}", response_model=MonthDetailResponse)
def get_month_detail(
    year: int = Path(..., ge=2000, le=2100, description="Year (e.g., 2025)"),
    month: int = Path(..., ge=1, le=12, description="Month number (1-12)"),
    category_type: MoneyMapType | None = Query(None, description="Filter by money_map_type"),
    search: str | None = Query(None, description="Case-insensitive search in description"),
    start_date: date | None = Query(None, description="Filter transactions from this date"),
    end_date: date | None = Query(None, description="Filter transactions until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> MonthDetailResponse:
    """
    Get detailed data for a specific month with filtered transactions.

    Parameters
    ----------
    year : int
        Year (e.g., 2025).
    month : int
        Month number (1-12).
    category_type : MoneyMapType | None
        Filter transactions by Money Map type.
    search : str | None
        Case-insensitive search in transaction descriptions.
    start_date : date | None
        Filter transactions from this date.
    end_date : date | None
        Filter transactions until this date.
    page : int
        Page number (default: 1).
    page_size : int
        Items per page (default: 50, max: 100).

    Returns
    -------
    MonthDetailResponse
        Month summary, transactions, and pagination info.

    Raises
    ------
    HTTPException 400
        If start_date is after end_date.
    HTTPException 404
        If month not found.
    HTTPException 503
        If database is temporarily unavailable.
    """
    # ##>: Validate date range before querying database.
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})",
        )

    try:
        month_record = months_service.get_month_by_year_month(db, year, month)

        if month_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {year}-{month:02d}. Please upload transactions for this month first.",
            )

        # ##>: Pass enum value to service (string comparison in database).
        transactions, total_items = months_service.get_transactions_filtered(
            db,
            month_id=month_record.id,
            category_type=category_type.value if category_type else None,
            search=search,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        # ##>: Use total_items (filtered count) for transaction_count when filters are applied.
        # This provides consistency between transaction_count and pagination.total_items.
        has_filters = any([category_type, search, start_date, end_date])
        transaction_count = total_items if has_filters else len(month_record.transactions)

        month_summary = MonthSummary.from_model(month_record, transaction_count)

        transaction_responses = [
            TransactionResponse(
                id=tx.id,
                date=tx.date,
                description=tx.description,
                account=tx.account,
                amount=tx.amount,
                bankin_category=tx.bankin_category,
                bankin_subcategory=tx.bankin_subcategory,
                money_map_type=tx.money_map_type,
                money_map_subcategory=tx.money_map_subcategory,
                is_manually_corrected=tx.is_manually_corrected,
            )
            for tx in transactions
        ]

        total_pages = ceil(total_items / page_size) if total_items > 0 else 0

        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

        return MonthDetailResponse(
            month=month_summary,
            transactions=transaction_responses,
            pagination=pagination,
        )
    except HTTPException:
        # ##>: Re-raise HTTPException (400, 404) without wrapping.
        raise
    except MonthDataError as error:
        logger.exception("Database error in get_month_detail for %d-%02d", year, month)
        raise HTTPException(status_code=503, detail=_http_detail_for_db_error(error)) from error
    except Exception as error:
        logger.exception(
            "Unexpected error in get_month_detail for %d-%02d: error_type=%s", year, month, type(error).__name__
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.") from error
