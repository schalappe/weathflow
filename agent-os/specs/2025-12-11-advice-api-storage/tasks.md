# Task Breakdown: Advice API and Storage

## Overview

**Total Tasks:** 16 sub-tasks across 4 task groups
**Estimated Size:** Small feature (~150 lines of new code)
**Stack:** Backend only (FastAPI + SQLAlchemy)

This feature exposes the existing `AdviceGenerator` service via REST API. Most infrastructure already exists - we're adding a thin service layer, response models, and router.

---

## Task List

### Service Layer

#### Task Group 1: Exception and Service Functions

**Dependencies:** None
**Estimated Time:** 45-60 minutes

- [ ] 1.0 Complete service layer for advice CRUD
  - [ ] 1.1 Write 4 focused tests for advice service functions
    - Test `get_advice_by_month_id()` returns advice when exists
    - Test `get_advice_by_month_id()` returns None when not exists
    - Test `create_or_update_advice()` creates new advice record
    - Test `create_or_update_advice()` updates existing advice record
  - [ ] 1.2 Add `AdviceQueryError` exception to `exceptions.py`
    - Inherit from `AdviceGenerationError`
    - Include `month_id` and `reason` attributes
    - Follow existing exception pattern (lines 359-427)
  - [ ] 1.3 Create `backend/app/services/advice.py` with CRUD functions
    - `get_advice_by_month_id(db, month_id) -> Advice | None`
    - `create_or_update_advice(db, month_id, advice_text) -> Advice`
    - `month_to_month_data(month: Month) -> MonthData`
    - `advice_response_to_json(advice: AdviceResponse) -> str`
    - Follow pattern from `backend/app/services/months.py`
  - [ ] 1.4 Ensure service layer tests pass
    - Run only the 4 tests from task 1.1
    - Verify CRUD operations work correctly

**Acceptance Criteria:**

- All 4 service tests pass
- `AdviceQueryError` added to exceptions module
- Service functions handle SQLAlchemy errors gracefully
- JSON serialization matches expected format

---

### Response Models

#### Task Group 2: Pydantic Response Models

**Dependencies:** None (can run in parallel with Task Group 1)
**Estimated Time:** 30-45 minutes

- [ ] 2.0 Complete response models for advice endpoints
  - [ ] 2.1 Write 3 focused tests for response model converters
    - Test `AdviceData.from_json()` parses valid JSON string
    - Test `AdviceData.from_service_response()` converts DTO correctly
    - Test response models validate field constraints
  - [ ] 2.2 Create `backend/app/responses/advice.py`
    - `ProblemAreaResponse` model (category, amount, trend)
    - `AdviceData` model with `from_json()` and `from_service_response()` class methods
    - `GenerateAdviceRequest` model (year, month, regenerate)
    - `GenerateAdviceResponse` model (success, advice, generated_at, was_cached)
    - `GetAdviceResponse` model (success, advice, generated_at, exists)
    - Follow pattern from `backend/app/responses/months.py`
  - [ ] 2.3 Ensure response model tests pass
    - Run only the 3 tests from task 2.1
    - Verify JSON parsing and DTO conversion work

**Acceptance Criteria:**

- All 3 response model tests pass
- Models have proper Field validators (year 2000-2100, month 1-12)
- `from_json()` handles stored advice format
- `from_service_response()` converts service DTOs

---

### API Layer

#### Task Group 3: Router and Endpoints

**Dependencies:** Task Groups 1 and 2
**Estimated Time:** 60-90 minutes

