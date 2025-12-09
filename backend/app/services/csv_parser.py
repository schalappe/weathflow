"""CSV parser for Bankin' export files."""

import csv
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import ClassVar

from app.services.dto.parsing import MonthData, ParsedMonthSummary, ParsedTransaction, ParseResult
from app.services.exceptions import InvalidFormatError, MissingColumnsError, RowParseError


class BankinCSVParser:
    """
    Parse Bankin' CSV exports and group transactions by month.

    This parser handles the French locale format used by Bankin':
    - Semicolon-separated values
    - Date format: DD/MM/YYYY
    - Decimal format: comma as separator (e.g., "1234,56")
    - Boolean: "Oui"/"Non" for reconciliation status

    Examples
    --------
    >>> parser = BankinCSVParser()
    >>> result = parser.parse(csv_content)
    >>> for month_key, month_data in result.months.items():
    ...     print(f"{month_key}: {month_data.summary.transaction_count} transactions")
    """

    EXPECTED_COLUMNS: ClassVar[list[str]] = [
        "Date",
        "Description",
        "Compte",
        "Montant",
        "Catégorie",
        "Sous-Catégorie",
        "Note",
        "Pointée",
    ]

    def parse(self, file_content: bytes | str) -> ParseResult:
        """
        Parse CSV content and return structured data grouped by month.

        Parameters
        ----------
        file_content : bytes | str
            Raw CSV file content. If bytes, decoded as UTF-8.

        Returns
        -------
        ParseResult
            Parsed transactions grouped by month with summaries.

        Raises
        ------
        InvalidFormatError
            If file is empty or has no header row.
        MissingColumnsError
            If required columns are missing from the header.
        RowParseError
            If a specific row cannot be parsed (includes line number).
        """
        content = self._normalize_content(file_content)

        if not content.strip():
            raise InvalidFormatError("File is empty")

        reader = csv.DictReader(StringIO(content), delimiter=";")
        self._validate_columns(reader.fieldnames)

        transactions: list[ParsedTransaction] = []
        for line_number, row in enumerate(reader, start=2):
            transaction = self._parse_row(row, line_number)
            transactions.append(transaction)

        months = self._group_by_month(transactions)

        return ParseResult(total_transactions=len(transactions), months=months)

    def _normalize_content(self, file_content: bytes | str) -> str:
        """
        Convert bytes to UTF-8 string if needed.

        Parameters
        ----------
        file_content : bytes | str
            Raw file content.

        Returns
        -------
        str
            UTF-8 decoded string.
        """
        if isinstance(file_content, bytes):
            return file_content.decode("utf-8")
        return file_content

    def _validate_columns(self, fieldnames: Sequence[str] | None) -> None:
        """
        Validate that all required columns are present.

        Parameters
        ----------
        fieldnames : Sequence[str] | None
            Column names from CSV header.

        Raises
        ------
        InvalidFormatError
            If fieldnames is None (no header).
        MissingColumnsError
            If any required columns are missing.
        """
        if fieldnames is None:
            raise InvalidFormatError("File has no header row")

        missing = [col for col in self.EXPECTED_COLUMNS if col not in fieldnames]
        if missing:
            raise MissingColumnsError(missing)

    def _parse_date(self, date_str: str, line_number: int) -> date:
        """
        Parse French date format DD/MM/YYYY.

        Parameters
        ----------
        date_str : str
            Date string in DD/MM/YYYY format.
        line_number : int
            Current line number for error reporting.

        Returns
        -------
        date
            Parsed date object.

        Raises
        ------
        RowParseError
            If date format is invalid.
        """
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError as e:
            raise RowParseError(f"Invalid date format '{date_str}'", line_number) from e

    def _parse_amount(self, amount_str: str, line_number: int) -> Decimal:
        """
        Parse French decimal format with comma separator.

        Parameters
        ----------
        amount_str : str
            Amount string (e.g., "1234,56" or "1234.56").
        line_number : int
            Current line number for error reporting.

        Returns
        -------
        Decimal
            Parsed amount with 2 decimal places.

        Raises
        ------
        RowParseError
            If amount format is invalid.
        """
        try:
            normalized = amount_str.replace(",", ".")
            return Decimal(normalized).quantize(Decimal("0.01"))
        except InvalidOperation as e:
            raise RowParseError(f"Invalid amount format '{amount_str}'", line_number) from e

    def _parse_pointed(self, value: str) -> bool:
        """
        Convert Pointée field to boolean.

        Parameters
        ----------
        value : str
            String value from CSV ("Oui", "Non", etc.).

        Returns
        -------
        bool
            True if value is "Oui" (case-insensitive), False otherwise.
        """
        return value.strip().lower() == "oui"

    def _parse_row(self, row: dict[str, str], line_number: int) -> ParsedTransaction:
        """
        Parse a single CSV row into a ParsedTransaction.

        Parameters
        ----------
        row : dict[str, str]
            Dictionary of column name to value.
        line_number : int
            Current line number for error reporting.

        Returns
        -------
        ParsedTransaction
            Parsed transaction object.

        Raises
        ------
        RowParseError
            If any field cannot be parsed.
        """
        note_value = row["Note"].strip()

        return ParsedTransaction(
            date=self._parse_date(row["Date"], line_number),
            description=row["Description"],
            account=row["Compte"],
            amount=self._parse_amount(row["Montant"], line_number),
            bankin_category=row["Catégorie"],
            bankin_subcategory=row["Sous-Catégorie"],
            note=note_value if note_value else None,
            is_pointed=self._parse_pointed(row["Pointée"]),
        )

    def _calculate_summary(self, transactions: list[ParsedTransaction], year: int, month: int) -> ParsedMonthSummary:
        """
        Calculate summary statistics for a list of transactions.

        Parameters
        ----------
        transactions : list[ParsedTransaction]
            Transactions to summarize.
        year : int
            Year for this summary.
        month : int
            Month (1-12) for this summary.

        Returns
        -------
        ParsedMonthSummary
            Aggregated statistics.
        """
        total_income = sum((t.amount for t in transactions if t.amount > 0), Decimal("0"))
        total_expenses = sum((abs(t.amount) for t in transactions if t.amount < 0), Decimal("0"))

        return ParsedMonthSummary(
            year=year,
            month=month,
            transaction_count=len(transactions),
            total_income=total_income.quantize(Decimal("0.01")),
            total_expenses=total_expenses.quantize(Decimal("0.01")),
        )

    def _group_by_month(self, transactions: list[ParsedTransaction]) -> dict[str, MonthData]:
        """
        Group transactions by month and calculate summaries.

        Parameters
        ----------
        transactions : list[ParsedTransaction]
            All parsed transactions.

        Returns
        -------
        dict[str, MonthData]
            Transactions grouped by "YYYY-MM" key, sorted chronologically.
        """
        grouped: dict[str, list[ParsedTransaction]] = defaultdict(list)

        for transaction in transactions:
            key = f"{transaction.date.year:04d}-{transaction.date.month:02d}"
            grouped[key].append(transaction)

        months: dict[str, MonthData] = {}
        for key in sorted(grouped.keys()):
            month_transactions = grouped[key]
            year, month = int(key[:4]), int(key[5:7])

            months[key] = MonthData(
                year=year,
                month=month,
                transactions=month_transactions,
                summary=self._calculate_summary(month_transactions, year, month),
            )

        return months
