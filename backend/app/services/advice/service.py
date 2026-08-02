"""Advice storage and generation-data services."""

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.advice import AdviceRepository
from app.services.advice.models import AdviceResponse, MonthData, TransactionSample
from app.services.exceptions import AdviceQueryError


def get_advice_by_month_id(advice_repo: AdviceRepository, month_id: int) -> Advice | None:
    """Retrieve stored advice.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Advice storage.
    month_id : int
        Month id.

    Returns
    -------
    Advice | None
        Stored record.

    Raises
    ------
    AdviceQueryError
        Query failed.
    """
    try:
        return advice_repo.get_by_month_id(month_id)
    except SQLAlchemyError as error:
        logger.exception("Database error retrieving advice for month_id={}", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def create_or_update_advice(advice_repo: AdviceRepository, month_id: int, advice_text: str) -> Advice:
    """Persist current monthly advice.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Advice storage.
    month_id : int
        Month id.
    advice_text : str
        Decision JSON.

    Returns
    -------
    Advice
        Persisted record.

    Raises
    ------
    AdviceQueryError
        Write failed.
    """
    try:
        result = advice_repo.upsert(month_id, advice_text)
        advice_repo.commit()
        advice_repo.refresh(result)
        return result
    except SQLAlchemyError as error:
        advice_repo.rollback()
        logger.exception("Database error saving advice for month_id={}", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def _extract_all_transactions(transactions: list[Transaction]) -> dict[str, list[TransactionSample]]:
    """Group observed expenses.

    Parameters
    ----------
    transactions : list[Transaction]
        Month transactions.

    Returns
    -------
    dict[str, list[TransactionSample]]
        Expenses grouped by Money Map category.
    """
    categories = {"CORE", "CHOICE", "COMPOUND"}
    grouped: dict[str, list[Transaction]] = {category: [] for category in categories}
    for transaction in transactions:
        if transaction.money_map_type in categories:
            grouped[transaction.money_map_type].append(transaction)

    return {
        category: [
            TransactionSample(
                description=transaction.description,
                amount=abs(transaction.amount),
                subcategory=transaction.money_map_subcategory,
            )
            for transaction in sorted(items, key=lambda item: abs(item.amount), reverse=True)
        ]
        for category, items in grouped.items()
    }


def month_to_month_data(month: Month) -> MonthData:
    """Convert persisted month to observed generation data.

    Parameters
    ----------
    month : Month
        Month with transactions loaded.

    Returns
    -------
    MonthData
        Generator input.
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
        transactions=_extract_all_transactions(month.transactions),
    )


def advice_response_to_json(advice: AdviceResponse) -> str:
    """Serialize decision outputs.

    Parameters
    ----------
    advice : AdviceResponse
        Valid decision outputs.

    Returns
    -------
    str
        Storage JSON.
    """
    return advice.model_dump_json()
