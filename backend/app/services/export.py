"""Service functions for exporting month data to various formats."""

import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services import months as months_service
from app.services.exceptions import MonthNotFoundError

logger = logging.getLogger(__name__)

# ##>: CSV field headers for export (used by both JSON and CSV exports).
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


def _get_month_export_data(db: Session, year: int, month: int) -> tuple[Month, list[Transaction]]:
    """
    Fetch month and transactions for export.

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
    tuple[Month, list[Transaction]]
        Month record and list of all transactions.

    Raises
    ------
    MonthNotFoundError
        If month not found.
    TransactionQueryError
        If database query fails.
    """
    month_record = months_service.get_month_by_year_month(db, year, month)

    if month_record is None:
        logger.info("Export requested for non-existent month: %d-%02d", year, month)
        raise MonthNotFoundError(month_id=-1)  # -1 indicates lookup by year/month

    transactions = months_service.get_all_transactions_for_month(db, month_record.id)
    return month_record, transactions


def export_month_to_json(db: Session, year: int, month: int) -> ExportResult:
    """
    Export month data as JSON.

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
    ExportResult
        Export result with JSON content, filename, and media type.

    Raises
    ------
    MonthNotFoundError
        If month not found.
    TransactionQueryError
        If database query fails.
    """
    month_record, transactions = _get_month_export_data(db, year, month)

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

    json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"moneymap-{year}-{month:02d}.json"

    logger.info("Generated JSON export for %d-%02d with %d transactions", year, month, len(transactions))

    return ExportResult(
        content=json_content.encode("utf-8"),
        filename=filename,
        media_type="application/json",
    )


def export_month_to_csv(db: Session, year: int, month: int) -> ExportResult:
    """
    Export month transactions as CSV.

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
    ExportResult
        Export result with CSV content, filename, and media type.

    Raises
    ------
    MonthNotFoundError
        If month not found.
    TransactionQueryError
        If database query fails.
    """
    _, transactions = _get_month_export_data(db, year, month)

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
