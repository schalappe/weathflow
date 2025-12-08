# Task Breakdown: Upload and Categorize API

## Overview

| Metric               | Value                        |
| -------------------- | ---------------------------- |
| Total Tasks          | 18                           |
| Estimated Complexity | Medium                       |
| Primary Stack        | FastAPI + Python 3.12        |
| New Files            | 3 (router, schemas, service) |
| Modified Files       | 1 (exceptions.py)            |

## Task List

### Schema Layer

#### Task Group 1: Pydantic Request/Response Models

**Dependencies:** None

- [x] 1.0 Complete schema layer
  - [x] 1.1 Create `backend/app/schemas/__init__.py` (empty package marker)
  - [x] 1.2 Create upload response schemas
    - `MonthSummaryResponse`: year, month, transaction_count, total_income, total_expenses
    - `TransactionPreview`: date, description, amount
    - `UploadResponse`: success, total_transactions, months_detected, preview_by_month
    - Follow pattern from: `backend/app/services/schemas/_base.py`
  - [x] 1.3 Create categorize request/response schemas
    - `CategorizeRequest`: months_to_process (list[str]), import_mode (Literal["replace", "merge"])
    - `MonthResult`: year, month, transactions_categorized, low_confidence_count, score, score_label
    - `CategorizeResponse`: success, months_processed, total_api_calls
  - [x] 1.4 Verify schemas import without errors
    - Run: `cd backend && uv run python -c "from app.schemas.upload import *"`

**Acceptance Criteria:**

- All schemas defined with proper type annotations
- Validation works for import_mode (only "replace" or "merge")
- Schemas can be imported without errors

---

### Exception Layer

#### Task Group 2: Upload-Specific Exceptions

**Dependencies:** None (can run parallel with Task Group 1)

- [x] 2.0 Complete exception layer
  - [x] 2.1 Add upload exceptions to `backend/app/services/exceptions.py`
    - `UploadError(Exception)`: Base exception for upload operations
    - `InvalidMonthFormatError(UploadError)`: When month format is not YYYY-MM (include `value` attribute)
    - `NoTransactionsFoundError(UploadError)`: When CSV contains no transactions
  - [x] 2.2 Verify exceptions import correctly
    - Run: `cd backend && uv run python -c "from app.services.exceptions import UploadError, InvalidMonthFormatError, NoTransactionsFoundError"`

**Acceptance Criteria:**

- Exceptions follow existing hierarchy pattern
- Each exception has meaningful error message
- Exceptions can be imported without errors

---

### Service Layer

#### Task Group 3: UploadService - Preview Functionality

**Dependencies:** Task Group 1, Task Group 2

- [x] 3.0 Complete upload preview functionality
  - [x] 3.1 Write 3 focused tests for preview functionality
    - Test: `get_upload_preview` returns correct month summaries
    - Test: `get_upload_preview` includes transaction previews per month
    - Test: `get_upload_preview` handles parser errors correctly
  - [x] 3.2 Create `backend/app/services/upload.py` with class skeleton
    - Define `UploadService` class with `__init__`
    - Initialize `BankinCSVParser` in constructor
    - Define `LOW_CONFIDENCE_THRESHOLD = 0.8` constant
  - [x] 3.3 Implement `get_upload_preview(file_content: bytes) -> dict` method
    - Call `BankinCSVParser.parse(file_content)`
    - Transform `ParseResult` to response format
    - Build `months_detected` list from month summaries
    - Build `preview_by_month` dict with transaction lists
  - [x] 3.4 Ensure preview tests pass
    - Run: `cd backend && uv run pytest tests/units/services/test_upload.py -v -k "preview"`

**Acceptance Criteria:**

- Tests from 3.1 pass
- Preview returns correct structure matching `UploadResponse` schema
- Parser errors propagate correctly

---

#### Task Group 4: UploadService - Categorization Core

**Dependencies:** Task Group 3

