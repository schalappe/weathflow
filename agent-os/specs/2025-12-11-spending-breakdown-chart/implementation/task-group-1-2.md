# Implementation: Task Groups 1-2 (Chart Component + Test Review)

**Date:** 2025-12-11
**Task Groups:** 1 (Chart Component Implementation) + 2 (Test Review & Manual Verification)
**Implementer:** implement-task command

## Summary

Implemented the SpendingBreakdownChart component - a stacked bar chart visualizing Core/Choice/Compound spending distribution month-over-month. Also created shared test utilities and refactored for DRY compliance.

## Architecture Approach

**Pattern Replication**: Followed existing `ScoreChart` patterns exactly:
- `"use client"` directive for Recharts
- Card wrapper with CardHeader/CardContent
- `transformToChartData()` for data processing
- `CustomTooltip` for hover interactions
- Empty state with `data-testid="empty-state"`

**Key Difference**: Uses `BarChart` with stacked `Bar` components (via `stackId`) instead of `LineChart` with `ReferenceArea`.

## Files Modified

- `frontend/__tests__/history/score-chart.test.tsx` - Updated to use shared test factory

## Files Created

- `frontend/components/history/breakdown-chart.tsx` - Main chart component (150 lines)
  - `SpendingBreakdownChart` - Exported component
  - `CustomTooltip` - Internal tooltip with color indicators
  - `transformToChartData()` - Filters zeros, sorts chronologically
  - `BreakdownChartDataPoint` - Internal interface

- `frontend/__tests__/history/breakdown-chart.test.tsx` - Test suite (67 lines)
  - 4 tests covering: valid data, empty state, zero filtering, responsive container

- `frontend/__tests__/utils/test-factories.ts` - Shared test utilities (40 lines)
  - `createMonthHistory()` - Flexible factory with percentage options

## Key Implementation Details

**Stacked Bar Configuration:**
```tsx
<Bar dataKey="core" name="Core" stackId="spending" fill={CATEGORY_COLORS.CORE} />
<Bar dataKey="choice" name="Choice" stackId="spending" fill={CATEGORY_COLORS.CHOICE} />
<Bar dataKey="compound" name="Compound" stackId="spending" fill={CATEGORY_COLORS.COMPOUND} />
```
- All bars share `stackId="spending"` for proper stacking
- Order determines visual stacking (Core bottom, Compound top)

**Data Transformation:**
```tsx
function transformToChartData(months: MonthHistory[]): BreakdownChartDataPoint[] {
  // 1. Filter months where all percentages are zero
  // 2. Sort chronologically using sortMonthsChronologically utility
  // 3. Map to chart format with short/full labels
}
```

**DRY Improvements:**
- Extracted `createMonthHistory` to shared test factory
- Renamed `data` prop to `months` for API consistency with ScoreChart

## Integration Points

- Imports `CATEGORY_COLORS` and `sortMonthsChronologically` from `lib/utils.ts`
- Uses `MonthHistory` type from `types/index.ts`
- Ready for integration into History Page (Feature #13)
- Accepts optional `className` prop for layout customization

## Testing Notes

**Tests Written (4 total):**
1. `renders chart with valid spending data` - Verifies title, container, no empty state
2. `displays empty state when no data provided` - Verifies empty state rendering
3. `skips months with zero percentages` - Verifies filtering logic
4. `renders responsive container with correct height` - Verifies Recharts setup

**Additional Test Coverage:**
- Score chart tests updated to use shared factory
- All 86 frontend tests pass
