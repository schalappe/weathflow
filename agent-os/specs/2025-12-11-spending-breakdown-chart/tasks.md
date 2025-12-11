# Task Breakdown: Spending Breakdown Chart

## Overview

Total Tasks: 8
Estimated Complexity: Low
Primary Stack: Next.js + TypeScript + Recharts

## Task List

### Frontend Components

#### Task Group 1: Chart Component Implementation

**Dependencies:** None (API already exists)

- [ ] 1.0 Complete spending breakdown chart component
  - [ ] 1.1 Write 4 focused tests for chart component
    - Test: renders chart with valid spending data
    - Test: displays empty state when no data provided
    - Test: skips months with zero percentages
    - Test: renders responsive container with correct height
  - [ ] 1.2 Create component file with interfaces and imports
    - Create `frontend/components/history/breakdown-chart.tsx`
    - Add `"use client"` directive
    - Define `BreakdownChartDataPoint` interface (label, fullLabel, core, choice, compound)
    - Define `SpendingBreakdownChartProps` interface (data: MonthHistory[], className?: string)
    - Import: Recharts (BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend)
    - Import: Card components from `@/components/ui/card`
    - Import: `CATEGORY_COLORS`, `sortMonthsChronologically`, `cn` from `@/lib/utils`
    - Import: `MonthHistory` from `@/types`
  - [ ] 1.3 Implement `transformToChartData()` function
    - Filter out months where all percentages are zero
    - Sort using `sortMonthsChronologically` utility
    - Map to `BreakdownChartDataPoint` with short label (Jan) and full label (January 2025)
    - Use `toLocaleDateString("en-US", { month: "short" })` for X-axis labels
  - [ ] 1.4 Implement `CustomTooltip` component
    - Accept `active`, `payload`, `label` props from Recharts
    - Return null if not active or no payload
    - Display full month name from `fullLabel` field
    - Show each category with color indicator (3x3 rounded div) and percentage (one decimal)
    - Style: `rounded-md border bg-background p-2 shadow-md`
  - [ ] 1.5 Implement main `SpendingBreakdownChart` component
    - Transform data using `transformToChartData()`
    - Check isEmpty: `chartData.length === 0`
    - Render Card wrapper with CardHeader (title: "Spending Breakdown by Month") and CardContent
    - Empty state: div with `data-testid="empty-state"`, 250px height, centered text
    - Chart state: ResponsiveContainer width="100%" height={250}
  - [ ] 1.6 Configure Recharts BarChart with stacked bars
    - XAxis: `dataKey="label"`, `tick={{ fontSize: 12 }}`
    - YAxis: `domain={[0, 100]}`, `ticks={[0, 25, 50, 75, 100]}`, `tickFormatter={(v) => \`${v}%\`}`, `width={40}`
    - Tooltip: `content={<CustomTooltip />}`
    - Legend: default Recharts Legend component
    - Bar (Core): `dataKey="core"`, `name="Core"`, `stackId="spending"`, `fill={CATEGORY_COLORS.CORE}`
    - Bar (Choice): `dataKey="choice"`, `name="Choice"`, `stackId="spending"`, `fill={CATEGORY_COLORS.CHOICE}`
    - Bar (Compound): `dataKey="compound"`, `name="Compound"`, `stackId="spending"`, `fill={CATEGORY_COLORS.COMPOUND}`
  - [ ] 1.7 Ensure component tests pass
    - Run: `cd frontend && bun test breakdown-chart`
    - Verify all 4 tests from 1.1 pass
    - Do NOT run entire test suite

**Acceptance Criteria:**

- All 4 tests from 1.1 pass
- Chart renders stacked bars with correct colors (Core purple, Choice amber, Compound emerald)
- Tooltip shows exact percentages on hover
- Empty state displays when no valid data
- Responsive container scales to parent width

### Testing

#### Task Group 2: Test Review & Manual Verification

**Dependencies:** Task Group 1

- [ ] 2.0 Review and verify component functionality
  - [ ] 2.1 Review tests from Task Group 1
    - Verify 4 tests cover critical component behaviors
    - Check test coverage for empty state and data rendering
  - [ ] 2.2 Add up to 2 additional tests if gaps identified
    - Consider: tooltip displays correct percentage format (one decimal)
    - Consider: legend shows all three categories
    - Maximum 2 additional tests
  - [ ] 2.3 Manual browser verification
    - Start dev server: `make dev`
    - Create test data via import or use existing months
    - Navigate to where component will be used (or create temp test page)
    - Verify chart renders with real data
    - Verify tooltip appears on hover
    - Verify responsive behavior by resizing window
  - [ ] 2.4 Run all feature tests
    - Run: `cd frontend && bun test breakdown-chart`
    - Expected: 4-6 tests pass
    - Verify no regressions in related components

**Acceptance Criteria:**

- All feature tests pass (4-6 tests total)
- Manual verification confirms chart works with real data
- Tooltip displays correctly formatted percentages
- Component is ready for integration into History Page (Feature #13)

## Execution Order

1. **Task Group 1: Chart Component Implementation** - Core development work, creates the component from scratch following existing patterns
2. **Task Group 2: Test Review & Manual Verification** - Ensures quality and readiness for integration

## Notes

- This is a **frontend-only feature** - no backend changes needed
- Historical Data API already returns `core_percentage`, `choice_percentage`, `compound_percentage`
- Component will be integrated into History Page (Feature #13) later
- Follow patterns from `score-chart.tsx` for consistency
- Critical Recharts pattern: all `Bar` components share `stackId="spending"` for stacking
