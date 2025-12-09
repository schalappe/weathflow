"""
Score calculation service for Money Map budget analysis.

This module provides pure calculation functions and database integration
for computing monthly budget scores based on the 50/30/20 framework.
"""

import logging

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.enums import SCORE_TO_LABEL, MoneyMapType, ScoreLabel
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.dto.calculation import MonthStats
from app.services.exceptions import MonthNotFoundError, ScorePersistenceError, TransactionAggregationError

logger = logging.getLogger(__name__)

# ##>: Money Map threshold constants for the 50/30/20 rule.
CORE_THRESHOLD = 50.0
CHOICE_THRESHOLD = 30.0
COMPOUND_THRESHOLD = 20.0


def calculate_score(core_pct: float, choice_pct: float, compound_pct: float) -> tuple[int, ScoreLabel]:
    """
    Calculate Money Map score from category percentages.

    Awards one point for each threshold met:
    - Core spending <= 50% of income
    - Choice spending <= 30% of income
    - Compound (savings) >= 20% of income

    Parameters
    ----------
    core_pct : float
        Core spending as percentage of income.
    choice_pct : float
        Choice spending as percentage of income.
    compound_pct : float
        Compound (savings) as percentage of income.

    Returns
    -------
    tuple[int, ScoreLabel]
        Score (0-3) and corresponding human-readable label.
    """
    score = 0

    if core_pct <= CORE_THRESHOLD:
        score += 1
    if choice_pct <= CHOICE_THRESHOLD:
        score += 1
    if compound_pct >= COMPOUND_THRESHOLD:
        score += 1

    return score, SCORE_TO_LABEL[score]


def _percentage_of_income(amount: float, income: float) -> float:
    """Calculate percentage of income, rounded to 1 decimal place."""
    return round((amount / income) * 100, 1)


def calculate_month_stats(income: float, core: float, choice: float) -> MonthStats:
    """
    Calculate complete month statistics from category totals.

    Derives compound (savings) as income - core - choice, calculates
    percentages relative to income, and determines the Money Map score.

    Parameters
    ----------
    income : float
        Total income for the month.
    core : float
        Total core expenses (absolute value).
    choice : float
        Total choice expenses (absolute value).

    Returns
    -------
    MonthStats
        Complete statistics including totals, percentages, and score.
    """
    # ##>: Compound is derived, not aggregated—it represents what remains after spending.
    compound = income - core - choice

    # ##>: Handle zero income edge case to avoid division by zero.
    if income <= 0:
        return MonthStats(
            total_income=income,
            total_core=core,
            total_choice=choice,
            total_compound=compound,
            core_percentage=0.0,
            choice_percentage=0.0,
            compound_percentage=0.0,
            score=0,
            score_label=ScoreLabel.POOR,
        )

    core_pct = _percentage_of_income(core, income)
    choice_pct = _percentage_of_income(choice, income)
    compound_pct = _percentage_of_income(compound, income)

    score, label = calculate_score(core_pct, choice_pct, compound_pct)

    return MonthStats(
        total_income=income,
        total_core=core,
        total_choice=choice,
        total_compound=compound,
        core_percentage=core_pct,
        choice_percentage=choice_pct,
        compound_percentage=compound_pct,
        score=score,
        score_label=label,
    )


def _aggregate_transaction_totals(db: Session, month_id: int) -> tuple[float, float, float]:
    """
    Aggregate transaction totals by money_map_type for a month.

    Uses a single SQL query with conditional aggregation for efficiency.
    Income is summed from positive amounts with INCOME type.
    Core and Choice are summed as absolute values from negative amounts.
    EXCLUDED and COMPOUND transactions are intentionally omitted.

    Parameters
    ----------
    db : Session
        Database session.
    month_id : int
        ID of the month to aggregate.

    Returns
    -------
    tuple[float, float, float]
        Tuple of (income, core, choice) totals.

    Raises
    ------
    TransactionAggregationError
        If database query fails.
    """
    try:
        result = (
            db.query(
                func.coalesce(
                    func.sum(Transaction.amount).filter(
                        Transaction.money_map_type == MoneyMapType.INCOME.value,
                        Transaction.amount > 0,
                    ),
                    0.0,
                ).label("income"),
                func.coalesce(
                    func.abs(
                        func.sum(Transaction.amount).filter(
                            Transaction.money_map_type == MoneyMapType.CORE.value,
                            Transaction.amount < 0,
                        )
                    ),
                    0.0,
                ).label("core"),
                func.coalesce(
                    func.abs(
                        func.sum(Transaction.amount).filter(
                            Transaction.money_map_type == MoneyMapType.CHOICE.value,
                            Transaction.amount < 0,
                        )
                    ),
                    0.0,
                ).label("choice"),
            )
            .filter(Transaction.month_id == month_id)
            .one()
        )
        return float(result.income), float(result.core), float(result.choice)
    except SQLAlchemyError as error:
        logger.error("Database error aggregating transactions for month_id=%d: %s", month_id, str(error))
        raise TransactionAggregationError(month_id, str(error)) from error


def calculate_and_update_month(db: Session, month_id: int) -> Month:
    """
    Calculate and persist month statistics.

    Fetches the month record, aggregates transaction totals, calculates
    statistics, updates the month record, and commits the changes.

    Parameters
    ----------
    db : Session
        Database session.
    month_id : int
        ID of the month to calculate.

    Returns
    -------
    Month
        Updated month record with all stats populated.

    Raises
    ------
    MonthNotFoundError
        If no month exists with the given ID.
    TransactionAggregationError
        If transaction aggregation query fails.
    ScorePersistenceError
        If database commit fails.
    """
    month = db.get(Month, month_id)
    if month is None:
        logger.warning("Month not found: month_id=%d", month_id)
        raise MonthNotFoundError(month_id)

    income, core, choice = _aggregate_transaction_totals(db, month_id)
    stats = calculate_month_stats(income, core, choice)

    # ##>: Update all month fields from calculated stats using model_dump.
    for field, value in stats.model_dump(exclude={"score_label"}).items():
        setattr(month, field, value)
    month.score_label = stats.score_label.value

    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Failed to persist score for month %d: %s", month_id, str(error))
        raise ScorePersistenceError(month_id) from error

    db.refresh(month)

    logger.info(
        "Updated month %d: income=%.2f, score=%d (%s)",
        month_id,
        stats.total_income,
        stats.score,
        stats.score_label.value,
    )

    return month
