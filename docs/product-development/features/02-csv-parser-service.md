# CSV Parser Service Specification

## Overview

Build a service that parses Bankin' CSV exports, detects all months present, groups transactions by month, and returns structured data with summaries.

---

## Problem Statement

Users export their transaction data from Bankin' as CSV files. These files can contain multiple months of data. The system needs to:

1. Parse the specific Bankin' CSV format (semicolon-separated, French locale)
2. Validate the file structure matches expected columns
3. Detect all months present in the file
4. Group transactions by month (year + month)
5. Provide summaries per month (count, income, expenses)

---

## Functional Requirements

### FR1: CSV Format Validation

The service must validate that uploaded files match the Bankin' CSV format.

**Expected Columns:**

| Column         | Type   | Description                    |
| -------------- | ------ | ------------------------------ |
| Date           | String | Format: DD/MM/YYYY             |
| Description    | String | Transaction description        |
| Compte         | String | Account name                   |
| Montant        | String | Amount (French decimal format) |
| Catégorie      | String | Bankin' category               |
| Sous-Catégorie | String | Bankin' subcategory            |
| Note           | String | User note (optional)           |
| Pointée        | String | Reconciliation status          |

**Acceptance Criteria:**

- [ ] Reject files missing required columns with clear error message
- [ ] Handle UTF-8 encoding
- [ ] Handle semicolon separator
- [ ] Handle French date format (DD/MM/YYYY)

### FR2: Transaction Parsing

Parse each row into a structured transaction object.

**Output Transaction Structure:**

```python
class ParsedTransaction(BaseModel):
    """Single parsed transaction from Bankin' CSV."""

    model_config = ConfigDict(frozen=True)

    date: date
    description: str
    account: str
    amount: Decimal
    bankin_category: str
    bankin_subcategory: str
    note: str | None = None
    is_pointed: bool = False
```

**Acceptance Criteria:**

- [ ] Parse dates from DD/MM/YYYY format
- [ ] Convert French decimal format (comma) to float
- [ ] Handle empty optional fields (Note)
- [ ] Convert "Oui/Non" to boolean for Pointée

### FR3: Month Detection and Grouping

Automatically detect and group transactions by month.

**Acceptance Criteria:**

- [ ] Extract year and month from each transaction date
- [ ] Group transactions by month key (YYYY-MM format)
- [ ] Sort months chronologically (oldest first)
- [ ] Handle files spanning multiple years

### FR4: Month Summaries

Calculate summary statistics for each detected month.

**Output Summary Structure:**

```python
class MonthSummary(BaseModel):
    """Summary statistics for a single month."""

    model_config = ConfigDict(frozen=True)

    year: int
    month: int
    transaction_count: int
    total_income: Decimal      # Sum of positive amounts
    total_expenses: Decimal    # Sum of negative amounts (absolute)
```

**Acceptance Criteria:**

- [ ] Count transactions per month
- [ ] Sum positive amounts as income
- [ ] Sum absolute negative amounts as expenses
- [ ] Round to 2 decimal places

### FR5: Complete Parse Result

Return a structured result containing all parsed data.

**Output Structure:**

```python
class MonthData(BaseModel):
    """All data for a single month."""

    model_config = ConfigDict(frozen=True)

    year: int
    month: int
    transactions: list[ParsedTransaction]
    summary: MonthSummary

class ParseResult(BaseModel):
    """Complete result from parsing a Bankin' CSV file."""

    model_config = ConfigDict(frozen=True)

    total_transactions: int
    months: dict[str, MonthData]  # Key: "YYYY-MM"
```

---

## Non-Functional Requirements

### NFR1: Performance

- Parse files with 2000+ transactions in < 2 seconds
- Memory efficient (stream large files if needed)

### NFR2: Error Handling

- Provide clear, actionable error messages
- Include line numbers in parsing errors
- Fail fast on invalid format

---

## Example Input/Output

### Input CSV

```csv
Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée
"31/10/2025";"Total Option System' Epargne";"Livret A";"4.67";"Entrées d'argent";"Economies";"";"Non"
"29/10/2025";"CB Domoro";"Compte De Dépôts";"-2.5";"Alimentation & Restau.";"Fast foods";"";"Non"
"29/10/2025";"Virement Salaire";"Compte De Dépôts";"2823.29";"Entrées d'argent";"Salaires";"";"Oui"
"15/09/2025";"CB Carrefour";"Compte De Dépôts";"-45.80";"Alimentation & Restau.";"Supermarché / Epicerie";"";"Non"
```

