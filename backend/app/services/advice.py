"""Service functions for advice storage and retrieval."""

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice_repository import AdviceRepository
from app.services.dto.advice import AdviceResponse, MonthData
from app.services.exceptions import AdviceQueryError

logger = logging.getLogger(__name__)


def get_advice_by_month_id(advice_repo: AdviceRepository, month_id: int) -> Advice | None:
    """
    Retrieve stored advice for a month.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Repository for advice data access.
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
        result = advice_repo.get_by_month_id(month_id)
        if result:
            logger.info("Found advice for month_id=%d", month_id)
        else:
            logger.info("No advice found for month_id=%d", month_id)
        return result
    except SQLAlchemyError as error:
        logger.exception("Database error retrieving advice for month_id=%d", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def create_or_update_advice(advice_repo: AdviceRepository, month_id: int, advice_text: str) -> Advice:
    """
    Create or update advice for a month (upsert pattern).

    Parameters
    ----------
    advice_repo : AdviceRepository
        Repository for advice data access.
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
        result = advice_repo.upsert(month_id, advice_text)
        advice_repo.commit()
        advice_repo.refresh(result)
        logger.info("Saved advice for month_id=%d", month_id)
        return result
    except SQLAlchemyError as error:
        advice_repo.rollback()
        logger.exception("Database error saving advice for month_id=%d", month_id)
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