- [x] 4.0 Complete categorization core functionality
  - [x] 4.1 Write 3 focused tests for categorization
    - Test: `process_categorization` categorizes transactions correctly
    - Test: `process_categorization` handles "all" months selection
    - Test: `process_categorization` tracks API call count
  - [x] 4.2 Add TransactionCategorizer initialization
    - Initialize with `ANTHROPIC_API_KEY` from environment
    - Add `_api_call_count` instance variable
  - [x] 4.3 Implement `_transform_to_input` helper method
    - Convert `ParsedTransaction` to `TransactionInput` format
    - Assign sequential IDs starting from `start_id`
  - [x] 4.4 Implement `_count_low_confidence` helper method
    - Count results where `confidence < LOW_CONFIDENCE_THRESHOLD`
  - [x] 4.5 Implement `process_categorization` method (core flow)
    - Parse CSV with `BankinCSVParser`
    - Filter months based on `months_to_process` (handle "all")
    - Validate month format (YYYY-MM), raise `InvalidMonthFormatError` if invalid
    - For each month: transform, categorize, track API calls
    - Return results dict
  - [x] 4.6 Ensure categorization tests pass
    - Run: `cd backend && uv run pytest tests/units/services/test_upload.py -v -k "categoriz"`

**Acceptance Criteria:**

- Tests from 4.1 pass
- Transactions are correctly transformed and categorized
- API call count is tracked accurately

---

#### Task Group 5: UploadService - Import Modes

**Dependencies:** Task Group 4

- [x] 5.0 Complete import mode functionality
  - [x] 5.1 Write 4 focused tests for import modes
    - Test: Replace mode deletes existing month before insert
    - Test: Replace mode creates new month and transactions
    - Test: Merge mode skips duplicate transactions
    - Test: Merge mode inserts only new transactions
  - [x] 5.2 Implement `_generate_transaction_key` helper method
    - Key format: `{date}_{description}_{amount}_{account}`
    - Used for duplicate detection in merge mode
  - [x] 5.3 Implement `_get_or_create_month` helper method
    - Query for existing month by year/month
    - Create new month if not found
    - Return month object
  - [x] 5.4 Implement `_handle_replace_mode` helper method
    - Delete existing month (cascade deletes transactions)
    - Use `db.delete()` with existing month object
  - [x] 5.5 Implement `_get_existing_transaction_keys` helper method
    - Query transactions for given month_id
    - Return set of transaction keys for duplicate detection
  - [x] 5.6 Implement `_persist_transactions` helper method
    - Create `Transaction` records with categorization results
    - Skip transactions with keys in `skip_keys` set (merge mode)
    - Use `db.add_all()` for bulk insert
    - Return count of inserted transactions
  - [x] 5.7 Integrate import modes into `process_categorization`
    - Add `import_mode` handling: "replace" or "merge"
    - Call `calculate_and_update_month` after persisting
    - Build and return `MonthResult` for each processed month
  - [x] 5.8 Ensure import mode tests pass
    - Run: `cd backend && uv run pytest tests/units/services/test_upload.py -v -k "mode"`

**Acceptance Criteria:**

- Tests from 5.1 pass
- Replace mode completely overwrites existing data
- Merge mode correctly detects and skips duplicates
- Score is calculated after persistence

---

### Router Layer

#### Task Group 6: FastAPI Router - Upload Endpoint

**Dependencies:** Task Group 3

- [x] 6.0 Complete upload endpoint
  - [x] 6.1 Write 3 focused tests for upload endpoint
    - Test: Valid CSV returns 200 with month summaries
    - Test: Invalid CSV format returns 400
    - Test: Empty file returns 400
  - [x] 6.2 Create `backend/app/routers/__init__.py` (empty package marker)
  - [x] 6.3 Create `backend/app/routers/upload.py` with router skeleton
    - Create `APIRouter(prefix="/api", tags=["upload"])`
    - Import schemas, services, and exceptions
  - [x] 6.4 Implement `POST /api/upload` endpoint
    - Accept `file: UploadFile = File(...)`
    - Read file content as bytes: `await file.read()`
    - Call `UploadService.get_upload_preview()`
    - Map `CSVParseError` to `HTTPException(400)`
    - Return `UploadResponse`
  - [x] 6.5 Ensure upload endpoint tests pass
    - Run: `cd backend && uv run pytest tests/units/routers/test_upload.py -v -k "upload"`

**Acceptance Criteria:**

- Tests from 6.1 pass
- Endpoint accepts multipart/form-data file upload
- Errors return appropriate HTTP status codes

---

#### Task Group 7: FastAPI Router - Categorize Endpoint

**Dependencies:** Task Group 5, Task Group 6