### Output

```python
ParseResult(
    total_transactions=4,
    months={
        "2025-09": MonthData(
            year=2025,
            month=9,
            transactions=[...],  # 1 transaction
            summary=MonthSummary(
                year=2025,
                month=9,
                transaction_count=1,
                total_income=Decimal("0.00"),
                total_expenses=Decimal("45.80")
            )
        ),
        "2025-10": MonthData(
            year=2025,
            month=10,
            transactions=[...],  # 3 transactions
            summary=MonthSummary(
                year=2025,
                month=10,
                transaction_count=3,
                total_income=Decimal("2827.96"),
                total_expenses=Decimal("2.50")
            )
        )
    }
)
```

---

## Technical Design

### File Location

```text
backend/app/services/csv_parser.py
```

### Class Design

```python
class BankinCSVParser:
    """
    Parse Bankin' CSV exports and group transactions by month.
    """

    EXPECTED_COLUMNS: ClassVar[list[str]] = [
        "Date", "Description", "Compte", "Montant",
        "Catégorie", "Sous-Catégorie", "Note", "Pointée"
    ]

    def parse(self, file_content: bytes | str) -> ParseResult:
        """
        Parse CSV content and return structured data grouped by month.

        Parameters
        ----------
        file_content : bytes | str
            Raw CSV file content.

        Returns
        -------
        ParseResult
            Parsed transactions grouped by month with summaries.

        Raises
        ------
        CSVParseError
            If file format is invalid or required columns are missing.
        """

    def _validate_columns(self, columns: list[str]) -> None:
        """Validate CSV has required Bankin' columns."""

    def _parse_row(self, row: dict[str, str], line_number: int) -> ParsedTransaction:
        """Parse a single CSV row into a transaction."""

    def _parse_date(self, date_str: str) -> date:
        """Parse French date format DD/MM/YYYY."""

    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse French decimal format (comma separator)."""
```

### Error Handling

```python
class CSVParseError(Exception):
    """Base exception for CSV parsing errors."""

class InvalidFormatError(CSVParseError):
    """Raised when CSV format doesn't match Bankin' export."""

class MissingColumnsError(CSVParseError):
    """Raised when required columns are missing."""

class RowParseError(CSVParseError):
    """Raised when a specific row cannot be parsed."""
    def __init__(self, message: str, line_number: int):
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}")
```

---

## Dependencies

- `pydantic` - Data validation and serialization
- `pandas` - CSV parsing and data manipulation
- Standard library: `csv`, `datetime`, `decimal`

---

## Testing Requirements

### Unit Tests

| Test Case                                 | Description                                  |
| ----------------------------------------- | -------------------------------------------- |
| `test_parse_valid_csv`                    | Parse a valid Bankin' CSV file               |
| `test_parse_empty_file`                   | Handle empty CSV gracefully                  |
| `test_parse_missing_columns`              | Raise error for missing required columns     |
| `test_parse_french_date_format`           | Correctly parse DD/MM/YYYY dates             |
| `test_parse_french_decimal_format`        | Correctly parse comma decimal separator      |
| `test_group_by_month`                     | Transactions grouped by YYYY-MM              |
| `test_multi_month_file`                   | Handle file spanning multiple months         |
| `test_multi_year_file`                    | Handle file spanning multiple years          |
| `test_calculate_income_expenses`          | Correct income/expense calculation           |
| `test_sort_months_chronologically`        | Months sorted oldest to newest               |
| `test_handle_empty_optional_fields`       | Handle empty Note field                      |
| `test_parse_pointed_boolean`              | Convert Oui/Non to boolean                   |
| `test_invalid_date_format`                | Raise error for invalid date                 |
| `test_invalid_amount_format`              | Raise error for invalid amount               |

### Integration Tests

| Test Case                           | Description                         |
| ----------------------------------- | ----------------------------------- |
| `test_parse_real_bankin_export`     | Parse actual Bankin' export file    |
| `test_large_file_performance`       | Verify < 2s for 2000+ transactions  |

---

## Out of Scope

- Duplicate detection (separate service)
- Transaction categorization (Claude API service)
- Database persistence (handled by upload router)
- API endpoint implementation (handled by router)
