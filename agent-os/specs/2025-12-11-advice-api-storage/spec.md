# Specification: Advice API and Storage

## Goal

Expose the existing Advice Generation Service via REST API endpoints, enabling clients to generate and retrieve personalized financial advice for any month, with automatic caching to avoid redundant Claude API calls.

## User Stories

- As a user, I want to generate personalized advice for a specific month so that I can understand my spending trends and receive actionable recommendations.
- As a user, I want to retrieve previously generated advice so that I can review recommendations without waiting for regeneration.

## Specific Requirements

**POST /api/advice/generate endpoint:**

- Accepts request body: `{year: int, month: int, regenerate: bool}`
- Returns cached advice if exists and `regenerate=False`
- Generates new advice via `AdviceGenerator` if no cache or `regenerate=True`
- Stores generated advice as JSON in `advice_text` column
- Returns `was_cached: bool` flag indicating if advice was freshly generated
- Response includes `generated_at` timestamp

**GET /api/advice/{year}/{month} endpoint:**

- Path parameters with validation: `year (2000-2100)`, `month (1-12)`
- Returns stored advice if exists with `exists: true`
- Returns `exists: false` with `advice: null` if no advice generated yet
- Does NOT auto-generate advice (explicit POST required)

**Advice storage format:**

- Serialize `AdviceResponse` to JSON: `{analysis, problem_areas, recommendations, encouragement}`
- Store in existing `Advice.advice_text` column (max 5000 chars)
- One advice record per month (upsert pattern: create or update)
- `generated_at` timestamp updated on each generation

**Data preparation for AdviceGenerator:**

- Convert `Month` model to `MonthData` DTO via direct field mapping
- Fetch last 3 months via `get_months_history(db, limit=3)`
- Filter current month from history list before passing to generator
- AdviceGenerator requires minimum 2 months (current + 1 history)

**Error handling:**

- 404: Month not found in database
- 400: Insufficient data (`InsufficientDataError` - fewer than 2 months)
- 503: Claude API unavailable (`AdviceAPIError`) or database error
- 500: Response parsing failure (`AdviceParseError`) or unexpected error

**Response models:**

- `GenerateAdviceResponse`: `{success, advice: AdviceData, generated_at, was_cached}`
- `GetAdviceResponse`: `{success, advice: AdviceData | null, generated_at, exists}`
- `AdviceData`: `{analysis, problem_areas: list[ProblemArea], recommendations, encouragement}`

## Visual Design

No visual assets provided. This is a backend-only feature (API endpoints).

## Existing Code to Leverage

**Router pattern - `backend/app/routers/months.py`**

- What it does: Defines monthly data API endpoints with error handling, path validation, dependency injection
- How to reuse: Replicate the same patterns for advice router (APIRouter setup, exception catching, HTTPException mapping)
- Key patterns: `Path(..., ge=, le=)` validation, `Depends(get_db)`, `response_model=`, error helper functions
- Found by: code-explorer analysis of months router

**AdviceGenerator - `backend/app/services/advisor.py`**

- What it does: Generates personalized advice via Claude API, validates input data, parses JSON response
- How to reuse: Import and instantiate with API key from settings, call `generate_advice(current_month, history)`
- Key methods: `generate_advice(current_month: MonthData, history: list[MonthData]) -> AdviceResponse`
- Found by: code-explorer analysis of advice infrastructure

**Advice DTOs - `backend/app/services/dto/advice.py`**

- What it does: Defines `MonthData`, `ProblemArea`, `AdviceResponse` as immutable Pydantic models
- How to reuse: Import `MonthData` for Month-to-DTO conversion, import `AdviceResponse` for type hints
- Key exports: `MonthData`, `ProblemArea`, `AdviceResponse`
- Found by: code-explorer analysis of advice infrastructure

**Advice model - `backend/app/db/models/advice.py`**

- What it does: SQLAlchemy model with `id`, `month_id`, `advice_text`, `generated_at`, indexed on `month_id`
- How to reuse: Query and persist advice records, model already exists with Month relationship
- Key fields: `advice_text` (JSON storage), `generated_at` (timestamp)
- Found by: code-explorer analysis of advice infrastructure

**Month service - `backend/app/services/months.py`**

- What it does: Provides `get_month_by_year_month()` and `get_months_history()` functions
- How to reuse: Import directly for month lookup and historical data retrieval
- Key functions: `get_month_by_year_month(db, year, month) -> Month | None`, `get_months_history(db, limit) -> list[Month]`
- Found by: code-explorer analysis of months service

## Architecture Approach

**Component Design:**

- `backend/app/routers/advice.py` - Thin router with 2 endpoints, delegates to service layer
- `backend/app/services/advice.py` - CRUD operations and Month-to-MonthData conversion
- `backend/app/responses/advice.py` - Pydantic response models with `from_json()` and `from_service_response()` converters
- Add `AdviceQueryError` to `backend/app/services/exceptions.py` for database errors

**Data Flow:**

- POST: Request → validate month exists → check cache → fetch history → convert to DTOs → generate via Claude → serialize JSON → store → response
- GET: Request → validate month exists → query advice → parse JSON → response

**Integration Points:**

- Wire router via `app.include_router(advice.router)` in `main.py`
- Use existing `get_db` dependency for database sessions
- Use `get_settings()` for `anthropic_api_key` and `anthropic_base_url`

## Out of Scope

- Rate limiting for Claude API calls
- Advice versioning/history (keeping multiple advice records per month)
- Advice Panel UI component (Feature 16)
- Category breakdown in MonthData (optional field, not stored in Month model)
- Automatic advice regeneration on transaction changes
- Advice expiration/TTL
- Bulk advice generation for multiple months
- Advice deletion endpoint
- Custom history window (fixed at 3 months)
- Advice comparison between months
