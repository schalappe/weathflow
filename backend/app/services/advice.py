"""Service functions for advice storage and retrieval."""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.base import utc_now
from app.db.models.month import Month
from app.services.dto.advice import AdviceResponse, MonthData
from app.services.exceptions import AdviceQueryError

logger = logging.getLogger(__name__)


def get_advice_by_month_id(db: Session, month_id: int) -> Advice | None:
    """
    Retrieve stored advice for a month.

    Parameters
    ----------
    db : Session
        Database session.
    month_id : int
        Month ID to look up.

    Returns
    -------
    Advice | None
        Advice record or None if not found.

    Raises
    ------
    AdviceQueryError
        If database query fails.
    """
    try:
        result = db.query(Advice).filter(Advice.month_id == month_id).first()
        if result:
            logger.info("Found advice for month_id=%d", month_id)
        else:
            logger.info("No advice found for month_id=%d", month_id)
        return result
    except SQLAlchemyError as error:
        logger.error("Database error retrieving advice for month_id=%d: %s", month_id, str(error))
        raise AdviceQueryError(month_id, str(error)) from error


def create_or_update_advice(db: Session, month_id: int, advice_text: str) -> Advice:
    """
    Create or update advice for a month (upsert pattern).

    Parameters
    ----------
    db : Session
        Database session.
    month_id : int
        Month ID for the advice.
    advice_text : str
        JSON-serialized AdviceResponse.

    Returns
    -------
    Advice
        Created or updated advice record.

    Raises
    ------
    AdviceQueryError
        If database operation fails.
    """
    try:
        existing = db.query(Advice).filter(Advice.month_id == month_id).first()

        if existing:
            existing.advice_text = advice_text
            existing.generated_at = utc_now()
            logger.info("Updated advice for month_id=%d", month_id)
            db.commit()
            db.refresh(existing)
            return existing

        advice = Advice(month_id=month_id, advice_text=advice_text)
        db.add(advice)
        db.commit()
        db.refresh(advice)
        logger.info("Created advice for month_id=%d", month_id)
        return advice
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Database error saving advice for month_id=%d: %s", month_id, str(error))
        raise AdviceQueryError(month_id, str(error)) from error


def month_to_month_data(month: Month) -> MonthData:
    """
    Convert Month model to MonthData DTO for advice generation.

    Parameters
    ----------
    month : Month
        Database month record.

    Returns
    -------
    MonthData
        DTO suitable for AdviceGenerator.
    """
    return MonthData(
        year=month.year,
        month=month.month,
        total_income=month.total_income,
        total_core=month.total_core,
        total_choice=month.total_choice,
        total_compound=month.total_compound,
        core_percentage=month.core_percentage,
        choice_percentage=month.choice_percentage,
        compound_percentage=month.compound_percentage,
        score=month.score,
        score_label=month.score_label,
        category_breakdown=None,
    )


def advice_response_to_json(advice: AdviceResponse) -> str:
    """
    Serialize AdviceResponse to JSON string for storage.

    Parameters
    ----------
    advice : AdviceResponse
        Advice response from generator.

    Returns
    -------
    str
        JSON string representation.
    """
    return advice.model_dump_json()
