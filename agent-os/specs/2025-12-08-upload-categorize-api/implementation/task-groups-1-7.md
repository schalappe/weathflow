# Implementation: Task Groups 1-7 (Upload and Categorize API)

**Date:** 2025-12-08
**Task Groups:** 1-7 (Schemas, Exceptions, Preview, Categorization, Import Modes, Upload Endpoint, Categorize Endpoint)
**Implementer:** implement-task command

## Summary

Implemented the complete Upload and Categorize API feature for Money Map Manager. This includes two FastAPI endpoints (`POST /api/upload` and `POST /api/categorize`) that allow users to upload Bankin' CSV exports, preview detected months, and trigger AI-powered categorization with database persistence.

## Architecture Approach

**Chosen: Hybrid (Minimal Changes + Clean Architecture)**

- Schemas placed in `app/schemas/upload.py` (separate API layer)
- Thin orchestrator service (`UploadService`) coordinating existing services
- Query parameters for `months_to_process` and `import_mode` in categorize endpoint
- Re-upload pattern (stateless API, no server-side session storage)

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/schemas/__init__.py` | Empty package marker | 0 |
| `backend/app/schemas/upload.py` | API request/response Pydantic models | 50 |
| `backend/app/services/upload.py` | UploadService orchestrator | 310 |
| `backend/app/routers/__init__.py` | Empty package marker | 0 |
| `backend/app/routers/upload.py` | FastAPI router with 2 endpoints | 110 |
| `backend/app/main.py` | FastAPI application entry point | 35 |
| `backend/tests/units/services/test_upload.py` | Unit tests for UploadService | 600 |
| `backend/tests/units/routers/__init__.py` | Empty package marker | 0 |
| `backend/tests/units/routers/test_upload.py` | Unit tests for router endpoints | 180 |

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/exceptions.py` | Added `UploadError`, `InvalidMonthFormatError`, `NoTransactionsFoundError` (+35 lines) |
| `backend/pyproject.toml` | Added FastAPI, uvicorn, python-multipart, httpx dependencies |

## Key Implementation Details

### Schemas (`app/schemas/upload.py`)

- `UploadResponse`: Preview with `months_detected` list and `preview_by_month` dict
- `CategorizeResponse`: Results with `months_processed` and `total_api_calls`
- `MonthResult`: Per-month categorization result with score
- `ImportMode`: Literal type for "replace" or "merge"

### UploadService (`app/services/upload.py`)

- `get_upload_preview()`: Parses CSV, returns month summaries without database access
- `process_categorization()`: Full flow - parse, filter months, categorize, persist, calculate score
- Replace mode: Uses cascade delete (deleting Month auto-deletes Transactions)
- Merge mode: Generates transaction keys for duplicate detection
- API call tracking: Estimates calls based on batch size (50 transactions/call)

### Router (`app/routers/upload.py`)

- `POST /api/upload`: Accepts multipart file, returns preview
- `POST /api/categorize`: Accepts file + query params, returns categorization results
- Exception mapping: CSVParseError → 400, CategorizationError → 502
- Validates empty months list, returns 400 if no valid months provided

### main.py

- FastAPI app with CORS configured for localhost:3000
- Router registered at `/api` prefix
- Database initialization on startup via `init_db()`

## Integration Points

1. **BankinCSVParser**: Reused for CSV parsing, returns `ParseResult` with grouped transactions
2. **TransactionCategorizer**: Reused for AI categorization, returns `CategorizationResult` list
3. **calculate_and_update_month**: Called after persisting transactions to calculate Money Map score
4. **get_db**: FastAPI dependency injection for database sessions

## Testing Notes

**Unit Tests Created:**

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_upload.py` (services) | 11 | Preview, categorization, import modes, validation |
| `test_upload.py` (routers) | 9 | Endpoint behavior, error responses, parameter parsing |

**Test Results:** All 20 new tests pass, 157 total tests in the suite pass.

## Design Decisions

1. **ID Reset per Month**: Transaction IDs start at 1 for each month's batch to simplify result mapping
2. **Float Conversion**: Decimal amounts converted to float for API/database consistency
3. **Actual API Call Count**: Returns estimated count based on batch size (ceil(transactions/50))
4. **Empty Months Validation**: Router validates that months_to_process is not empty after parsing
