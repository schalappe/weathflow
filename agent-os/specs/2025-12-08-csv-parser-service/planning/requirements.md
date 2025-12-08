# Spec Requirements: CSV Parser Service

## Initial Description

Build a service that parses Bankin' CSV exports, detects all months present, groups transactions by month, and returns structured data with summaries.

## Requirements Discussion

### Source Document

All requirements are derived from the existing specification at:
`docs/product-development/features/02-csv-parser-service.md`

### Key Requirements (from spec)

**Q1: What is the Bankin' CSV format?**
**Answer:** Semicolon-separated, French locale, UTF-8 encoding with columns:

- Date (DD/MM/YYYY)
- Description
- Compte (Account)
- Montant (Amount - French decimal with comma)
- Catégorie
- Sous-Catégorie
- Note (optional)
- Pointée (Oui/Non boolean)

**Q2: How are months detected and grouped?**
**Answer:** Extract year and month from each transaction date, group by YYYY-MM format, sort chronologically (oldest first).

**Q3: What summary metrics are needed?**
**Answer:**

- `transaction_count`: Number of transactions
- `total_income`: Sum of positive amounts
- `total_expenses`: Sum of absolute negative amounts
- All rounded to 2 decimal places

**Q4: What is the service interface?**
**Answer:** Pure Python class `BankinCSVParser` with a `parse(file_content: bytes | str) -> ParseResult` method.

**Q5: How should errors be handled?**
**Answer:** Fail fast on invalid format with:

- Clear, actionable error messages
- Line numbers in parsing errors
- Specific error types: `CSVParseError`, `InvalidFormatError`, `MissingColumnsError`, `RowParseError`

**Q6: Should Bankin' categories be preserved?**
**Answer:** Yes, in `bankin_category` and `bankin_subcategory` fields.

### Existing Code to Reference

**Similar Features Identified:**

- Model: `backend/app/db/models/transaction.py` - Transaction model with `bankin_category`, `bankin_subcategory` fields
- Model: `backend/app/db/models/month.py` - Month model for grouping
- Enum: `backend/app/db/enums.py` - MoneyMapType enum

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

N/A - This is a backend service with no UI components.

## Requirements Summary

### Functional Requirements

**FR1: CSV Format Validation:**

- Validate Bankin' CSV format (semicolon-separated, UTF-8)
- Reject files missing required columns with clear error message
- Handle French date format (DD/MM/YYYY)

**FR2: Transaction Parsing:**

- Parse each row into `ParsedTransaction` Pydantic model
- Convert French decimal format (comma) to Decimal
- Handle empty optional fields (Note)
- Convert "Oui/Non" to boolean for Pointée

**FR3: Month Detection and Grouping:**

- Extract year and month from transaction dates
- Group transactions by month key (YYYY-MM format)
- Sort months chronologically (oldest first)
- Handle files spanning multiple years

**FR4: Month Summaries:**

- Count transactions per month
- Sum positive amounts as income
- Sum absolute negative amounts as expenses
- Round to 2 decimal places

**FR5: Complete Parse Result:**

- Return `ParseResult` with `total_transactions` and `months` dict
- Each month contains `MonthData` with transactions and summary

### Reusability Opportunities

- Pydantic models for data validation (`ParsedTransaction`, `MonthSummary`, `MonthData`, `ParseResult`)
- Error hierarchy pattern from existing codebase
- Service class pattern matching other services in `backend/app/services/`

### Scope Boundaries

**In Scope:**

- Parsing Bankin' CSV format
- Validating file structure and columns
- Detecting months present in file
- Grouping transactions by month
- Calculating monthly summaries (count, income, expenses)
- Returning structured Pydantic models

**Out of Scope:**

- Duplicate detection (separate service)
- Transaction categorization (Claude API service)
- Database persistence (handled by upload router)
- API endpoint implementation (handled by router)

### Technical Considerations

- File location: `backend/app/services/csv_parser.py`
- Dependencies: `pydantic`, `pandas`, standard library (`csv`, `datetime`, `decimal`)
- Performance: Parse 2000+ transactions in < 2 seconds
- Memory efficient (stream large files if needed)

### Testing Requirements

**Unit Tests (14 test cases):**

- Valid CSV parsing
- Empty file handling
- Missing columns error
- French date/decimal format parsing
- Month grouping and sorting
- Multi-month/multi-year files
- Income/expense calculation
- Optional field handling
- Boolean conversion (Oui/Non)
- Invalid format errors

**Integration Tests (2 test cases):**

- Parse real Bankin' export file
- Large file performance verification
