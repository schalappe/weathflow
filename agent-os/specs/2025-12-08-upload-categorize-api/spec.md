# Specification: Upload and Categorize API

## Goal

Build two FastAPI endpoints that allow users to upload a Bankin' CSV file, preview detected months, and trigger AI-powered categorization with database persistence using replace or merge import modes.

## User Stories

- As a user, I want to upload my Bankin' CSV export so that I can preview which months are included and their transaction summaries before processing.
- As a user, I want to trigger categorization for selected months so that transactions are automatically categorized and my Money Map score is calculated.

## Specific Requirements

**POST /api/upload Endpoint:**

- Accept CSV file via `multipart/form-data` with field name `file`
- Parse using existing `BankinCSVParser` service
- Return preview with month summaries (year, month, count, income, expenses)
- Include full transaction list per month in `preview_by_month` dict
- Return 400 for invalid CSV format or missing required columns

**POST /api/categorize Endpoint:**

- Accept CSV file (re-upload), `months_to_process` list, and `import_mode` parameter
- Support `months_to_process: ["all"]` to process all detected months
- Validate `import_mode` is either "replace" or "merge"
- Re-parse CSV to get transactions (stateless API design)
- Return 400 for invalid month format (expected `YYYY-MM`)
- Return 502 if Claude API is unavailable

**Replace Import Mode:**

- Delete existing Month record (cascade deletes all transactions)
- Create new Month and Transaction records
- Calculate and persist score after transactions are saved

**Merge Import Mode:**

- Skip transactions that already exist in database
- Duplicate detection key: `{date}_{description}_{amount}_{account}`
- Only insert new transactions, preserve existing data
- Recalculate score after new transactions are added

**Categorization Processing:**

- Transform `ParsedTransaction` to `TransactionInput` format for categorizer
- Use existing `TransactionCategorizer` service (batches 50 per API call)
- Track `low_confidence_count` for transactions with confidence < 0.8
- Track `total_api_calls` for cost monitoring

**Score Calculation:**

- After persisting transactions, call `calculate_and_update_month(db, month_id)`
- Return score (0-3) and score_label (POOR, NEED_IMPROVEMENT, OKAY, GREAT) in response

**Error Handling:**

- `InvalidFormatError` → 400 with detail message
- `MissingColumnsError` → 400 with missing column names
- `NoTransactionsFoundError` → 400 with "No transactions found"
- `InvalidMonthFormatError` → 400 with "Invalid month format"
- `APIConnectionError` → 502 with "Categorization service unavailable"

**Response Schemas:**

- `UploadResponse`: success, total_transactions, months_detected, preview_by_month
- `CategorizeResponse`: success, months_processed, total_api_calls
- `MonthResult`: year, month, transactions_categorized, low_confidence_count, score, score_label

## Existing Code to Leverage

**BankinCSVParser - `backend/app/services/csv_parser.py`**

- What it does: Parses Bankin' CSV exports, groups transactions by month
- How to reuse: Instantiate and call `parse(file_content: bytes | str) -> ParseResult`
- Key methods: `parse()` returns `ParseResult` with `months: dict[str, MonthData]`
- Found by: code-explorer analysis of existing services

**TransactionCategorizer - `backend/app/services/categorizer.py`**

- What it does: Categorizes transactions via Claude API with caching
- How to reuse: Initialize with `api_key`, call `categorize(list[TransactionInput])`
- Key methods: `categorize()` returns `list[CategorizationResult]` with money_map_type
- Found by: code-explorer analysis of existing services

**Score Calculator - `backend/app/services/calculator.py`**

- What it does: Calculates Money Map percentages and scores
- How to reuse: Call `calculate_and_update_month(db, month_id)` after persisting transactions
- Key methods: Updates Month record with totals, percentages, score, and score_label
- Found by: code-explorer analysis of existing services

**Database Models - `backend/app/db/models/`**

- What it does: ORM models for Month and Transaction with cascade delete
- How to reuse: Create/query using SQLAlchemy session from `Depends(get_db)`
- Key methods: `db.add()`, `db.add_all()`, `db.delete()`, `db.commit()`
- Found by: code-explorer analysis of database patterns

**Service Exceptions - `backend/app/services/exceptions.py`**

- What it does: Provides exception hierarchy for error handling
- How to reuse: Import and catch `CSVParseError`, `CategorizationError` in router
- Key methods: Each exception has meaningful attributes (e.g., `missing` columns)
- Found by: code-explorer analysis of existing services

## Architecture Approach

**Component Design:**

- `upload.py` router: Thin controller handling HTTP concerns only
- `UploadService`: Orchestrator coordinating parser, categorizer, and calculator
- `upload.py` schemas: Pydantic models for request/response validation

**Data Flow:**

- Upload: File → BankinCSVParser.parse() → Transform to response format → JSON
- Categorize: File → Parse → Filter months → For each month: Categorize → Handle import mode → Persist → Calculate score → JSON

**Integration Points:**

- Router uses `Depends(get_db)` for database session injection
- Router maps service exceptions to HTTPException with appropriate status codes
- UploadService initializes services with environment config (ANTHROPIC_API_KEY)

**Key Design Decisions:**

- Stateless re-upload approach (no session management)
- One database transaction per month (partial success possible)
- API call count estimated from batch size (50 transactions per call)

## Out of Scope

- Frontend upload UI (roadmap item #7)
- Progress indicators or WebSocket updates
- Database schema changes (models already exist)
- New service business logic (services already exist)
- Real-time categorization progress feedback
- Retry logic for partial month failures
- CSV format auto-detection (Bankin' format only)
- Transaction editing or manual categorization
- Advice generation (separate feature)
- File size limits or upload validation
