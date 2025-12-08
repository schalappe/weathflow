# Implementation: BankinCSVParser and Quality Assurance

**Date:** 2025-12-08
**Task Groups:** 3 (BankinCSVParser Class) and 4 (Quality Assurance)
**Implementer:** implement-task command

## Summary

Implemented the `BankinCSVParser` class that parses Bankin' CSV exports (French locale, semicolon-separated) and groups transactions by month. The implementation includes comprehensive unit tests, linting, type checking, and edge case coverage.

## Architecture Approach

Selected a **single-class parser** with private helper methods:

- Clean separation of concerns (normalization, validation, parsing, grouping)
- Standard library `csv.DictReader` for parsing (no pandas dependency)
- `strptime` for date parsing (readable approach)
- Exception chaining for proper error context

## Files Created

- `backend/app/services/csv_parser.py` - BankinCSVParser class (289 lines)
  - `EXPECTED_COLUMNS` class variable with 8 Bankin' columns
  - `parse()` main entry point
  - `_normalize_content()`, `_validate_columns()`, `_parse_date()`, `_parse_amount()`, `_parse_pointed()`, `_parse_row()`, `_calculate_summary()`, `_group_by_month()`

- `backend/tests/units/services/test_csv_parser.py` - Unit tests (235 lines)
  - 15 test cases across 5 test classes
  - Coverage: valid parsing, errors, summaries, boolean conversion, edge cases

## Key Implementation Details

### Parser Methods

| Method | Purpose |
|--------|---------|
| `parse(file_content)` | Orchestrates parsing flow, returns `ParseResult` |
| `_normalize_content()` | Decodes bytes to UTF-8 string |
| `_validate_columns()` | Checks all 8 required columns present |
| `_parse_date()` | Parses DD/MM/YYYY using `strptime` |
| `_parse_amount()` | Handles French comma decimal, quantizes to 2 places |
| `_parse_pointed()` | Case-insensitive "Oui" to True |
| `_parse_row()` | Maps CSV row to `ParsedTransaction` |
| `_calculate_summary()` | Computes income/expenses for a month |
| `_group_by_month()` | Groups by YYYY-MM key, sorts chronologically |

### Error Handling

- `InvalidFormatError`: Empty file or missing header
- `MissingColumnsError`: Lists missing column names
- `RowParseError`: Includes 1-based line number for debugging

### Type Fixes

Fixed 3 mypy errors:
1. Changed `list[str]` to `Sequence[str]` for `_validate_columns()` parameter
2. Added `Decimal("0")` as start value for `sum()` to avoid `Literal[0]` union

## Integration Points

- `ParsedTransaction` fields align with `Transaction` SQLAlchemy model
- `MonthSummary` fields mirror `Month` model structure
- Parser is stateless and reusable

## Testing Notes

15 unit tests covering:

| Test Class | Tests | Focus |
|------------|-------|-------|
| `TestBankinCSVParserValidCSV` | 4 | Valid parsing, multi-month, French decimal |
| `TestBankinCSVParserErrors` | 4 | Empty file, missing columns, invalid data |
| `TestBankinCSVParserSummary` | 1 | Income/expense calculation |
| `TestBankinCSVParserPointedField` | 2 | Boolean conversion |
| `TestBankinCSVParserEdgeCases` | 4 | Multi-year, period decimal, bytes input |

All tests use `unittest.TestCase` following project patterns.
