# Task Breakdown: CSV Parser Service

## Overview

Total Tasks: 4 Task Groups, 16 Sub-tasks

This is a backend-only service. No UI components required.

## Task List

### Foundation Layer

#### Task Group 1: Exception Hierarchy and Package Setup

**Dependencies:** None
**Estimated Time:** 30-45 minutes

- [x] 1.0 Complete exception hierarchy and package setup
  - [x] 1.1 Create services package structure
    - Create `backend/app/services/__init__.py` (empty)
    - Create `backend/tests/units/services/__init__.py` (empty)
  - [x] 1.2 Create exception hierarchy in `backend/app/services/exceptions.py`
    - `CSVParseError`: Base exception for all CSV parsing errors
    - `InvalidFormatError`: Empty file or no header
    - `MissingColumnsError`: Store `missing: list[str]` attribute, message lists missing columns
    - `RowParseError`: Store `line_number: int` attribute, message includes line number
    - Follow NumPy docstring style for all classes

**Acceptance Criteria:**

- Package structure created
- All 4 exception classes defined with proper attributes
- Exception messages are clear and actionable
- Type annotations on all `__init__` parameters

---

### Data Models Layer

#### Task Group 2: Pydantic Models

**Dependencies:** None (can run parallel with Task Group 1)
**Estimated Time:** 30-45 minutes

- [x] 2.0 Complete Pydantic models
  - [x] 2.1 Create `ParsedTransaction` model in `backend/app/services/schemas.py`
    - Fields: `date`, `description`, `account`, `amount` (Decimal), `bankin_category`, `bankin_subcategory`, `note` (optional), `is_pointed`
    - Use `ConfigDict(frozen=True)` for immutability
    - Field names align with Transaction SQLAlchemy model
  - [x] 2.2 Create `MonthSummary` model
    - Fields: `year`, `month`, `transaction_count`, `total_income` (Decimal), `total_expenses` (Decimal)
    - Use `ConfigDict(frozen=True)`
  - [x] 2.3 Create `MonthData` model
    - Fields: `year`, `month`, `transactions: list[ParsedTransaction]`, `summary: MonthSummary`
    - Use `ConfigDict(frozen=True)`
  - [x] 2.4 Create `ParseResult` model
    - Fields: `total_transactions: int`, `months: dict[str, MonthData]`
    - Use `ConfigDict(frozen=True)`

**Acceptance Criteria:**

- All 4 Pydantic models defined
- All models use `frozen=True` configuration
- `Decimal` used for all financial amounts
- Modern union syntax (`str | None`) for optional fields

---

### Parser Implementation Layer

#### Task Group 3: BankinCSVParser Class

**Dependencies:** Task Groups 1 and 2
**Estimated Time:** 1.5-2 hours

- [x] 3.0 Complete BankinCSVParser implementation
  - [x] 3.1 Write 6-8 focused unit tests in `backend/tests/units/services/test_csv_parser.py`
    - Test valid CSV parsing with single transaction
    - Test valid CSV parsing with multiple months
    - Test empty file raises `InvalidFormatError`
    - Test missing columns raises `MissingColumnsError`
    - Test invalid date raises `RowParseError` with line number
    - Test invalid amount raises `RowParseError` with line number
    - Test French decimal format (comma) parsed correctly
    - Test month grouping and chronological sorting
  - [x] 3.2 Create `BankinCSVParser` class skeleton
    - Define `EXPECTED_COLUMNS` class variable with all 8 column names
    - Add class docstring with usage example
    - Define public `parse()` method signature
  - [x] 3.3 Implement `_normalize_content()` method
    - Convert `bytes` to `str` using UTF-8 decoding
    - Return string unchanged if already string
  - [x] 3.4 Implement `_validate_columns()` method
    - Check if `fieldnames` is None → raise `InvalidFormatError`
    - Find missing columns → raise `MissingColumnsError(missing)`
  - [x] 3.5 Implement `_parse_date()` method
    - Split DD/MM/YYYY by `/`
    - Create `date(year, month, day)` object
    - Wrap in try/except → raise `RowParseError` with line number
  - [x] 3.6 Implement `_parse_amount()` method
    - Replace comma with period for French decimal
    - Convert to `Decimal` and quantize to 2 places
    - Wrap in try/except → raise `RowParseError` with line number
  - [x] 3.7 Implement `_parse_pointed()` method
    - Case-insensitive check for "oui" → return `True`
    - All other values → return `False`
  - [x] 3.8 Implement `_parse_row()` method
    - Call `_parse_date()`, `_parse_amount()`, `_parse_pointed()`
    - Map CSV columns to `ParsedTransaction` fields
    - Handle empty `Note` field as `None`
  - [x] 3.9 Implement `_calculate_summary()` method
    - Sum positive amounts as `total_income`
    - Sum absolute negative amounts as `total_expenses`
    - Count transactions
    - Quantize sums to 2 decimal places
  - [x] 3.10 Implement `_group_by_month()` method
    - Group transactions by "YYYY-MM" key
    - Sort keys chronologically
    - Create `MonthData` with summary for each month
  - [x] 3.11 Implement `parse()` method (main entry point)
    - Call `_normalize_content()`
    - Create `csv.DictReader` with semicolon delimiter
    - Call `_validate_columns()`
    - Loop rows calling `_parse_row()` (line numbers start at 2)
    - Call `_group_by_month()`
    - Return `ParseResult`
  - [x] 3.12 Run tests and verify all pass
    - Run only the 6-8 tests from step 3.1
    - Fix any failing tests
    - Do NOT run entire test suite yet

