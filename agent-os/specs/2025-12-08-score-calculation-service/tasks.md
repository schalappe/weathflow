# Task Breakdown: Score Calculation Service

## Overview

Total Tasks: 14 sub-tasks across 3 task groups

This is a **backend-only** service with no UI components. The tasks are organized by layer:

1. Schema & Exception Layer (foundation)
2. Pure Calculation Functions (core logic)
3. Database Integration (persistence)

## Task List

### Schema & Exception Layer

#### Task Group 1: MonthStats Schema and Custom Exception

**Dependencies:** None

- [ ] 1.0 Complete schema and exception layer
  - [ ] 1.1 Write 3 focused tests for MonthStats schema
    - Test MonthStats creation with valid data
    - Test immutability (modification raises ValidationError)
    - Test Field constraints (score 0-3, non-negative totals)
  - [ ] 1.2 Add MonthStats schema to `backend/app/services/schemas.py`
    - Inherit from `FrozenModel`
    - Fields: `total_income`, `total_core`, `total_choice`, `total_compound`
    - Fields: `core_percentage`, `choice_percentage`, `compound_percentage`
    - Fields: `score` (int, 0-3), `score_label` (str)
    - Use `Field(ge=0)` for non-negative constraints
    - Allow negative `total_compound` (overspending case)
    - Add NumPy-style docstring with Attributes section
  - [ ] 1.3 Add MonthNotFoundError to `backend/app/services/exceptions.py`
    - Create base `ScoreCalculationError` exception
    - Create `MonthNotFoundError(ScoreCalculationError)` with `month_id` attribute
    - Follow existing exception pattern with typed attributes
  - [ ] 1.4 Run schema and exception tests only
    - Verify the 3 tests from 1.1 pass
    - Do NOT run the entire test suite

**Acceptance Criteria:**

- MonthStats schema validates correctly
- MonthStats is immutable (frozen)
- MonthNotFoundError stores month_id and provides readable message
- All 3 tests pass

---

### Pure Calculation Functions

#### Task Group 2: Score and Stats Calculation Functions

**Dependencies:** Task Group 1

- [ ] 2.0 Complete pure calculation functions
  - [ ] 2.1 Write 6 focused tests for calculation functions
    - Test `calculate_score` perfect score (45%, 25%, 30%) → score 3, "Great"
    - Test `calculate_score` at exact thresholds (50%, 30%, 20%) → score 3
    - Test `calculate_score` one threshold exceeded → score 2
    - Test `calculate_month_stats` happy path with valid totals
    - Test `calculate_month_stats` zero income edge case → score 0, "Poor"
    - Test `calculate_month_stats` negative compound (overspent) → calculates correctly
  - [ ] 2.2 Create `backend/app/services/calculator.py` with constants
    - Add module docstring
    - Add module-level logger: `logger = logging.getLogger(__name__)`
    - Define constants: `CORE_THRESHOLD = 50.0`, `CHOICE_THRESHOLD = 30.0`, `COMPOUND_THRESHOLD = 20.0`
    - Add necessary imports: `ScoreLabel` from `app.db.enums`, `MonthStats` from schemas
  - [ ] 2.3 Implement `calculate_score()` function
    - Signature: `def calculate_score(core_pct: float, choice_pct: float, compound_pct: float) -> tuple[int, ScoreLabel]`
    - Award +1 if core_pct <= 50, +1 if choice_pct <= 30, +1 if compound_pct >= 20
    - Map score to label using dict: `{0: POOR, 1: NEED_IMPROVEMENT, 2: OKAY, 3: GREAT}`
    - Add NumPy-style docstring
  - [ ] 2.4 Implement `calculate_month_stats()` function
    - Signature: `def calculate_month_stats(income: float, core: float, choice: float) -> MonthStats`
    - Handle zero income edge case first (return zeroed stats with score 0)
    - Derive compound: `income - core - choice`
    - Calculate percentages: `round((category / income) * 100, 1)`
    - Call `calculate_score()` to get score and label
    - Return `MonthStats` with all fields populated
    - Add NumPy-style docstring
  - [ ] 2.5 Run pure calculation tests only
    - Verify the 6 tests from 2.1 pass
    - Do NOT run the entire test suite

**Acceptance Criteria:**

