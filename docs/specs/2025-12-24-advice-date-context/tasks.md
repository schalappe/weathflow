# Task Breakdown: Advice Date Context Improvement

## Overview

Total Tasks: 16
Estimated Complexity: Medium
Primary Stack: FastAPI + Python 3.12

## Task List

### Repository Layer

#### Task Group 1: Repository Methods

**Dependencies:** None

- [ ] 1.0 Complete repository layer
  - [ ] 1.1 Write 4 focused tests for new repository methods
    - Test `get_most_recent_month()` returns newest month by year/month
    - Test `get_most_recent_month()` returns None when no months exist
    - Test `has_any_advice()` returns True when advice exists
    - Test `has_any_advice()` returns False when no advice exists
  - [ ] 1.2 Add `get_most_recent_month()` to MonthRepository
    - Single query: `ORDER BY year DESC, month DESC LIMIT 1`
    - Return type: `Month | None`
    - Follow pattern from `get_recent_with_transactions()`
  - [ ] 1.3 Add `has_any_advice()` to AdviceRepository
    - Existence check: `SELECT 1 FROM advice LIMIT 1`
    - Return type: `bool`
    - Follow pattern from existing repository methods
  - [ ] 1.4 Ensure tests pass (run ONLY tests from 1.1)

**Acceptance Criteria:**

- `MonthRepository.get_most_recent_month()` returns correct month
- `AdviceRepository.has_any_advice()` correctly detects advice presence
- All 4 tests pass

---

### Exception Layer

#### Task Group 2: Custom Exception

**Dependencies:** None (can run parallel with Task Group 1)

- [ ] 2.0 Complete exception layer
  - [ ] 2.1 Write 2 focused tests for MonthNotEligibleError
    - Test exception carries year, month, and reason attributes
    - Test exception message formats correctly
  - [ ] 2.2 Add `MonthNotEligibleError` to exceptions.py
    - Inherit from `AdviceGenerationError`
    - Attributes: `year`, `month`, `reason`
    - Follow pattern from `InsufficientDataError`
  - [ ] 2.3 Ensure tests pass (run ONLY tests from 2.1)

**Acceptance Criteria:**

- Exception properly inherits from `AdviceGenerationError`
- Exception carries structured error information
- Both tests pass

---

### Service Layer

#### Task Group 3: Eligibility Service

**Dependencies:** Task Group 1, Task Group 2

- [ ] 3.0 Complete eligibility service
  - [ ] 3.1 Write 8 focused tests for eligibility logic
    - Test eligible month (most recent) returns `is_eligible=True`
    - Test eligible month (second most recent) returns `is_eligible=True`
    - Test ineligible month (too old) returns `is_eligible=False` with reason
    - Test first advice scenario returns `history_limit=12`
    - Test subsequent advice returns `history_limit=3`
    - Test regenerating first advice returns `history_limit=12`
    - Test insufficient data (1 month) returns appropriate error
    - Test year boundary eligibility (Dec 2024 + Jan 2025)
  - [ ] 3.2 Create `eligibility.py` module with constants
    - `REGULAR_HISTORY_LIMIT = 3`
    - `EXTENDED_HISTORY_LIMIT = 12`
    - `MIN_MONTHS_REQUIRED = 2`
    - `ELIGIBLE_MONTH_WINDOW = 2`
  - [ ] 3.3 Implement `EligibilityResult` dataclass
    - Fields: `is_eligible`, `history_limit`, `is_first_advice`, `reason`
    - Use `@dataclass` decorator
  - [ ] 3.4 Implement `check_eligibility()` function
    - Query most recent month for reference date
    - Calculate eligible window (2 most recent months)
    - Check if target month is within window
    - Determine history limit based on first-advice detection
    - Return `EligibilityResult`
  - [ ] 3.5 Implement `is_first_advice_month()` helper
    - Check if any advice exists in database
    - If no advice exists, return True
    - If regenerating, check if target is earliest advice month
  - [ ] 3.6 Ensure tests pass (run ONLY tests from 3.1)

**Acceptance Criteria:**

- Pure functions enable easy unit testing
- All eligibility scenarios handled correctly
- All 8 tests pass

---

#### Task Group 4: Months Service Wrapper

**Dependencies:** Task Group 1