**Acceptance Criteria:**

- All 6-8 unit tests pass
- Parser handles valid Bankin' CSV correctly
- Error messages include line numbers
- Months sorted chronologically
- All amounts use `Decimal` with 2 decimal places

---

### Validation Layer

#### Task Group 4: Quality Assurance and Final Testing

**Dependencies:** Task Group 3
**Estimated Time:** 30-45 minutes

- [x] 4.0 Complete quality assurance
  - [x] 4.1 Run linting and fix issues
    - Run `uv run ruff check backend/app/services/`
    - Run `uv run ruff format backend/app/services/`
    - Fix any linting errors
  - [x] 4.2 Run type checking and fix issues
    - Run `uv run mypy backend/app/services/`
    - Fix any type errors
    - Ensure all functions have complete type annotations
  - [x] 4.3 Review test coverage and add up to 4 additional tests if needed
    - Review existing 6-8 tests for gaps
    - Add tests for edge cases only if critical:
      - Multi-year file spanning (e.g., Dec 2024 + Jan 2025)
      - Single transaction file
      - Period decimal format (robustness check)
      - Empty optional fields (Note column)
    - Maximum 4 additional tests
  - [x] 4.4 Run full feature test suite
    - Run `uv run pytest backend/tests/units/services/ -v`
    - Verify all tests pass (expected: 10-12 tests total)
    - Check test output for any warnings

**Acceptance Criteria:**

- Zero linting errors
- Zero type checking errors
- All tests pass (10-12 total)
- Code follows project conventions (119 char lines, NumPy docstrings)

---

## Execution Order

```text
┌─────────────────────────────────────────┐
│  Task Group 1: Exceptions (30-45 min)   │──┐
└─────────────────────────────────────────┘  │
                                             ├──▶ Task Group 3: Parser (1.5-2 hrs)
┌─────────────────────────────────────────┐  │         │
│  Task Group 2: Pydantic (30-45 min)     │──┘         │
└─────────────────────────────────────────┘            ▼
                                             ┌─────────────────────────────────────┐
                                             │  Task Group 4: QA (30-45 min)       │
                                             └─────────────────────────────────────┘
```

**Recommended sequence:**

1. **Task Groups 1 & 2** can run in parallel (no dependencies between them)
2. **Task Group 3** requires both 1 & 2 complete
3. **Task Group 4** requires Task Group 3 complete

**Total estimated time:** 3-4 hours

---

## Files Created/Modified

| File                                              | Action         | Task Group |
| ------------------------------------------------- | -------------- | ---------- |
| `backend/app/services/__init__.py`                | Create (empty) | 1          |
| `backend/app/services/exceptions.py`              | Create         | 1          |
| `backend/app/services/schemas.py`                 | Create         | 2          |
| `backend/app/services/csv_parser.py`              | Create         | 3          |
| `backend/tests/units/services/__init__.py`        | Create (empty) | 1          |
| `backend/tests/units/services/test_exceptions.py` | Create         | 1          |
| `backend/tests/units/services/test_schemas.py`    | Create         | 2          |
| `backend/tests/units/services/test_csv_parser.py` | Create         | 3, 4       |

---

## Test Summary

| Phase           | Tests Written           | Cumulative      |
| --------------- | ----------------------- | --------------- |
| Task Group 3.1  | 6-8 core tests          | 6-8             |
| Task Group 4.3  | Up to 4 edge case tests | 10-12           |
| **Final Total** | -                       | **10-12 tests** |