- [x] 7.0 Complete categorize endpoint
  - [x] 7.1 Write 4 focused tests for categorize endpoint
    - Test: Valid request returns 200 with month results
    - Test: Invalid month format returns 400
    - Test: Invalid import mode returns 400 (via Pydantic validation)
    - Test: Claude API error returns 502
  - [x] 7.2 Implement `POST /api/categorize` endpoint
    - Accept `file: UploadFile`, `months_to_process: list[str]`, `import_mode: str`
    - Inject database session: `db: Session = Depends(get_db)`
    - Validate import_mode is "replace" or "merge"
    - Call `UploadService.process_categorization()`
    - Map exceptions to HTTPException:
      - `CSVParseError` → 400
      - `InvalidMonthFormatError` → 400
      - `CategorizationError` → 502
    - Return `CategorizeResponse`
  - [x] 7.3 Ensure categorize endpoint tests pass
    - Run: `cd backend && uv run pytest tests/units/routers/test_upload.py -v -k "categorize"`

**Acceptance Criteria:**

- Tests from 7.1 pass
- Endpoint accepts file + form parameters
- Errors mapped to correct HTTP status codes
- Response includes all month results and API call count

---

### Integration Layer

#### Task Group 8: App Integration

**Dependencies:** Task Group 6, Task Group 7

- [ ] 8.0 Complete app integration
  - [ ] 8.1 Register router in main app
    - Add `from app.routers import upload` to `main.py`
    - Add `app.include_router(upload.router)`
  - [ ] 8.2 Verify endpoints are accessible
    - Run: `cd backend && uv run uvicorn app.main:app --reload`
    - Check: `curl -X POST http://localhost:8000/api/upload` returns 422 (missing file)
    - Check: `curl http://localhost:8000/docs` shows upload endpoints

**Acceptance Criteria:**

- Router is registered in the FastAPI app
- Endpoints appear in OpenAPI docs (`/docs`)
- Endpoints respond to requests

---

### Testing Layer

#### Task Group 9: Test Review & Integration Tests

**Dependencies:** Task Groups 1-8

- [ ] 9.0 Complete test review and integration tests
  - [ ] 9.1 Review existing tests from Task Groups 3-7
    - Service tests: ~10 tests from groups 3, 4, 5
    - Router tests: ~7 tests from groups 6, 7
    - Total: ~17 tests
  - [ ] 9.2 Write up to 5 integration tests
    - Test: Full upload → categorize → verify database (replace mode)
    - Test: Full upload → categorize → verify database (merge mode)
    - Test: Multi-month file processing end-to-end
    - Test: Partial success (some months fail categorization)
    - Test: Claude API mock failure handling
  - [ ] 9.3 Run all feature tests
    - Run: `cd backend && uv run pytest tests/units/services/test_upload.py tests/units/routers/test_upload.py tests/integration/test_upload_flow.py -v`
    - Expected: ~22 tests pass

**Acceptance Criteria:**

- All feature-specific tests pass (~22 tests)
- Critical end-to-end workflows covered
- No more than 5 integration tests added

---

## Execution Order

```text
Task Group 1 (Schemas) ──────┐
                             ├──► Task Group 3 (Preview) ──► Task Group 4 (Core) ──► Task Group 5 (Modes) ──┐
Task Group 2 (Exceptions) ───┘                                                                              │
                                                                                                            ▼
                             ┌──────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
Task Group 6 (Upload EP) ──► Task Group 7 (Categorize EP) ──► Task Group 8 (Integration) ──► Task Group 9 (Tests)
```

**Recommended Sequence:**

1. **Task Groups 1 & 2** (parallel) - Foundation: schemas and exceptions
2. **Task Group 3** - Preview functionality (enables upload endpoint)
3. **Task Group 6** - Upload endpoint (can be tested independently)
4. **Task Group 4** - Categorization core
5. **Task Group 5** - Import modes (replace/merge)
6. **Task Group 7** - Categorize endpoint
7. **Task Group 8** - App integration
8. **Task Group 9** - Final testing

---

## File Creation Summary

| File                                          | Task Group | Size       |
| --------------------------------------------- | ---------- | ---------- |
| `backend/app/schemas/__init__.py`             | 1          | ~0 lines   |
| `backend/app/schemas/upload.py`               | 1          | ~50 lines  |
| `backend/app/services/upload.py`              | 3, 4, 5    | ~180 lines |
| `backend/app/routers/__init__.py`             | 6          | ~0 lines   |
| `backend/app/routers/upload.py`               | 6, 7       | ~80 lines  |
| `backend/app/services/exceptions.py` (modify) | 2          | +20 lines  |
| `backend/app/main.py` (modify)                | 8          | +3 lines   |
| `tests/units/services/test_upload.py`         | 3, 4, 5    | ~150 lines |
| `tests/units/routers/test_upload.py`          | 6, 7       | ~120 lines |
| `tests/integration/test_upload_flow.py`       | 9          | ~100 lines |
