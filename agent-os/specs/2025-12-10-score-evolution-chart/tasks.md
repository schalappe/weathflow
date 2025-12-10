# Task Breakdown: Score Evolution Chart

## Overview

Total Tasks: 12
Estimated Complexity: Low
Primary Stack: Next.js + TypeScript + Recharts (Frontend-only feature)

**Note:** This is a frontend-only feature. The backend API (`GET /api/months/history`) already exists.

## Task List

### Foundation Layer

#### Task Group 1: Types and Constants

**Dependencies:** None

- [ ] 1.0 Complete types and constants
  - [ ] 1.1 Add TypeScript types to `frontend/types/index.ts`
    - Add `ScoreTrend` type: `"improving" | "declining" | "stable"`
    - Add `MonthHistory` interface with all fields from API response
    - Add `MonthReference` interface (year, month, score)
    - Add `HistorySummary` interface with trend and statistics
    - Add `HistoryResponse` interface (months + summary)
    - Follow existing type patterns in the file
  - [ ] 1.2 Add `SCORE_COLORS_HEX` constant to `frontend/lib/utils.ts`
    - Add after existing `SCORE_COLORS` constant (around line 61)
    - Type: `Record<number, string>`
    - Values: 0="#ef4444", 1="#f97316", 2="#eab308", 3="#22c55e"
  - [ ] 1.3 Verify TypeScript compilation
    - Run `bun run lint` to check for type errors
    - Ensure no conflicts with existing types

**Acceptance Criteria:**

- All new types compile without errors
- Types match backend API response structure
- `SCORE_COLORS_HEX` constant is exported and accessible

---

### API Client Layer

#### Task Group 2: API Client Function

**Dependencies:** Task Group 1

- [ ] 2.0 Complete API client function
  - [ ] 2.1 Add `HistoryResponse` import to `frontend/lib/api-client.ts`
    - Import from `@/types`
  - [ ] 2.2 Implement `getMonthsHistory()` function
    - Parameters: `months: number = 12`
    - Return type: `Promise<HistoryResponse>`
    - URL: `${API_BASE}/api/months/history?months=${months}`
    - Follow existing patterns: `safeParseJson<T>()`, `extractErrorMessage()`
    - Add network error handling with try/catch
  - [ ] 2.3 Verify API client works
    - Manually test endpoint in browser: `http://localhost:8000/api/months/history?months=12`
    - Confirm response structure matches types

**Acceptance Criteria:**

- Function exported from api-client.ts
- Returns typed `HistoryResponse`
- Error handling matches existing patterns

---

### UI Component Layer

#### Task Group 3: ScoreChart Component

**Dependencies:** Task Group 2

- [ ] 3.0 Complete ScoreChart component
  - [ ] 3.1 Write 4 focused tests for ScoreChart
    - Test 1: Renders chart with valid data (no empty state)
    - Test 2: Displays empty state when months array is empty
    - Test 3: Chart container exists (`.recharts-responsive-container`)
    - Test 4: Card title displays correct text
    - Location: `frontend/__tests__/history/score-chart.test.tsx`
    - Mock ResizeObserver in beforeAll
  - [ ] 3.2 Create `frontend/components/history/` directory
    - Create empty directory for history-related components
  - [ ] 3.3 Create ScoreChart component structure
    - File: `frontend/components/history/score-chart.tsx`
    - Add `"use client"` directive
    - Define `ScoreChartProps` interface: `{ months: MonthHistory[] }`
    - Import: Card components, Recharts components, SCORE_COLORS_HEX
    - Export named function `ScoreChart`
  - [ ] 3.4 Implement data transformation logic
    - Create `ChartDataPoint` interface: `{ name, fullMonth, score, label }`
    - Build `transformToChartData()` function
    - Generate last 12 months range
    - Map API data to range, fill gaps with `null`
    - Return array of ChartDataPoint
  - [ ] 3.5 Implement empty state
    - Check `months.length === 0`
    - Return Card with centered message "No historical data available"
    - Match 250px height with `h-[250px]`
    - Use `text-muted-foreground` styling
  - [ ] 3.6 Implement Recharts LineChart
    - ResponsiveContainer: `width="100%"` `height={250}`
    - LineChart with transformed data
    - XAxis: `dataKey="name"` (month abbreviation)
    - YAxis: domain `[0, 3]`, ticks `[0, 1, 2, 3]`
    - Line: `dataKey="score"`, `connectNulls={false}`, stroke color
  - [ ] 3.7 Add ReferenceArea score zones
    - Zone 0-1: `fill={SCORE_COLORS_HEX[0]}` `fillOpacity={0.1}`
    - Zone 1-2: `fill={SCORE_COLORS_HEX[1]}` `fillOpacity={0.1}`
    - Zone 2-3: `fill={SCORE_COLORS_HEX[2]}` `fillOpacity={0.1}`
  - [ ] 3.8 Implement custom Tooltip
    - Create `CustomTooltip` component inline
    - Props: `active`, `payload`
    - Display: fullMonth, score/3, label
    - Return null for null scores (gaps)
    - Style: `bg-background border rounded-md p-2 shadow-md`
  - [ ] 3.9 Ensure ScoreChart tests pass
    - Run: `bun run test frontend/__tests__/history/score-chart.test.tsx`
    - All 4 tests should pass

**Acceptance Criteria:**

- All 4 tests pass
- Component renders line chart with score data
- Empty state displays when no data
- Tooltip shows month details on hover
- Gaps appear for missing months
- Score zones visible as colored backgrounds

---

### Testing Layer

#### Task Group 4: Test Review and Final Verification

**Dependencies:** Task Group 3

- [ ] 4.0 Complete testing and verification
  - [ ] 4.1 Review existing tests
    - Review the 4 tests from Task Group 3
    - Verify test coverage for critical behaviors
  - [ ] 4.2 Add up to 3 additional integration tests if needed
    - Test tooltip content appears on simulated hover (if feasible)
    - Test data transformation with missing months
    - Test score zone rendering
  - [ ] 4.3 Run all ScoreChart tests
    - Run: `bun run test frontend/__tests__/history/`
    - All tests should pass (4-7 tests total)
  - [ ] 4.4 Manual visual verification
    - Create a temporary test page or use Storybook
    - Verify chart renders correctly with real API data
    - Check responsive behavior
    - Verify tooltip styling matches app design

**Acceptance Criteria:**

- All tests pass (4-7 tests total)
- Component visually matches wireframe
- Tooltip displays correct information
- Chart is responsive

---

## Execution Order

1. **Task Group 1: Types and Constants** - Foundation for type safety
2. **Task Group 2: API Client Function** - Enables data fetching
3. **Task Group 3: ScoreChart Component** - Main implementation
4. **Task Group 4: Testing and Verification** - Quality assurance

## Files to Create/Modify

| Action | File                                              |
| ------ | ------------------------------------------------- |
| Modify | `frontend/types/index.ts`                         |
| Modify | `frontend/lib/utils.ts`                           |
| Modify | `frontend/lib/api-client.ts`                      |
| Create | `frontend/components/history/score-chart.tsx`     |
| Create | `frontend/__tests__/history/score-chart.test.tsx` |

## Notes

- **API already exists**: `GET /api/months/history?months=12` is complete
- **Follow existing patterns**: Use `spending-pie-chart.tsx` as reference
- **Component location**: `frontend/components/history/` for future history page components
- **Will be consumed by**: History Page UI (roadmap item #13)
