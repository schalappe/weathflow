"""Upload service for CSV processing and transaction categorization."""

import re
from math import ceil
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.services.calculator import calculate_and_update_month
from app.services.categorizer import TransactionCategorizer
from app.services.csv_parser import BankinCSVParser
from app.services.exceptions import InvalidMonthFormatError, NoTransactionsFoundError
from app.services.schemas.categorization import CategorizationResult, TransactionInput
from app.services.schemas.parsing import MonthData, ParsedTransaction

LOW_CONFIDENCE_THRESHOLD = 0.8
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class UploadService:
    """
    Orchestrates CSV upload, parsing, categorization, and persistence.

    Uses existing services (BankinCSVParser, TransactionCategorizer, calculator)
    to process uploaded CSV files and persist categorized transactions.

    Examples
    --------
    >>> service = UploadService()
    >>> preview = service.get_upload_preview(csv_bytes)
    >>> result = service.process_categorization(csv_bytes, ["2025-01"], "replace", db)
    """

    def __init__(self) -> None:
        """Initialize with parser instance. Categorizer is created lazily."""
        self._parser = BankinCSVParser()
        self._categorizer: TransactionCategorizer | None = None
        self._api_call_count = 0

    def _get_categorizer(self) -> TransactionCategorizer:
        """
        Get or create the categorizer instance.

        Raises
        ------
        CategorizationError
            If ANTHROPIC_API_KEY is not configured in settings.
        """
        if self._categorizer is None:
            settings = get_settings()
            api_key = settings.anthropic_api_key.get_secret_value()
            base_url = settings.anthropic_base_url
            self._categorizer = TransactionCategorizer(api_key=api_key, base_url=base_url)
        return self._categorizer

    def get_upload_preview(self, file_content: bytes) -> dict[str, Any]:
        """
        Parse CSV and return preview of detected months.

        Parameters
        ----------
        file_content : bytes
            Raw CSV file content.

        Returns
        -------
        dict
            Preview with success, total_transactions, months_detected, preview_by_month.

        Raises
        ------
        CSVParseError
            If CSV format is invalid or missing required columns.
        NoTransactionsFoundError
            If no transactions found in the file.
        """
        result = self._parser.parse(file_content)

        if result.total_transactions == 0:
            raise NoTransactionsFoundError()

        months_detected = []
        preview_by_month: dict[str, list[dict[str, Any]]] = {}

        for month_key, month_data in result.months.items():
            months_detected.append(
                {
                    "year": month_data.year,
                    "month": month_data.month,
                    "transaction_count": month_data.summary.transaction_count,
                    "total_income": float(month_data.summary.total_income),
                    "total_expenses": float(month_data.summary.total_expenses),
                }
            )

            preview_by_month[month_key] = [
                {
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "amount": float(t.amount),
                }
                for t in month_data.transactions
            ]

        return {
            "success": True,
            "total_transactions": result.total_transactions,
            "months_detected": months_detected,
            "preview_by_month": preview_by_month,
        }

    def process_categorization(
        self,
        file_content: bytes,
        months_to_process: list[str],
        import_mode: Literal["replace", "merge"],
        db: Session,
    ) -> dict[str, Any]:
        """
        Parse, categorize, and persist transactions for selected months.

        Parameters
        ----------
        file_content : bytes
            Raw CSV file content.
        months_to_process : list[str]
            List of months to process in YYYY-MM format, or ["all"] for all months.
        import_mode : Literal["replace", "merge"]
            "replace" deletes existing month and all its transactions, creating fresh.
            "merge" preserves existing month and transactions, only adding new ones.
        db : Session
            Database session for persistence.

        Returns
        -------
        dict[str, Any]
            Keys: success (bool), months_processed (list), months_not_found (list),
            total_api_calls (int). Months requested but not in CSV are listed in
            months_not_found rather than causing an error.

        Raises
        ------
        CSVParseError
            If CSV format is invalid.
        NoTransactionsFoundError
            If no transactions found in the file.
        InvalidMonthFormatError
            If month format is not YYYY-MM.
        CategorizationError
            If Claude API fails.
        ScoreCalculationError
            If score calculation or persistence fails.
        """
        self._api_call_count = 0
        result = self._parser.parse(file_content)

        if result.total_transactions == 0:
            raise NoTransactionsFoundError()

        # ##>: Handle "all" months selection.
        target_months = list(result.months.keys()) if months_to_process == ["all"] else months_to_process

        # ##>: Validate month formats before processing.
        for month_key in target_months:
            if not MONTH_PATTERN.match(month_key):
                raise InvalidMonthFormatError(month_key)

        months_processed = []
        months_not_found = []

        for month_key in target_months:
            if month_key not in result.months:
                months_not_found.append(month_key)
                continue

            month_data = result.months[month_key]
            month_result = self._process_single_month(
                db=db,
                month_data=month_data,
                import_mode=import_mode,
            )
            months_processed.append(month_result)

        return {
            "success": True,
            "months_processed": months_processed,
            "months_not_found": months_not_found,
            "total_api_calls": self._api_call_count,
        }

    def _process_single_month(
        self,
        db: Session,
        month_data: MonthData,
        import_mode: Literal["replace", "merge"],
    ) -> dict[str, Any]:
        """Process categorization and persistence for a single month."""
        year, month = month_data.year, month_data.month

        # ##>: Handle import mode and get month record.
        if import_mode == "replace":
            month_record = self._handle_replace_mode(db, year, month)
            skip_keys: set[str] = set()
        else:
            month_record, skip_keys = self._handle_merge_mode(db, year, month)

        # ##>: Transform and categorize transactions. IDs start at 1 for each month.
        inputs = self._transform_to_inputs(month_data.transactions, start_id=1)
        categorizer = self._get_categorizer()
        results = categorizer.categorize(inputs)

        # ##>: Track API calls (estimate based on batch size of 50).
        pending_count = len(inputs)
        self._api_call_count += ceil(pending_count / 50)

        # ##>: Persist transactions and calculate score.
        inserted_count = self._persist_transactions(
            db=db,
            month_id=month_record.id,
            transactions=month_data.transactions,
            results=results,
            skip_keys=skip_keys,
        )

        # ##>: Flush to make transactions visible for aggregation query, but don't commit yet.
        db.flush()
        # ##>: Let calculate_and_update_month handle the final commit for atomicity.
        updated_month = calculate_and_update_month(db, month_record.id)

        low_confidence_count = self._count_low_confidence(results)

        return {
            "year": year,
            "month": month,
            "transactions_categorized": inserted_count,
            "low_confidence_count": low_confidence_count,
            "score": updated_month.score,
            "score_label": updated_month.score_label,
        }

    def _transform_to_inputs(self, transactions: list[ParsedTransaction], start_id: int) -> list[TransactionInput]:
        """Convert ParsedTransaction list to TransactionInput list."""
        return [
            TransactionInput(
                id=start_id + i,
                date=t.date.isoformat(),
                description=t.description,
                amount=float(t.amount),
                bankin_category=t.bankin_category,
                bankin_subcategory=t.bankin_subcategory,
            )
            for i, t in enumerate(transactions)
        ]

    def _count_low_confidence(self, results: list[CategorizationResult]) -> int:
        """Count results with confidence below threshold."""
        return sum(1 for r in results if r.confidence < LOW_CONFIDENCE_THRESHOLD)

    def _generate_transaction_key(self, t: ParsedTransaction) -> str:
        """Generate unique key for duplicate detection."""
        return f"{t.date.isoformat()}_{t.description}_{float(t.amount)}_{t.account}"

    def _handle_replace_mode(self, db: Session, year: int, month: int) -> Month:
        """Delete existing month and create new one."""
        existing = db.query(Month).filter(Month.year == year, Month.month == month).first()
        if existing:
            db.delete(existing)
            db.flush()

        new_month = Month(year=year, month=month)
        db.add(new_month)
        db.flush()
        return new_month

    def _handle_merge_mode(self, db: Session, year: int, month: int) -> tuple[Month, set[str]]:
        """Get or create month and return existing transaction keys."""
        existing = db.query(Month).filter(Month.year == year, Month.month == month).first()

        if existing:
            skip_keys = self._get_existing_transaction_keys(db, existing.id)
            return existing, skip_keys

        new_month = Month(year=year, month=month)
        db.add(new_month)
        db.flush()
        return new_month, set()

    def _get_existing_transaction_keys(self, db: Session, month_id: int) -> set[str]:
        """Get transaction keys for duplicate detection."""
        transactions = db.query(Transaction).filter(Transaction.month_id == month_id).all()
        # ##>: Use float() to match key format from _generate_transaction_key.
        return {f"{t.date.isoformat()}_{t.description}_{float(t.amount)}_{t.account}" for t in transactions}

    def _persist_transactions(
        self,
        db: Session,
        month_id: int,
        transactions: list[ParsedTransaction],
        results: list[CategorizationResult],
        skip_keys: set[str],
    ) -> int:
        """Persist categorized transactions, skipping duplicates in merge mode."""
        result_by_id: dict[int, CategorizationResult] = {r.id: r for r in results}
        new_transactions = []

        for i, t in enumerate(transactions):
            tx_key = self._generate_transaction_key(t)
            if tx_key in skip_keys:
                continue

            # ##>: IDs start at 1 for each month's batch, matching _transform_to_inputs.
            result = result_by_id.get(i + 1)
            if result is None:
                continue

            new_transactions.append(
                Transaction(
                    month_id=month_id,
                    date=t.date,
                    description=t.description,
                    amount=float(t.amount),
                    account=t.account,
                    bankin_category=t.bankin_category,
                    bankin_subcategory=t.bankin_subcategory,
                    money_map_type=result.money_map_type.value,
                    money_map_subcategory=result.money_map_subcategory,
                )
            )

        if new_transactions:
            db.add_all(new_transactions)

        return len(new_transactions)
