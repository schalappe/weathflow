# Implementation: Historical Data API (Task Groups 1-6)

**Date:** 2025-12-10
**Task Groups:** 1-6 (Complete Feature)
**Implementer:** implement-task command

## Summary

Implemented the Historical Data API feature which provides a new endpoint `GET /api/months/history` that returns aggregated historical data for the last N months. The implementation includes response models, service layer functions, API endpoint, and comprehensive tests.

## Architecture Approach

Selected **Minimal Changes** approach:
- Extended existing `months.py` service file rather than creating a separate history service
- Added `ScoreTrendLiteral` to shared `_types.py` for consistency with other Literal types
- Created new `history.py` response models file for clean separation
- Added endpoint to existing months router before the parameterized route

**Rationale:** The history feature is closely related to months and doesn't warrant a separate service module. This keeps the codebase cohesive and minimizes file proliferation.

## Files Modified

- `backend/app/responses/_types.py` - Added `ScoreTrendLiteral = Literal["improving", "declining", "stable"]`
- `backend/app/services/months.py` - Added 3 functions: `get_months_history()`, `_calculate_score_trend()`, `calculate_history_summary()`
- `backend/app/routers/months.py` - Added imports and `get_history()` endpoint

## Files Created

- `backend/app/responses/history.py` - Response models:
  - `MonthReference` - Lightweight reference for best/worst month (year, month, score)
  - `MonthHistory` - Single month data with `from_model()` classmethod
  - `HistorySummary` - Summary statistics (total_months, average_score, score_trend, best_month, worst_month)
  - `HistoryResponse` - Top-level response wrapper
  - `_format_month_label()` - Helper to format "Oct 2025" style labels

- `backend/tests/units/services/test_history.py` - 12 unit tests:
  - `TestGetMonthsHistory` (3 tests): limit behavior, empty database
  - `TestCalculateScoreTrend` (5 tests): improving/declining/stable logic, best/worst identification
  - `TestCalculateHistorySummary` (4 tests): average calculation, tie-breaking, empty handling

- `backend/tests/integration/test_history_api.py` - 6 integration tests:
  - Correct months count, chronological order, default limit
  - Max limit validation (422 for > 24), empty database, summary structure

## Key Implementation Details

### Response Model Pattern
Used `from_model()` classmethod following existing `MonthSummary` pattern:
```python
@classmethod
def from_model(cls, month: "Month") -> Self:
    return cls(
        year=month.year,
        month=month.month,
        month_label=_format_month_label(month.year, month.month),
        # ... other fields
    )
```

### Database Query Strategy
Query DESC then reverse for efficiency:
```python
result = db.query(Month).order_by(Month.year.desc(), Month.month.desc()).limit(limit).all()
result.reverse()  # Chronological order (oldest first)
```

### Score Trend Calculation
Compares average of last 3 months vs previous 3 months:
- "improving": recent > previous
- "declining": recent < previous
- "stable": equal or < 6 months of data

### Tie-Breaking Logic
For best/worst month when scores are equal, most recent month wins:
```python
for month in months:  # Oldest first iteration
    if month.score >= best.score:  # >= allows later (more recent) to win
        best = month
```

## Integration Points

- Reuses existing `MonthDataError` exception hierarchy
- Uses existing `_http_detail_for_db_error()` helper for error messages
- Follows three-tier error handling pattern (SQLAlchemyError → MonthQueryError → HTTPException 503)
- Uses same database session injection (`Depends(get_db)`)

## Testing Notes

- **Unit tests:** 12 tests covering service functions
- **Integration tests:** 6 tests covering API contract
- **Total new tests:** 18 tests (spec expected 14)
- All 220 project tests pass

### Test Coverage
- Empty database handling
- Limit parameter edge cases
- Chronological ordering verification
- Score trend calculation (improving/declining/stable)
- Tie-breaking for best/worst months
- Query parameter validation (422 for invalid range)