- `calculate_score` correctly evaluates all threshold combinations
- `calculate_month_stats` handles happy path and edge cases
- Percentages are rounded to 1 decimal place
- Zero income returns score 0 with label "Poor"
- Negative compound is calculated correctly (not errored)
- All 6 tests pass

---

### Database Integration

#### Task Group 3: Transaction Aggregation and Month Update

**Dependencies:** Task Group 2

- [ ] 3.0 Complete database integration layer
  - [ ] 3.1 Write 5 focused tests for database integration
    - Test `_aggregate_transaction_totals` with sample transactions
    - Test `_aggregate_transaction_totals` with no transactions → (0, 0, 0)
    - Test `calculate_and_update_month` updates Month record correctly
    - Test `calculate_and_update_month` with non-existent month_id → raises MonthNotFoundError
    - Test recalculation after transaction category change
  - [ ] 3.2 Implement `_aggregate_transaction_totals()` helper
    - Signature: `def _aggregate_transaction_totals(db: Session, month_id: int) -> tuple[float, float, float]`
    - Use single SQL query with conditional `func.sum().filter()`
    - Income: SUM where `money_map_type == INCOME` and `amount > 0`
    - Core: ABS(SUM) where `money_map_type == CORE` and `amount < 0`
    - Choice: ABS(SUM) where `money_map_type == CHOICE` and `amount < 0`
    - Use `func.coalesce(..., 0.0)` for NULL handling
    - Return tuple of floats: `(income, core, choice)`
    - Add NumPy-style docstring
  - [ ] 3.3 Implement `calculate_and_update_month()` function
    - Signature: `def calculate_and_update_month(db: Session, month_id: int) -> Month`
    - Fetch Month by ID, raise `MonthNotFoundError` if not found
    - Call `_aggregate_transaction_totals()` to get totals
    - Call `calculate_month_stats()` to get stats
    - Update all Month fields from stats
    - Commit and refresh the Month record
    - Log the update with month_id, income, score, and label
    - Return the updated Month
    - Add NumPy-style docstring with Raises section
  - [ ] 3.4 Run database integration tests only
    - Verify the 5 tests from 3.1 pass
    - Do NOT run the entire test suite

**Acceptance Criteria:**

- `_aggregate_transaction_totals` returns correct totals from transactions
- SQL query is efficient (single query, not N+1)
- `calculate_and_update_month` persists all stats to Month record
- `MonthNotFoundError` is raised for invalid month_id
- Recalculation produces correct results after category changes
- All 5 tests pass

---

## Execution Order

Recommended implementation sequence:

1. **Task Group 1: Schema & Exception** (foundation)
   - Creates MonthStats schema and MonthNotFoundError exception
   - No dependencies, can start immediately
   - Estimated time: 45-60 minutes

2. **Task Group 2: Pure Calculation Functions** (core logic)
   - Implements stateless calculation functions
   - Depends on MonthStats schema from Task Group 1
   - Estimated time: 60-90 minutes

3. **Task Group 3: Database Integration** (persistence)
   - Implements transaction aggregation and month update
   - Depends on calculation functions from Task Group 2
   - Estimated time: 60-90 minutes

**Total Estimated Time:** 3-4 hours

---

## Files to Create/Modify

| File                                              | Action                  | Task Group |
| ------------------------------------------------- | ----------------------- | ---------- |
| `backend/app/services/schemas.py`                 | Modify (add MonthStats) | 1          |
| `backend/app/services/exceptions.py`              | Modify (add exceptions) | 1          |
| `backend/app/services/calculator.py`              | Create (new file)       | 2, 3       |
| `backend/tests/units/services/test_calculator.py` | Create (new file)       | 1, 2, 3    |

---

## Test Summary

| Task Group | Tests Written | Focus                                         |
| ---------- | ------------- | --------------------------------------------- |
| 1          | 3 tests       | MonthStats schema validation and immutability |
| 2          | 6 tests       | Pure calculation functions (score + stats)    |
| 3          | 5 tests       | Database integration and Month updates        |
| **Total**  | **14 tests**  | Full coverage of critical paths               |

---

## Quality Gates (Run After All Task Groups)

After completing all task groups:

```bash
cd backend
uv run ruff check .
uv run ruff format .
uv run mypy .
uv run pytest tests/units/services/test_calculator.py -v
```

All 14 tests should pass, and code should have no linting/type errors.
