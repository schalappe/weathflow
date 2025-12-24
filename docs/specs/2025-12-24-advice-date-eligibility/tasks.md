# Task Breakdown: Advice Date Eligibility Improvement

## Overview

Total Task Groups: 5
Total Subtasks: 22

## Task List

### Backend Infrastructure

#### Task Group 1: Repository Extensions

**Dependencies:** None

- [ ] 1.0 Complete repository extensions
  - [ ] 1.1 Write 4 focused tests for repository methods
    - `test_get_most_recent_returns_latest_month`
    - `test_get_most_recent_returns_none_when_empty`
    - `test_has_any_returns_true_when_advice_exists`
    - `test_count_returns_correct_count`
  - [ ] 1.2 Add `get_most_recent()` to `MonthRepository`
  - [ ] 1.3 Add `has_any()` and `count()` to `AdviceRepository`
  - [ ] 1.4 Ensure tests pass (run ONLY tests from 1.1)

**Acceptance Criteria:**

- `get_most_recent()` returns newest month by (year, month) or None
- `has_any()` returns True if any advice exists, False otherwise
- `count()` returns total advice record count
- All 4 tests pass

**Files to modify:**

- `backend/app/repositories/month.py`
- `backend/app/repositories/advice.py`
- `backend/tests/units/repositories/test_month_eligibility.py` (create)
- `backend/tests/units/repositories/test_advice_eligibility.py` (create)

---

### Backend Service Layer

#### Task Group 2: Eligibility Service

**Dependencies:** Task Group 1

- [ ] 2.0 Complete eligibility service
  - [ ] 2.1 Write 6 focused tests for eligibility logic
    - `test_eligible_when_target_is_most_recent_month`
    - `test_eligible_when_target_is_previous_month`
    - `test_not_eligible_when_target_too_old`
    - `test_first_advice_returns_12_month_limit`
    - `test_regenerating_only_advice_returns_12_month_limit`
    - `test_normal_advice_returns_3_month_limit`
  - [ ] 2.2 Create `EligibilityResult` frozen dataclass
  - [ ] 2.3 Implement `check_eligibility()` function
  - [ ] 2.4 Implement `_is_within_eligible_window()` helper
  - [ ] 2.5 Ensure tests pass (run ONLY tests from 2.1)

**Acceptance Criteria:**

- `EligibilityResult` contains: `is_eligible`, `history_limit`, `is_first_advice`, `reason`
- Eligibility window is [last_month - 1, last_month]
- First advice scenario detected correctly (no advice or regenerating only advice)
- History limit is 12 for first advice, 3 otherwise
- All 6 tests pass

**Files to create/modify:**

- `backend/app/services/advice/eligibility.py` (create)
- `backend/tests/units/services/advice/test_eligibility.py` (create)

---

### Backend API Layer

#### Task Group 3: API Integration

**Dependencies:** Task Group 2

- [ ] 3.0 Complete API layer integration
  - [ ] 3.1 Write 5 focused tests for API eligibility
    - `test_get_advice_returns_eligibility_info`
    - `test_generate_advice_uses_dynamic_history_limit`
    - `test_generate_advice_returns_403_when_not_eligible`
    - `test_generate_first_advice_uses_12_month_limit`
    - `test_eligibility_reason_included_in_403_response`
  - [ ] 3.2 Add `EligibilityInfo` model to response schemas
  - [ ] 3.3 Update `GetAdviceResponse` with eligibility field
  - [ ] 3.4 Integrate eligibility check in `get_advice()` endpoint
  - [ ] 3.5 Integrate eligibility check in `generate_advice()` endpoint
  - [ ] 3.6 Use dynamic `history_limit` instead of hardcoded `3`
  - [ ] 3.7 Ensure tests pass (run ONLY tests from 3.1)

**Acceptance Criteria:**

- `GET /api/advice/{year}/{month}` returns `eligibility` field
- `POST /api/advice/generate` validates eligibility before generating
- HTTP 403 returned with clear reason when not eligible
- History fetched with 3 or 12 based on `eligibility.history_limit`
- All 5 tests pass

**Files to modify:**

- `backend/app/responses/advice.py`
- `backend/app/api/advice.py`
- `backend/tests/integrations/api/test_advice_eligibility.py` (create)

---

### Frontend Layer

#### Task Group 4: Frontend Eligibility Update

**Dependencies:** Task Group 3

- [ ] 4.0 Complete frontend eligibility update
  - [ ] 4.1 Add `EligibilityInfo` type to TypeScript types
  - [ ] 4.2 Update `GetAdviceResponse` type with eligibility field
  - [ ] 4.3 Remove `isGenerationAllowed()` function from component
  - [ ] 4.4 Update reducer state to store eligibility from response
  - [ ] 4.5 Update `FETCH_SUCCESS` action to include eligibility
  - [ ] 4.6 Use `eligibility.can_generate` for UI decisions
  - [ ] 4.7 Delete obsolete test file `is-generation-allowed.test.tsx`

**Acceptance Criteria:**

- `isGenerationAllowed()` function removed
- UI shows/hides generate button based on backend eligibility
- Eligibility reason displayed when not eligible
- TypeScript compiles without errors

**Files to modify:**

- `frontend/types/index.ts`
- `frontend/components/history/advice-panel-content.tsx`
- `frontend/__tests__/history/is-generation-allowed.test.tsx` (delete)

---

### Testing & Verification

#### Task Group 5: Test Review and Gap Fill

**Dependencies:** Task Groups 1-4

- [ ] 5.0 Review tests and fill critical gaps
  - [ ] 5.1 Review all tests from groups 1-4 (~15 tests)
  - [ ] 5.2 Identify critical gaps for eligibility feature only
  - [ ] 5.3 Write max 5 additional tests for gaps found
  - [ ] 5.4 Run all eligibility-related tests to verify
  - [ ] 5.5 Verify TypeScript compilation passes

**Acceptance Criteria:**

- All eligibility tests pass (~15-20 total)
- Critical edge cases covered (empty DB, January wraparound, etc.)
- No regressions in existing advice functionality

**Test files to run:**

- `backend/tests/units/repositories/test_month_eligibility.py`
- `backend/tests/units/repositories/test_advice_eligibility.py`
- `backend/tests/units/services/advice/test_eligibility.py`
- `backend/tests/integrations/api/test_advice_eligibility.py`

---

## Execution Order

1. **Task Group 1:** Repository Extensions (backend infrastructure)
2. **Task Group 2:** Eligibility Service (backend business logic)
3. **Task Group 3:** API Integration (backend endpoints)
4. **Task Group 4:** Frontend Eligibility Update (UI changes)
5. **Task Group 5:** Test Review and Gap Fill (verification)

## Size Verification

| Task Group | Estimated Duration | Files Changed | Size   |
| ---------- | ------------------ | ------------- | ------ |
| Group 1    | 30-45 min          | 4             | Small  |
| Group 2    | 45-60 min          | 2             | Small  |
| Group 3    | 60-90 min          | 3             | Medium |
| Group 4    | 45-60 min          | 3             | Small  |
| Group 5    | 30-45 min          | 0 (tests)     | Small  |

All tasks within acceptable size limits (no large tasks).