- [ ] 4.0 Complete months service wrapper
  - [ ] 4.1 Write 2 focused tests for service wrapper
    - Test `get_most_recent_month()` returns month from repository
    - Test `get_most_recent_month()` handles repository errors
  - [ ] 4.2 Add `get_most_recent_month()` to months service
    - Wrap `MonthRepository.get_most_recent_month()`
    - Add error handling with `MonthDataError`
    - Follow pattern from existing service functions
  - [ ] 4.3 Ensure tests pass (run ONLY tests from 4.1)

**Acceptance Criteria:**

- Service wrapper properly handles errors
- Both tests pass

---

### API Layer

#### Task Group 5: Router Integration

**Dependencies:** Task Group 3, Task Group 4

- [ ] 5.0 Complete router integration
  - [ ] 5.1 Write 6 focused tests for router eligibility
    - Test eligible month generates advice successfully
    - Test ineligible month returns HTTP 400 with clear message
    - Test first advice uses 12-month history (mock verification)
    - Test subsequent advice uses 3-month history (mock verification)
    - Test regenerating first advice uses 12-month history
    - Test month not found returns HTTP 404
  - [ ] 5.2 Update error mapping function
    - Add `MonthNotEligibleError` to `_http_detail_for_advice_error()`
    - Map to HTTP 400 with `error.reason`
  - [ ] 5.3 Integrate eligibility check in `generate_advice()` endpoint
    - Import eligibility module
    - Call `check_eligibility()` after fetching month record
    - Raise `MonthNotEligibleError` if not eligible
    - Use `eligibility_result.history_limit` instead of hardcoded `3`
  - [ ] 5.4 Ensure tests pass (run ONLY tests from 5.1)

**Acceptance Criteria:**

- Ineligible months return HTTP 400 with descriptive message
- Dynamic history limit used based on eligibility result
- All 6 tests pass

---

### Testing

#### Task Group 6: Integration Tests and Gap Analysis

**Dependencies:** Task Groups 1-5

- [ ] 6.0 Complete testing phase
  - [ ] 6.1 Review all tests from groups 1-5 (~22 tests)
  - [ ] 6.2 Identify critical gaps for this feature
    - End-to-end scenario: first advice generation
    - End-to-end scenario: subsequent advice generation
    - End-to-end scenario: ineligible month rejection
    - Edge case: gap in months (Aug, Oct but no Sep)
  - [ ] 6.3 Write max 6 additional integration tests
    - Test full flow: new user generates first advice (12-month context)
    - Test full flow: returning user generates advice (3-month context)
    - Test full flow: ineligible month rejected with correct message
    - Test edge case: month gap handling
    - Test edge case: regenerating first advice after adding more months
    - Test year boundary: Dec + Jan eligibility
  - [ ] 6.4 Run all feature-specific tests
    - Run ONLY tests for advice eligibility feature
    - Verify all ~28 tests pass

**Acceptance Criteria:**

- All feature tests pass (~28 total)
- Critical workflows covered
- Edge cases handled

---

## Execution Order

1. **Task Group 1** (Repository) + **Task Group 2** (Exception) — Run in parallel, no dependencies
2. **Task Group 4** (Months Service) — Depends on repository methods
3. **Task Group 3** (Eligibility Service) — Depends on repository + exception
4. **Task Group 5** (Router Integration) — Depends on eligibility service
5. **Task Group 6** (Testing) — Final verification

## Files to Create

| File                                         | Task Group |
| -------------------------------------------- | ---------- |
| `backend/app/services/advice/eligibility.py` | 3          |

## Files to Modify

| File                                  | Task Group |
| ------------------------------------- | ---------- |
| `backend/app/repositories/month.py`   | 1          |
| `backend/app/repositories/advice.py`  | 1          |
| `backend/app/services/exceptions.py`  | 2          |
| `backend/app/services/data/months.py` | 4          |
| `backend/app/api/advice.py`           | 5          |

## Test Files to Create

| File                                                                   | Task Group |
| ---------------------------------------------------------------------- | ---------- |
| `backend/tests/units/repositories/test_month_eligibility.py`           | 1          |
| `backend/tests/units/repositories/test_advice_eligibility.py`          | 1          |
| `backend/tests/units/services/test_month_not_eligible_error.py`        | 2          |
| `backend/tests/units/services/advice/test_eligibility.py`              | 3          |
| `backend/tests/units/services/data/test_months_service_eligibility.py` | 4          |
| `backend/tests/integrations/api/test_advice_eligibility.py`            | 5, 6       |
