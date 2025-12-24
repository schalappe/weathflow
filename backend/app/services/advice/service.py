"""Service functions for advice storage and retrieval."""

import json

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.advice import AdviceRepository
from app.services.advice.models import AdviceResponse, MonthData, TransactionSample
from app.services.exceptions import AdviceQueryError


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
            logger.info("Found advice for month_id={}", month_id)
        else:
            logger.info("No advice found for month_id={}", month_id)
        return result
    except SQLAlchemyError as error:
        logger.exception("Database error retrieving advice for month_id={}", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def get_advice_by_month_ids(advice_repo: AdviceRepository, month_ids: list[int]) -> dict[int, Advice]:
    """
    Retrieve stored advice for multiple months in a single query.

    Eliminates N+1 queries when fetching advice for multiple months.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Repository for advice data access.
    month_ids : list[int]
        List of month IDs to look up.

    Returns
    -------
    dict[int, Advice]
        Mapping of month_id to Advice record. Missing months are not included.

    Raises
    ------
    AdviceQueryError
        If database query fails.
    """
    try:
        result = advice_repo.get_by_month_ids(month_ids)
        logger.info("Retrieved {} advice records for {} month_ids", len(result), len(month_ids))
        return result
    except SQLAlchemyError as error:
        logger.exception("Database error retrieving advice for month_ids={}", month_ids)
        raise AdviceQueryError(0, str(error)) from error


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
        logger.info("Saved advice for month_id={}", month_id)
        return result
    except SQLAlchemyError as error:
        advice_repo.rollback()
        logger.exception("Database error saving advice for month_id={}", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def _extract_all_transactions(transactions: list[Transaction]) -> dict[str, list[TransactionSample]]:
    """
    Extract all transactions per category for pattern analysis.

    Groups transactions by money_map_type so Claude can identify patterns,
    recurring expenses, and opportunities for savings.

    Parameters
    ----------
    transactions : list[Transaction]
        All transactions for the month.

    Returns
    -------
    dict[str, list[TransactionSample]]
        All transactions per category (CORE, CHOICE, COMPOUND).
    """
    # ##>: Group transactions by category, excluding INCOME and EXCLUDED.
    categories_to_include = {"CORE", "CHOICE", "COMPOUND"}
    grouped: dict[str, list[Transaction]] = {cat: [] for cat in categories_to_include}

    for tx in transactions:
        if tx.money_map_type in categories_to_include:
            grouped[tx.money_map_type].append(tx)

    result: dict[str, list[TransactionSample]] = {}
    for category, category_transactions in grouped.items():
        # ##>: Sort by absolute amount (largest first) for readability.
        sorted_txs = sorted(category_transactions, key=lambda t: abs(t.amount), reverse=True)

        result[category] = [
            TransactionSample(
                description=tx.description,
                amount=abs(tx.amount),
                subcategory=tx.money_map_subcategory,
            )
            for tx in sorted_txs
        ]

    return result


def month_to_month_data(month: Month, past_advice: list[str] | None = None) -> MonthData:
    """
    Convert Month model to MonthData DTO for advice generation.

    Includes all transactions per category for pattern analysis and personalized recommendations.

    Parameters
    ----------
    month : Month
        Database month record with transactions loaded.
    past_advice : list[str] | None
        Previous recommendations given for this month (if any).

    Returns
    -------
    MonthData
        DTO suitable for AdviceGenerator.
    """
    all_transactions = _extract_all_transactions(month.transactions)

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
        transactions=all_transactions,
        past_advice=past_advice,
    )


def extract_recommendations_from_advice(advice_text: str) -> list[str]:
    """
    Extract recommendations list from stored advice JSON.

    Handles both new dictionary format and legacy string format.

    Parameters
    ----------
    advice_text : str
        JSON-serialized advice stored in database.

    Returns
    -------
    list[str]
        List of recommendation action strings, or empty list if parsing fails.
    """
    try:
        data = json.loads(advice_text)
        recommendations = data.get("recommendations", [])
        if not isinstance(recommendations, list):
            logger.warning("Advice JSON has non-list recommendations field: type={}", type(recommendations).__name__)
            return []

        result = []
        for rec in recommendations:
            if isinstance(rec, dict):
                # ##>: New format: extract action text from structured recommendation.
                action = rec.get("action", "")
                if action:
                    result.append(action)
            else:
                # ##>: Legacy format: recommendation is already a string.
                result.append(str(rec))
        return result
    except json.JSONDecodeError as error:
        logger.warning("Failed to parse advice JSON for recommendations extraction: {}", error)
        return []
    except (TypeError, AttributeError) as error:
        logger.warning("Unexpected error extracting recommendations: {}: {}", type(error).__name__, error)
        return []


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
