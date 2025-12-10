# Task Breakdown: Historical Data API

## Overview

Total Tasks: 16
Estimated Complexity: Low-Medium
Primary Stack: FastAPI + Python 3.12 + SQLAlchemy

## Task List

### Response Models Layer

#### Task Group 1: Pydantic Response Models

**Dependencies:** None

- [x] 1.0 Complete response models layer
  - [x] 1.1 Add `ScoreTrendLiteral` type to shared types
    - File: `backend/app/responses/_types.py`
    - Add: `ScoreTrendLiteral = Literal["improving", "declining", "stable"]`
    - Follow existing pattern from `ScoreLabelLiteral`
  - [x] 1.2 Create `MonthHistory` response model
    - File: `backend/app/responses/history.py` (new file)
    - Fields: year, month, month_label, total_income, total_core, total_choice, total_compound, core_percentage, choice_percentage, compound_percentage, score, score_label
    - Add `from_model()` classmethod following `MonthSummary` pattern
    - Generate `month_label` using `datetime(year, month, 1).strftime("%b %Y")`
  - [x] 1.3 Create `MonthReference` and `HistorySummary` models
    - File: `backend/app/responses/history.py`
    - `MonthReference`: year, month, score (for best/worst month)
    - `HistorySummary`: total_months, average_score, score_trend, best_month (optional), worst_month (optional)
  - [x] 1.4 Create `HistoryResponse` model
    - File: `backend/app/responses/history.py`
    - Compose: `months: list[MonthHistory]`, `summary: HistorySummary`

**Acceptance Criteria:**

- All models have proper type hints
- `from_model()` classmethod works correctly
- Models pass mypy type checking
- `month_label` generates correct format (e.g., "Oct 2025")

---

### Service Layer

#### Task Group 2: Database Query Function

**Dependencies:** None (can run in parallel with Task Group 1)

- [x] 2.0 Complete database query function
  - [x] 2.1 Write 3 focused tests for `get_months_history()`
    - File: `backend/tests/units/services/test_history.py` (new file)
    - Test 1: Returns correct number of months when limit < available
    - Test 2: Returns all months when limit > available
    - Test 3: Returns empty list when no months exist
  - [x] 2.2 Implement `get_months_history()` function
    - File: `backend/app/services/months.py`
    - Query: `ORDER BY year DESC, month DESC LIMIT :limit`
    - Reverse result for chronological order (oldest first)
    - Catch `SQLAlchemyError`, raise `MonthQueryError`
    - Add logging for success/failure
  - [x] 2.3 Run tests from 2.1
    - Command: `cd backend && uv run pytest tests/units/services/test_history.py -v`
    - All 3 tests must pass

**Acceptance Criteria:**

- Function returns months in chronological order (oldest first)
- Handles empty database gracefully
- Follows existing service layer patterns
- All 3 unit tests pass

---

#### Task Group 3: Summary Calculation Logic

**Dependencies:** Task Group 1 (needs response models)

- [x] 3.0 Complete summary calculation logic
  - [x] 3.1 Write 5 focused tests for trend calculation
    - File: `backend/tests/units/services/test_history.py`
    - Test 1: Returns "improving" when last 3 avg > previous 3 avg
    - Test 2: Returns "declining" when last 3 avg < previous 3 avg
    - Test 3: Returns "stable" when averages are equal
    - Test 4: Returns "stable" when fewer than 6 months
    - Test 5: Correctly identifies best and worst months
  - [x] 3.2 Implement `_calculate_score_trend()` helper
    - File: `backend/app/services/months.py`
    - Compare avg of last 3 months vs avg of previous 3 months
    - Return "stable" if fewer than 6 months
    - Return type: `ScoreTrendLiteral`
  - [x] 3.3 Implement `calculate_history_summary()` function
    - File: `backend/app/services/months.py`
    - Calculate: total_months, average_score, score_trend, best_month, worst_month
    - Handle empty list case (return zeroed summary)
    - Return `HistorySummary` model
  - [x] 3.4 Run tests from 3.1
    - Command: `cd backend && uv run pytest tests/units/services/test_history.py -v`
    - All 8 tests must pass (3 from 2.1 + 5 from 3.1)

**Acceptance Criteria:**

- Trend calculation correctly compares 3-month averages
- Summary handles edge cases (empty, single month, equal scores)
- All 8 unit tests pass
- Functions have proper type hints and docstrings

---

### Router Layer

#### Task Group 4: API Endpoint

