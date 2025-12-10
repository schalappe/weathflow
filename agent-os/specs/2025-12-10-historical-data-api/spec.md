# Specification: Historical Data API

## Goal

Extend the months API with a new endpoint that returns aggregated historical data for the last N months, enabling frontend visualization of score progression and spending trends over time.

## User Stories

- As a budget-conscious user, I want to see my Money Map score evolution over 12 months so that I can track my financial progress.
- As a user analyzing my spending, I want to see Core/Choice/Compound percentage trends so that I can identify areas needing improvement.

## Specific Requirements

**New API Endpoint:**

- Endpoint: `GET /api/months/history`
- Query parameter: `months` (int, default: 12, range: 1-24)
- Returns historical months with per-month totals, percentages, and scores
- Includes summary with trend analysis

**Response Structure - Months Array:**

- Each month includes: year, month, month_label (e.g., "Oct 2025")
- Financial data: total_income, total_core, total_choice, total_compound
- Percentages: core_percentage, choice_percentage, compound_percentage
- Score data: score (0-3), score_label ("Poor" to "Great")

**Response Structure - Summary Object:**

- `total_months`: Count of months returned
- `average_score`: Average across all months (float)
- `score_trend`: "improving" | "declining" | "stable"
- `best_month`: Reference to highest-scoring month (year, month, score)
- `worst_month`: Reference to lowest-scoring month (year, month, score)

**Score Trend Calculation:**

- Compare average score of last 3 months vs previous 3 months
- "improving": last 3 avg > previous 3 avg
- "declining": last 3 avg < previous 3 avg
- "stable": equal averages or fewer than 6 months of data

**Data Ordering and Gaps:**

- Months returned in chronological order (oldest first)
- Missing months (gaps) are excluded, not interpolated
- If requested months > available, return all available without error

**Performance Requirement:**

- Response time < 100ms for 12 months of data
- Single database query with LIMIT clause

**Error Handling:**

- 503 for database errors (MonthDataError)
- 500 for unexpected errors
- Empty database returns empty months array with zeroed summary

## Visual Design

No visual assets provided. This is a backend-only API feature. Frontend charts are separate roadmap items (#11-13).

## Existing Code to Leverage

**Router Pattern - `backend/app/routers/months.py`**

- What it does: Handles `/api/months` and `/api/months/{year}/{month}` endpoints
- How to reuse: Follow same error handling pattern (HTTPException → MonthDataError → generic), use `Depends(get_db)` for session injection, `Query()` for parameter validation
- Key methods: `_http_detail_for_db_error()` helper for consistent error messages

**Service Pattern - `backend/app/services/months.py`**

- What it does: Database queries for month data with SQLAlchemy
- How to reuse: Add `get_months_history()` function following existing `get_all_months_with_counts()` pattern
- Key methods: `SQLAlchemyError` handling wrapped in domain exceptions

**Response Models - `backend/app/responses/months.py`**

- What it does: Pydantic models for API responses with `from_model()` classmethods
- How to reuse: Create similar `MonthHistory` model following `MonthSummary` pattern
- Key methods: `Field()` for validation, `cast()` for Literal types

**Shared Types - `backend/app/responses/_types.py`**

- What it does: Centralized type definitions (ScoreLabelLiteral, MoneyMapTypeLiteral)
- How to reuse: Add `ScoreTrendLiteral = Literal["improving", "declining", "stable"]`

**Month Model - `backend/app/db/models/month.py`**

- What it does: SQLAlchemy model with all required fields
- How to reuse: Query Month model directly (no JOINs needed for history)
- Key fields: year, month, total_income, total_core, total_choice, total_compound, percentages, score, score_label

## Architecture Approach

**Component Design:**

- New file `responses/history.py`: MonthHistory, MonthReference, HistorySummary, HistoryResponse models
- Extend `services/months.py`: Add `get_months_history()` and `calculate_history_summary()` functions
- Extend `routers/months.py`: Add `get_history()` endpoint

**Data Flow:**

1. Request arrives at `GET /api/months/history?months=12`
2. Router validates `months` parameter (1-24)
3. Service queries Month table: `ORDER BY year DESC, month DESC LIMIT N`, then reverses for chronological order
4. Router builds `MonthHistory.from_model()` for each month
5. Service calculates summary (avg score, trend, best/worst)
6. Router returns `HistoryResponse`

**Integration Points:**

- Reuses existing `MonthDataError` exception hierarchy
- Follows established three-tier error handling in router
- Uses same database session injection pattern (`Depends(get_db)`)

## Out of Scope

- Date range filtering (start_date/end_date parameters)
- Category-level trends (per subcategory breakdown)
- Comparison between non-consecutive periods
- Data interpolation for missing months
- Frontend components (Score Evolution Chart, Spending Breakdown Chart, History Page)
- Transaction-level data in history response
- Caching or performance optimization beyond single query
- Advice generation based on historical trends