- [ ] 3.0 Complete API router with both endpoints
  - [ ] 3.1 Write 6 focused tests for advice endpoints
    - Test POST generates new advice when none exists
    - Test POST returns cached advice when exists and `regenerate=False`
    - Test POST regenerates advice when `regenerate=True`
    - Test POST returns 404 when month not found
    - Test GET returns existing advice with `exists=True`
    - Test GET returns `exists=False` when no advice
  - [ ] 3.2 Create `backend/app/routers/advice.py` with POST endpoint
    - `POST /api/advice/generate` with `GenerateAdviceRequest` body
    - Check month exists (404 if not)
    - Check for cached advice (return if exists and not regenerating)
    - Fetch history via `get_months_history(db, limit=3)`
    - Convert months to `MonthData` DTOs
    - Call `AdviceGenerator.generate_advice()`
    - Store result via `create_or_update_advice()`
    - Map exceptions to HTTP status codes (400, 404, 500, 503)
  - [ ] 3.3 Add GET endpoint to advice router
    - `GET /api/advice/{year}/{month}` with path validation
    - Check month exists (404 if not)
    - Query advice via `get_advice_by_month_id()`
    - Return `exists=False` if no advice, otherwise parse and return
  - [ ] 3.4 Wire router in `backend/app/main.py`
    - Import advice router
    - Add `app.include_router(advice.router)`
  - [ ] 3.5 Ensure API tests pass
    - Run only the 6 tests from task 3.1
    - Verify all endpoints respond correctly

**Acceptance Criteria:**

- All 6 endpoint tests pass
- POST handles caching logic correctly (`was_cached` flag)
- GET returns proper `exists` flag
- Error mapping follows established patterns (404, 400, 503, 500)
- Router registered in main.py

---

### Testing

#### Task Group 4: Test Review and Integration

**Dependencies:** Task Groups 1, 2, and 3
**Estimated Time:** 30-45 minutes

- [ ] 4.0 Review existing tests and add integration coverage
  - [ ] 4.1 Review tests from Task Groups 1-3
    - Review 4 service tests (Task 1.1)
    - Review 3 response model tests (Task 2.1)
    - Review 6 endpoint tests (Task 3.1)
    - Total existing: 13 tests
  - [ ] 4.2 Identify critical integration gaps
    - Full flow: generate → store → retrieve
    - Error scenarios with mocked Claude API
    - Insufficient data handling (< 2 months)
  - [ ] 4.3 Write up to 5 additional integration tests
    - Test full generate-then-retrieve flow
    - Test 400 error when insufficient historical data
    - Test regeneration replaces existing advice
    - Test 503 error when Claude API unavailable (mocked)
    - Test advice JSON persisted correctly in database
  - [ ] 4.4 Run all feature-specific tests
    - Run all 18 tests (13 existing + 5 integration)
    - Verify all pass
    - Run quality checks: `ruff check`, `ruff format`, `mypy`

**Acceptance Criteria:**

- All 18 feature tests pass
- Full generate-retrieve workflow covered
- Error scenarios tested (400, 503)
- Code passes linting and type checking

---

## Execution Order

```txt
┌─────────────────────────────────────────────────────────────┐
│ Task Group 1: Service Layer   Task Group 2: Response Models │
│ (45-60 min)                    (30-45 min)                  │
│                                                             │
│ Can run in PARALLEL - no dependencies between them          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Task Group 3: Router and Endpoints                          │
│ (60-90 min)                                                 │
│                                                             │
│ Depends on Task Groups 1 AND 2                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Task Group 4: Test Review and Integration                   │
│ (30-45 min)                                                 │
│                                                             │
│ Depends on Task Group 3                                     │
└─────────────────────────────────────────────────────────────┘
```

**Recommended sequence:**

1. **Task Groups 1 & 2** (parallel) - Build foundation
2. **Task Group 3** - Implement endpoints
3. **Task Group 4** - Verify and finalize

**Total estimated time:** 2.5-4 hours

---

## Files to Create

| File                                                     | Task Group | Lines (est.) |
| -------------------------------------------------------- | ---------- | ------------ |
| `backend/app/services/advice.py`                         | 1          | ~60          |
| `backend/app/responses/advice.py`                        | 2          | ~50          |
| `backend/app/routers/advice.py`                          | 3          | ~120         |
| `backend/tests/units/services/test_advice_service.py`    | 1          | ~80          |
| `backend/tests/units/responses/test_advice_responses.py` | 2          | ~50          |
| `backend/tests/units/routers/test_advice_router.py`      | 3          | ~120         |
| `backend/tests/integration/test_advice_api.py`           | 4          | ~80          |

## Files to Modify

| File                                 | Task Group | Change                            |
| ------------------------------------ | ---------- | --------------------------------- |
| `backend/app/services/exceptions.py` | 1          | Add `AdviceQueryError` class      |
| `backend/app/main.py`                | 3          | Import and register advice router |
