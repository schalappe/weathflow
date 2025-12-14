# Implementation: Sankey Cash Flow Diagram

**Date:** 2025-12-14
**Task Groups:** 1-6 (Complete Feature)

## Summary

Implemented a full-stack Sankey diagram visualization for the History page. The feature shows income flowing into spending categories (Core, Choice, Compound) with subcategory breakdowns. A red "Deficit" node appears when spending exceeds income.

## Architecture Approach

Selected the "Follow Existing Patterns" approach which maximizes consistency with the existing codebase:
- Backend: Repository → Service → API pattern
- Frontend: useReducer state management with parallel API fetching
- Testing: DatabaseTestCase for backend, vitest with mocks for frontend

## Files Modified

### Backend

- `backend/app/repositories/transaction.py` — Added `aggregate_by_subcategory()` method
- `backend/app/api/months.py` — Added `/cashflow` endpoint with imports

### Frontend

- `frontend/components/history/history-client.tsx` — Extended state with `cashFlowData`, added parallel fetch
- `frontend/lib/api-client.ts` — Added `getCashFlow()` function
- `frontend/lib/translations.ts` — Added `sankeyChart` section
- `frontend/types/index.ts` — Added `CashFlowResponse`, `CashFlowData`, `CategoryBreakdown` types

### Tests (Updated to include getCashFlow mock)

- `frontend/__tests__/history/history-client.test.tsx` — Added getCashFlow mock
- `frontend/__tests__/history/history-page.test.tsx` — Added getCashFlow mock

## Files Created

### Backend

- `backend/app/responses/cashflow.py` — Pydantic response models
- `backend/app/services/data/cashflow.py` — Service layer with deficit calculation
- `backend/tests/integration/test_cashflow_api.py` — API integration tests (4 tests)
- `backend/tests/units/repositories/test_transaction.py` — Added TestAggregateBySubcategory class (6 tests)
- `backend/tests/units/services/test_cashflow.py` — Service unit tests (6 tests)

### Frontend

- `frontend/components/history/sankey-chart.tsx` — SankeyChart component with Recharts
- `frontend/__tests__/history/sankey-chart.test.tsx` — Component tests (7 tests)
- `frontend/__tests__/lib/api-client-cashflow.test.ts` — API client tests (4 tests)

## Key Details

### Deficit Calculation

When `Core + Choice > Income`, a deficit is calculated:
```python
deficit = max(0.0, core_total + choice_total - income_total)
```

When deficit > 0, Compound is hidden and replaced with a red Deficit node (per user preference).

### Sankey Data Transformation

The `transformToSankeyData()` function builds:
1. **Nodes**: Income, Core, Choice, Compound (or Deficit), plus all subcategories
2. **Links**: Income → Categories, Categories → Subcategories

### Color Scheme

- Income: `#6a9bcc` (blue)
- Core: `#d97757` (orange)
- Choice: `#e8b931` (yellow)
- Compound: `#788c5d` (green)
- Deficit: `#c45a3b` (red)

## Integration Points

- **API Endpoint**: `GET /api/months/cashflow?months=12`
- **Period Selector**: Uses same period state as history charts (3, 6, 12, or 0 for all)
- **Parallel Fetching**: `Promise.all([getMonthsHistory(period), getCashFlow(period)])`

## Testing Notes

- **Backend**: 398 tests pass (16 new cashflow-related tests)
- **Frontend**: 217 tests pass (11 new cashflow-related tests)
- Code reviewer identified and fixed:
  - SQLAlchemy CASE/SUM ordering issue
  - Null safety guards in custom Recharts components
  - mypy type ignore for SQLAlchemy query return
