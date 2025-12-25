"""Service functions for cash flow data aggregation."""

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.enums import MoneyMapType
from app.repositories.month import MonthRepository
from app.repositories.transaction import TransactionRepository
from app.responses.cashflow import CashFlowData, CategoryBreakdown
from app.services.exceptions import MonthQueryError, TransactionQueryError


def get_cashflow_data(
    month_repo: MonthRepository,
    transaction_repo: TransactionRepository,
    months: int,
) -> CashFlowData:
    """
    Aggregate cash flow data for Sankey diagram visualization.

    Retrieves recent months, aggregates transactions by category and subcategory,
    and calculates deficit when spending exceeds income.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
    transaction_repo : TransactionRepository
        Repository for transaction data access.
    months : int
        Number of months to aggregate (0 = all time).

    Returns
    -------
    CashFlowData
        Aggregated cash flow data with category totals, breakdowns, and deficit.

    Raises
    ------
    MonthQueryError
        If database query for months fails.
    TransactionQueryError
        If database query for transactions fails.
    """
    try:
        month_records = month_repo.get_recent(months)
        if not month_records:
            logger.info("No months found for cashflow aggregation")
            return CashFlowData(
                income_total=0.0,
                core_total=0.0,
                choice_total=0.0,
                compound_total=0.0,
                deficit=0.0,
                core_breakdown=[],
                choice_breakdown=[],
                compound_breakdown=[],
            )

        month_ids = [m.id for m in month_records]
        logger.info("Aggregating cashflow for {} months: {}", len(month_ids), month_ids)

    except SQLAlchemyError as error:
        logger.error("Database error retrieving months for cashflow: {}", str(error))
        raise MonthQueryError(str(error)) from error

    try:
        aggregated = transaction_repo.aggregate_by_subcategory(month_ids)
    except SQLAlchemyError as error:
        logger.error("Database error aggregating transactions for cashflow: {}", str(error))
        raise TransactionQueryError(0, str(error)) from error

    return _build_cashflow_data(aggregated)


def _build_cashflow_data(
    aggregated: list[tuple[str, str | None, float]],
) -> CashFlowData:
    """
    Build CashFlowData from aggregated transaction tuples.

    Groups data by category, calculates totals, and computes deficit.

    Parameters
    ----------
    aggregated : list[tuple[str, str | None, float]]
        List of (money_map_type, money_map_subcategory, total) tuples.

    Returns
    -------
    CashFlowData
        Structured cash flow data ready for API response.
    """
    income_total = 0.0
    core_total = 0.0
    choice_total = 0.0

    core_breakdown: list[CategoryBreakdown] = []
    choice_breakdown: list[CategoryBreakdown] = []
    compound_breakdown: list[CategoryBreakdown] = []

    for money_map_type, subcategory, amount in aggregated:
        subcategory_name = subcategory or "Other"

        if money_map_type == MoneyMapType.INCOME.value:
            income_total += amount
        elif money_map_type == MoneyMapType.CORE.value:
            core_total += amount
            core_breakdown.append(CategoryBreakdown(subcategory=subcategory_name, amount=amount))
        elif money_map_type == MoneyMapType.CHOICE.value:
            choice_total += amount
            choice_breakdown.append(CategoryBreakdown(subcategory=subcategory_name, amount=amount))
        elif money_map_type == MoneyMapType.COMPOUND.value:
            # [>]: Collect actual savings transactions for breakdown display.
            # compound_total is calculated below using Money Map formula.
            compound_breakdown.append(CategoryBreakdown(subcategory=subcategory_name, amount=amount))

    # [>]: Calculate deficit or compound using Money Map formula.
    # COMPOUND = INCOME - (CORE + CHOICE) when no overspending.
    # Deficit = (CORE + CHOICE) - INCOME when overspending.
    spending = core_total + choice_total

    if spending > income_total:
        # [>]: Overspending: show deficit, hide compound.
        deficit = spending - income_total
        compound_total = 0.0
        compound_breakdown = []
    else:
        # [>]: No overspending: calculate disposable savings using Money Map formula.
        # compound_breakdown retains actual savings transactions for subcategory display.
        deficit = 0.0
        compound_total = income_total - spending

    logger.info(
        "Cashflow aggregation complete: income={:.2f}, core={:.2f}, choice={:.2f}, compound={:.2f}, deficit={:.2f}",
        income_total,
        core_total,
        choice_total,
        compound_total,
        deficit,
    )

    return CashFlowData(
        income_total=income_total,
        core_total=core_total,
        choice_total=choice_total,
        compound_total=compound_total,
        deficit=deficit,
        core_breakdown=core_breakdown,
        choice_breakdown=choice_breakdown,
        compound_breakdown=compound_breakdown,
    )
