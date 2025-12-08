# Specification: CSV Parser Service

## Goal

Build a stateless service that parses Bankin' CSV exports (French locale, semicolon-separated), validates format, detects all months present, groups transactions by month, and returns structured Pydantic models with summaries.

## User Stories

- As a user, I want to upload my Bankin' CSV export so that my transactions are automatically parsed and organized by month
- As a user, I want clear error messages with line numbers when my CSV has formatting issues so I can fix them

## Specific Requirements

**CSV Format Validation:**

- Validate semicolon separator and UTF-8 encoding
- Require all 8 Bankin' columns: Date, Description, Compte, Montant, Catégorie, Sous-Catégorie, Note, Pointée
- Raise `MissingColumnsError` listing missing columns if any are absent
- Raise `InvalidFormatError` if file is empty or has no header

**French Date Parsing:**

- Parse DD/MM/YYYY format (e.g., "31/10/2025" → `date(2025, 10, 31)`)
- Raise `RowParseError` with line number for invalid dates
- Use standard library parsing, not external date libraries

**French Decimal Parsing:**

- Convert comma decimal separator to Decimal (e.g., "1234,56" → `Decimal("1234.56")`)
- Also accept period separator for robustness
- Quantize all amounts to 2 decimal places
- Raise `RowParseError` with line number for invalid amounts

**Boolean Conversion:**

- Convert "Oui" to `True`, anything else to `False` for Pointée field
- Case-insensitive comparison

**Month Detection and Grouping:**

- Extract year-month from each transaction date
- Group transactions into `dict[str, MonthData]` with key format "YYYY-MM"
- Sort months chronologically (oldest first)
- Handle files spanning multiple years correctly

**Summary Calculation:**

- Count transactions per month
- Sum positive amounts as `total_income`
- Sum absolute negative amounts as `total_expenses`
- Round all sums to 2 decimal places

**Service Interface:**

- Single public method: `parse(file_content: bytes | str) -> ParseResult`
- Accept both bytes (UTF-8) and string input
- Stateless class design allowing safe reuse
- Use standard library `csv.DictReader` with semicolon delimiter

**Error Handling:**

- Fail fast: validate columns before parsing any rows
- Include line numbers in all `RowParseError` exceptions (1-based, header is line 1)
- Chain exceptions with `raise ... from e` for context

## Visual Design

No visual assets provided. This is a backend service with no UI components.

## Existing Code to Leverage

**Transaction Model - `backend/app/db/models/transaction.py`**

- What it does: Defines the Transaction SQLAlchemy model with `bankin_category`, `bankin_subcategory`, `account` fields
- How to reuse: Field names in `ParsedTransaction` should align for easy database mapping later
- Key fields: `date`, `description`, `amount`, `account`, `bankin_category`, `bankin_subcategory`

**Month Model - `backend/app/db/models/month.py`**

- What it does: Defines Month model with `year`, `month` fields and totals
- How to reuse: `MonthSummary` fields mirror the Month model structure
- Key fields: `year`, `month`, `total_income`

**Enum Pattern - `backend/app/db/enums.py`**

- What it does: Demonstrates `(str, Enum)` inheritance pattern
- How to reuse: Follow same pattern if enum needed (not required for this service)

**Test Base Class - `backend/tests/conftest.py`**

- What it does: Provides `DatabaseTestCase` with in-memory SQLite
- How to reuse: CSV parser tests don't need database, use plain `unittest.TestCase`

**Utility Function - `backend/app/db/models/base.py`**

- What it does: Provides `utc_now()` for timestamps
- How to reuse: Follow same pattern for any utility functions

## Architecture Approach

**Component Design:**

- `backend/app/services/exceptions.py`: Exception hierarchy (`CSVParseError`, `InvalidFormatError`, `MissingColumnsError`, `RowParseError`)
- `backend/app/services/csv_parser.py`: `BankinCSVParser` class + Pydantic models (`ParsedTransaction`, `MonthSummary`, `MonthData`, `ParseResult`)

**Data Flow:**

1. `parse()` receives `bytes | str` → `_normalize_content()` converts to string
2. `csv.DictReader` parses with semicolon delimiter
3. `_validate_columns()` checks all 8 columns present (fail fast)
4. Loop: `_parse_row()` calls `_parse_date()`, `_parse_amount()`, `_parse_pointed()` for each row
5. `_group_by_month()` groups transactions, calls `_calculate_summary()` per month
6. Return `ParseResult` with sorted months dict

**Method Responsibilities:**

| Method                 | Responsibility                                      |
| ---------------------- | --------------------------------------------------- |
| `parse()`              | Orchestrate full parsing flow, return `ParseResult` |
| `_normalize_content()` | Convert bytes to UTF-8 string                       |
| `_validate_columns()`  | Check required columns, raise `MissingColumnsError` |
| `_parse_row()`         | Parse single CSV row to `ParsedTransaction`         |
| `_parse_date()`        | DD/MM/YYYY → `date`, raise `RowParseError`          |
| `_parse_amount()`      | French decimal → `Decimal`, raise `RowParseError`   |
| `_parse_pointed()`     | Oui/Non → `bool`                                    |
| `_group_by_month()`    | Group transactions, sort chronologically            |
| `_calculate_summary()` | Compute income/expenses/count for one month         |

**Integration Points:**

- This service is standalone with no external dependencies
- Future upload router will call `parser.parse(file_content)` and persist results
- `ParsedTransaction` fields map directly to `Transaction` model columns

## Out of Scope

- Duplicate transaction detection (separate service)
- Money Map categorization (Claude API service)
- Database persistence (upload router responsibility)
- API endpoint implementation (router responsibility)
- File upload handling (router responsibility)
- CSV export/download (separate feature)
- Caching of parsed results
- Streaming very large files (2000+ transactions sufficient)
- Non-Bankin' CSV formats
- Localization of error messages
