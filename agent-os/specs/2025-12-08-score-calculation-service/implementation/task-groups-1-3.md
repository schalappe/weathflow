# Implementation: Task Groups 1-3 (Score Calculation Service)

**Date:** 2025-12-08
**Task Groups:** 1, 2, 3 (Schema & Exception, Pure Calculation, Database Integration)
**Implementer:** implement-task command

## Summary

Implemented the complete Score Calculation Service for the Money Map (50/30/20 budgeting) framework. The service calculates monthly budget scores based on categorized transactions, with pure calculation functions for testability and a database integration layer for persistence.

## Architecture Approach

Selected the **functional module approach** (not class-based) because:

- No external state or dependencies to manage
- Pure functions enable simple unit testing without mocks
- Matches existing patterns in the codebase (`csv_parser.py`, `categorization_cache.py`)
- Single file with clear separation: constants → pure functions → DB functions

## Files Modified

- `backend/app/services/schemas.py` - Added `MonthStats` FrozenModel schema with all stat fields, score constraints, and ScoreLabel enum import
- `backend/app/services/exceptions.py` - Added `ScoreCalculationError` base exception and `MonthNotFoundError` with typed `month_id` attribute

## Files Created

- `backend/app/services/calculator.py` - Core service module with:
  - Module constants: `CORE_THRESHOLD`, `CHOICE_THRESHOLD`, `COMPOUND_THRESHOLD`
  - Score-to-label mapping: `_SCORE_TO_LABEL`
  - Pure functions: `calculate_score()`, `calculate_month_stats()`
  - DB helper: `_aggregate_transaction_totals()` (single query with conditional aggregation)
  - Orchestrator: `calculate_and_update_month()`

- `backend/tests/units/services/test_score_calculator.py` - Comprehensive test suite with:
  - 6 tests for schema and exception (Task Group 1)
  - 8 tests for pure calculations (Task Group 2)
  - 5 tests for database integration (Task Group 3)
  - Total: 19 tests covering all acceptance criteria

## Key Implementation Details

### MonthStats Schema

```python
class MonthStats(FrozenModel):
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float  # Can be negative (overspending)
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int = Field(ge=0, le=3)
    score_label: ScoreLabel
```

### Score Calculation Logic

```python
def calculate_score(core_pct, choice_pct, compound_pct) -> tuple[int, ScoreLabel]:
    score = 0
    if core_pct <= 50.0: score += 1
    if choice_pct <= 30.0: score += 1
    if compound_pct >= 20.0: score += 1
    return score, _SCORE_TO_LABEL[score]
```

### Transaction Aggregation (Single SQL Query)

Uses SQLAlchemy's `func.sum().filter()` for conditional aggregation:

```python
db.query(
    func.coalesce(func.sum(Transaction.amount).filter(
        Transaction.money_map_type == MoneyMapType.INCOME.value,
        Transaction.amount > 0,
    ), 0.0).label("income"),
    # ... similar for core and choice
).filter(Transaction.month_id == month_id).one()
```

### Edge Cases Handled

| Scenario | Handling |
|----------|----------|
| Zero income | All percentages = 0.0, score = 0, label = "Poor" |
| Negative compound | Stored as-is (represents overspending) |
| No transactions | Returns (0, 0, 0) via COALESCE |
| Month not found | Raises `MonthNotFoundError` with month_id |

## Integration Points

- Imports `ScoreLabel` from `app.db.enums`
- Imports `Month`, `Transaction` from `app.db.models`
- Uses `MonthStats` from `app.services.schemas`
- Uses `MonthNotFoundError` from `app.services.exceptions`
- Follows existing service patterns (NumPy docstrings, logging, comment prefixes)

## Testing Notes

All 19 tests pass:

- **TestMonthStatsSchema**: 3 tests for schema validation and immutability
- **TestMonthNotFoundError**: 3 tests for exception behavior
- **TestCalculateScore**: 5 tests covering all threshold combinations
- **TestCalculateMonthStats**: 3 tests for happy path and edge cases
- **TestAggregateTransactionTotals**: 2 tests for SQL aggregation
- **TestCalculateAndUpdateMonth**: 3 tests for DB integration

Test file location: `backend/tests/units/services/test_score_calculator.py`

## Deviations from Spec

1. **score_label type**: Changed from `str` to `ScoreLabel` enum as clarified by user
2. **Test file name**: Changed from `test_calculator.py` to `test_score_calculator.py` as clarified by user
3. **Additional tests**: Added 5 extra tests beyond the 14 specified (19 total) for better coverage
