"""Service functions for exporting month data to various formats."""

import csv
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.month import MonthRepository
from app.repositories.transaction import TransactionRepository
from app.services.exceptions import ExportSerializationError, MonthNotFoundError

# ##>: CSV column headers for CSV export output.
EXPORT_HEADERS = [
    "Date",
    "Description",
    "Account",
    "Amount",
    "Bankin Category",
    "Bankin Subcategory",
    "Money Map Type",
    "Money Map Subcategory",
    "Manually Corrected",
]


@dataclass
class ExportResult:
    """
    Result of an export operation.

    Attributes
    ----------
    content : bytes
        The exported content as UTF-8 bytes.
    filename : str
        Suggested filename for the download.
    media_type : str
        MIME type for the response.
    """

    content: bytes
    filename: str
    media_type: str


def _sanitize_csv_field(value: str | None) -> str:
    """
    Sanitize a string field to prevent CSV injection attacks.

    Excel and LibreOffice interpret cells starting with =, +, -, @ as formulas.
    Prefixing with a single quote prevents formula execution.

    Parameters
    ----------
    value : str | None
        Field value to sanitize.

    Returns
    -------
    str
        Sanitized value safe for CSV export.
    """
    if value is None:
        return ""
    if value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def _serialize_transaction(t: Transaction) -> dict[str, Any]:
    """
    Serialize a transaction to a dictionary for export.

    Parameters
    ----------
    t : Transaction
        Transaction model instance.

    Returns
    -------
    dict[str, Any]
        Dictionary with all export fields.
    """
    return {
        "date": t.date.isoformat(),
        "description": t.description,
        "amount": t.amount,
        "account": t.account,
        "bankin_category": t.bankin_category,
        "bankin_subcategory": t.bankin_subcategory,
        "money_map_type": t.money_map_type,
        "money_map_subcategory": t.money_map_subcategory,
        "is_manually_corrected": t.is_manually_corrected,
    }


def _get_month_export_data(
    month_repo: MonthRepository,
    transaction_repo: TransactionRepository,
    year: int,
    month: int,
) -> tuple[Month, list[Transaction]]:
    """
    Fetch month and transactions for export.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
    transaction_repo : TransactionRepository
        Repository for transaction data access.
    year : int
        Year (e.g., 2025).
    month : int
        Month number (1-12).

    Returns
    -------
    tuple[Month, list[Transaction]]
        Month record and list of all transactions.

    Raises
    ------
    MonthNotFoundError
        If month not found.
    TransactionQueryError
        If database query fails.
    """
    month_record = month_repo.get_by_year_month(year, month)

    if month_record is None:
        logger.info("Export requested for non-existent month: %d-%02d", year, month)
        raise MonthNotFoundError(month_id=-1)  # -1 indicates lookup by year/month

    transactions = transaction_repo.get_all_for_month(month_record.id)
    return month_record, transactions


def export_month_to_json(
    month_repo: MonthRepository,
    transaction_repo: TransactionRepository,
    year: int,
    month: int,
) -> ExportResult:
    """
    Export month data as JSON.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
    transaction_repo : TransactionRepository
        Repository for transaction data access.
    year : int
        Year (e.g., 2025).
    month : int
        Month number (1-12).

    Returns
    -------
    ExportResult
        Export result with JSON content, filename, and media type.

    Raises
    ------
    MonthNotFoundError
        If month not found.
    MonthDataError
        If database query fails (includes TransactionQueryError).
    ExportSerializationError
        If JSON serialization fails due to non-serializable data.
    """
    month_record, transactions = _get_month_export_data(month_repo, transaction_repo, year, month)

    export_data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "month": {
            "year": month_record.year,
            "month": month_record.month,
            "total_income": month_record.total_income,
            "total_core": month_record.total_core,
            "total_choice": month_record.total_choice,
            "total_compound": month_record.total_compound,
            "core_percentage": month_record.core_percentage,
            "choice_percentage": month_record.choice_percentage,
            "compound_percentage": month_record.compound_percentage,
            "score": month_record.score,
            "score_label": month_record.score_label,
        },
        "transactions": [_serialize_transaction(t) for t in transactions],
        "transaction_count": len(transactions),
    }

    try:
        json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
    except TypeError as error:
        logger.error("JSON serialization failed for %d-%02d: %s", year, month, str(error))
        raise ExportSerializationError(year, month, str(error)) from error

    filename = f"moneymap-{year}-{month:02d}.json"

    logger.info("Generated JSON export for %d-%02d with %d transactions", year, month, len(transactions))

    return ExportResult(
        content=json_content.encode("utf-8"),
        filename=filename,
        media_type="application/json",
    )


def export_month_to_csv(
    month_repo: MonthRepository,
    transaction_repo: TransactionRepository,
    year: int,
    month: int,
) -> ExportResult:
    """
    Export month transactions as CSV.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
    transaction_repo : TransactionRepository
        Repository for transaction data access.
    year : int
        Year (e.g., 2025).
    month : int
        Month number (1-12).

    Returns
    -------
    ExportResult
        Export result with CSV content, filename, and media type.

    Raises
    ------
    MonthNotFoundError
        If month not found.
    TransactionQueryError
        If database query fails.
    """
    _, transactions = _get_month_export_data(month_repo, transaction_repo, year, month)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(EXPORT_HEADERS)

    for t in transactions:
        writer.writerow(
            [
                t.date.isoformat(),
                _sanitize_csv_field(t.description),
                _sanitize_csv_field(t.account),
                t.amount,
                _sanitize_csv_field(t.bankin_category),
                _sanitize_csv_field(t.bankin_subcategory),
                t.money_map_type,
                _sanitize_csv_field(t.money_map_subcategory),
                str(t.is_manually_corrected).lower(),
            ]
        )

    filename = f"moneymap-{year}-{month:02d}.csv"

    logger.info("Generated CSV export for %d-%02d with %d transactions", year, month, len(transactions))

    return ExportResult(
        content=output.getvalue().encode("utf-8"),
        filename=filename,
        media_type="text/csv",
    )