**Dependencies:** Task Groups 1, 2, 3

- [x] 4.0 Complete API endpoint
  - [x] 4.1 Add `get_history()` endpoint to months router
    - File: `backend/app/routers/months.py`
    - Route: `GET /api/months/history`
    - Query param: `months: int = Query(12, ge=1, le=24, description="Number of months to retrieve")`
    - Use `Depends(get_db)` for session injection
  - [x] 4.2 Implement endpoint logic
    - Call `get_months_history(db, limit=months)`
    - Build `MonthHistory.from_model()` for each month
    - Call `calculate_history_summary(month_records)`
    - Return `HistoryResponse`
  - [x] 4.3 Add error handling
    - Follow existing three-tier pattern (HTTPException → MonthDataError → generic)
    - Reuse `_http_detail_for_db_error()` helper
    - Log errors with context
  - [x] 4.4 Verify endpoint in FastAPI docs
    - Start server: `make dev-backend`
    - Check: http://localhost:8000/docs
    - Verify endpoint appears with correct schema

**Acceptance Criteria:**

- Endpoint accessible at `GET /api/months/history`
- Query parameter validates range (1-24)
- Error handling follows existing patterns
- Endpoint documented in OpenAPI schema

---

### Testing Layer

#### Task Group 5: Integration Tests

**Dependencies:** Task Group 4

- [x] 5.0 Complete integration tests
  - [x] 5.1 Write 6 focused integration tests
    - File: `backend/tests/integration/test_history_api.py` (new file)
    - Test 1: `test_history_returns_correct_months_count` - Verify limit parameter works
    - Test 2: `test_history_chronological_order` - Verify oldest-first ordering
    - Test 3: `test_history_default_limit_is_12` - Verify default when no param
    - Test 4: `test_history_max_limit_24` - Verify 422 when > 24
    - Test 5: `test_history_empty_database` - Verify empty response structure
    - Test 6: `test_history_summary_structure` - Verify summary fields present
  - [x] 5.2 Run integration tests
    - Command: `cd backend && uv run pytest tests/integration/test_history_api.py -v`
    - All 6 tests must pass

**Acceptance Criteria:**

- All 6 integration tests pass
- Tests use existing fixtures (client, db_session)
- Tests verify complete API contract

---

#### Task Group 6: Final Validation

**Dependencies:** Task Groups 1-5

- [x] 6.0 Complete final validation
  - [x] 6.1 Run all feature tests
    - Command: `cd backend && uv run pytest tests/units/services/test_history.py tests/integration/test_history_api.py -v`
    - Expected: 14 tests pass (8 unit + 6 integration)
  - [x] 6.2 Run code quality checks
    - Linting: `cd backend && uv run ruff check .`
    - Formatting: `cd backend && uv run ruff format .`
    - Type checking: `cd backend && uv run mypy .`
  - [x] 6.3 Manual API verification
    - Test with real data: `curl "http://localhost:8000/api/months/history?months=6"`
    - Verify response structure matches spec
    - Verify chronological ordering
    - Verify summary calculations

**Acceptance Criteria:**

- All 14 feature tests pass
- No linting or type errors
- API returns correct response structure
- Performance: < 100ms for 12 months

---

## Execution Order

1. **Task Group 1** (Response Models) - Foundation for all other layers
2. **Task Group 2** (Database Query) - Can run in parallel with Group 1
3. **Task Group 3** (Summary Calculation) - Depends on response models
4. **Task Group 4** (API Endpoint) - Integrates all layers
5. **Task Group 5** (Integration Tests) - Validates complete feature
6. **Task Group 6** (Final Validation) - Quality assurance

## Files Created/Modified

| File                                            | Action | Task Group |
| ----------------------------------------------- | ------ | ---------- |
| `backend/app/responses/_types.py`               | Modify | 1          |
| `backend/app/responses/history.py`              | Create | 1          |
| `backend/app/services/months.py`                | Modify | 2, 3       |
| `backend/app/routers/months.py`                 | Modify | 4          |
| `backend/tests/units/services/test_history.py`  | Create | 2, 3       |
| `backend/tests/integration/test_history_api.py` | Create | 5          |

## Test Summary

| Phase        | Tests  | Focus                     |
| ------------ | ------ | ------------------------- |
| Task Group 2 | 3      | Database query function   |
| Task Group 3 | 5      | Trend calculation logic   |
| Task Group 5 | 6      | API endpoint integration  |
| **Total**    | **14** | Complete feature coverage |
