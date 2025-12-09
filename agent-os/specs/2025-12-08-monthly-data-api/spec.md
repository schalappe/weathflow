# Specification: Monthly Data API

## Goal

Create FastAPI endpoints to retrieve month data (totals, percentages, score) and transaction lists with filtering and pagination capabilities.

## User Stories

- As a user, I want to see a list of all my imported months with their Money Map scores so that I can track my budget progress over time
- As a user, I want to view detailed transaction data for a specific month with filtering options so that I can analyze my spending patterns

## Specific Requirements

**GET /api/months - List All Months:**

- Returns all months ordered by date (most recent first)
- Each month includes: id, year, month, totals (income/core/choice/compound), percentages, score, score_label, transaction_count, timestamps
- Response wrapper includes `months` array and `total` count
- No pagination needed (expected < 100 months per user)

**GET /api/months/{year}/{month} - Get Month Detail:**

- Path parameters: `year` (int), `month` (int, 1-12)
- Returns month summary data plus paginated transaction list
- Returns 404 with `{"detail": "Month not found"}` when month doesn't exist
- Validates month is 1-12 (FastAPI/Pydantic constraint)

**Transaction Filtering (Query Parameters):**

- `category_type`: Filter by MoneyMapType enum (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED)
- `start_date`: Filter transactions >= this date (ISO format)
- `end_date`: Filter transactions <= this date (ISO format)
- `search`: Case-insensitive partial match on description using SQL `ILIKE`
- All filters combine with AND logic

**Pagination (Query Parameters):**

- `page`: Page number (default: 1, min: 1)
- `page_size`: Items per page (default: 50, min: 1, max: 100)
- Response includes `pagination` object: page, page_size, total_items, total_pages
- Transactions ordered by date descending within page

**Response Schema: MonthSummary:**

- Fields: id, year, month, total_income, total_core, total_choice, total_compound, core_percentage, choice_percentage, compound_percentage, score, score_label, transaction_count, created_at, updated_at
- Used in list endpoint and nested in detail endpoint

**Response Schema: TransactionResponse:**

- Fields: id, date, description, account, amount, bankin_category, bankin_subcategory, money_map_type, money_map_subcategory, is_manually_corrected
- `account` and subcategory fields are nullable

**Response Schema: PaginationInfo:**

- Fields: page, page_size, total_items, total_pages
- `total_pages` calculated as `ceil(total_items / page_size)`

## Visual Design

No visual assets provided - this is a backend API specification.

## Existing Code to Leverage

**Router Pattern - `backend/app/routers/upload.py`**

- What it does: Defines `/api/upload` and `/api/categorize` endpoints with dependency injection
- How to reuse: Copy structure for `APIRouter(prefix="/api", tags=["months"])`, use same `Depends(get_db)` pattern
- Key methods/exports: HTTPException handling, Query() for parameters, NumPy docstrings
- Found by: code-explorer analysis of upload router

**Database Models - `backend/app/db/models/month.py` and `transaction.py`**

- What it does: SQLAlchemy 2.0 models with Mapped[] syntax, relationships, constraints
- How to reuse: Query directly - no modifications needed, all required fields exist
- Key methods/exports: Month.transactions relationship, Transaction.month_id FK
- Found by: code-explorer analysis of DB models

**Enums - `backend/app/db/enums.py`**

- What it does: Defines MoneyMapType and ScoreLabel enums
- How to reuse: Import MoneyMapType for query parameter validation
- Key methods/exports: `MoneyMapType`, `ScoreLabel`, `SCORE_TO_LABEL`
- Found by: code-explorer analysis of score service

**Database Session - `backend/app/db/database.py`**

- What it does: Provides `get_db()` generator for FastAPI dependency injection
- How to reuse: Import and use with `Depends(get_db)` in router endpoints
- Key methods/exports: `get_db()` -> Generator[Session, None, None]
- Found by: code-explorer analysis of upload router

**Schema Patterns - `backend/app/schemas/upload.py`**

- What it does: Pydantic BaseModel with Field() validation, Literal types
- How to reuse: Follow same patterns for response schemas, use `Field(ge=, le=)` for constraints
- Key methods/exports: Response model structure, validation patterns
- Found by: code-explorer analysis of existing schemas

## Architecture Approach

**Component Design:**

- Router (`routers/months.py`): Two endpoints, thin controller, delegates to service
- Service (`services/months.py`): Query logic, filtering, pagination - receives db per call
- Schemas (`schemas/months.py`): Response models only (no request bodies for GET endpoints)

**Data Flow:**

- List: Router → Service.get_all_months() → Query Month ordered by date → Transform to MonthSummary with transaction_count
- Detail: Router → Service.get_month_by_year_month() → 404 if None → Service.get_transactions_filtered() → Build response with pagination

**Integration Points:**

- Register router in `main.py`: `from app.routers import months` + `app.include_router(months.router)`
- Use existing `get_db` dependency for database sessions
- Use `MoneyMapType` enum for category_type query parameter validation

**Query Implementation:**

- List months: `db.query(Month).order_by(Month.year.desc(), Month.month.desc()).all()`
- Filter transactions: Chain `.filter()` calls for each provided filter, use `.ilike()` for search
- Paginate: `.offset((page - 1) * page_size).limit(page_size)` after getting count

## Out of Scope

- Advice generation or retrieval (handled by Advice API - roadmap item #15)
- Historical trend aggregation across months (handled by Historical Data API - roadmap item #10)
- Transaction editing or category correction (roadmap item #9)
- Data export to JSON/CSV (roadmap item #18)
- Authentication or authorization (not in current MVP scope)
- Caching or performance optimization beyond existing indexes
- Eager loading optimization (lazy loading acceptable for small datasets)
- Creating, updating, or deleting months (handled by Upload API)
- Variance from 50/30/20 targets (not in requirements)
- POST/PUT/DELETE methods for these endpoints
