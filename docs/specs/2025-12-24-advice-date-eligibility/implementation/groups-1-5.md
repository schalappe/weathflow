# Implementation: Task Groups 1-5 (Advice Date Eligibility)

**Date:** 2024-12-24
**Task Groups:** All 5 groups implemented together

## Summary

Implemented backend eligibility service that determines when users can generate AI advice based on their most recent transaction data. The feature includes:
- Backend repository extensions for finding recent months/advice
- Eligibility service with date-window validation
- API integration returning eligibility info to frontend
- Frontend updates to use backend-provided eligibility

## Architecture Approach

**Chosen approach:** Clean separation with service layer owning business logic

Key design decisions:
1. Eligibility check as a separate service module (not embedded in API)
2. Backend-driven eligibility eliminates frontend date calculations
3. Dynamic history limit (12 for first advice, 3 otherwise)
4. Discriminated union types for type-safe API responses

## Files Modified

- `backend/app/repositories/month.py` - Added `get_most_recent()` method
- `backend/app/repositories/advice.py` - Added `has_any()` and `count()` methods
- `backend/app/api/advice.py` - Integrated eligibility checks in both endpoints
- `backend/app/responses/advice.py` - Added `EligibilityInfo` model
- `frontend/types/index.ts` - Added `EligibilityInfo` TypeScript type
- `frontend/components/history/advice-panel-content.tsx` - Updated to use backend eligibility

## Files Created

- `backend/app/services/advice/eligibility.py` - Core eligibility service
- `backend/tests/units/repositories/test_month_eligibility.py` - Repository tests
- `backend/tests/units/repositories/test_advice_eligibility.py` - Repository tests
- `backend/tests/units/services/advice/test_eligibility.py` - Service tests
- `backend/tests/integration/test_advice_eligibility.py` - API integration tests

## Files Deleted

- `frontend/__tests__/history/is-generation-allowed.test.tsx` - Obsolete client-side test

## Key Details

### EligibilityResult Dataclass

```python
@dataclass(frozen=True)
class EligibilityResult:
    is_eligible: bool
    history_limit: int  # 3 or 12
    is_first_advice: bool
    reason: str | None
```

### Eligibility Logic

1. Find most recent month in database
2. Check if target month is within window [most_recent - 1, most_recent]
3. Determine if first-advice scenario (0 advice or regenerating only advice)
4. Return appropriate history limit (12 for first, 3 otherwise)

### API Changes

- `GET /api/advice/{year}/{month}` now returns `eligibility` field
- `POST /api/advice/generate` returns 403 with reason when not eligible
- Uses dynamic `eligibility.history_limit` instead of hardcoded 3

## Integration Points

- Eligibility check happens early in both endpoints (before expensive DB queries)
- Frontend reducer stores eligibility in state
- EmptyState component displays eligibility reason when not eligible

## Testing Notes

- 19 eligibility-specific tests created
- 422 backend tests pass (no regressions)
- 235 frontend tests pass (no regressions)
- Code review score: 93/100 (frontend), no critical issues (backend)
