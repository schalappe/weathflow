# Task Breakdown: Monthly Dashboard UI

## Overview

Total Tasks: 24
Estimated Complexity: Medium
Primary Stack: Next.js 14 + TypeScript + shadcn/ui + Recharts

## Task List

### Foundation Layer

#### Task Group 1: Dependencies and Type Definitions

**Dependencies:** None

- [x] 1.0 Complete foundation layer
  - [x] 1.1 Install required dependencies
    - Run `bunx shadcn@latest add select` for month selector dropdown
    - Run `bun add recharts` for pie chart visualization
    - Verify installations in `package.json`
  - [x] 1.2 Add dashboard TypeScript types to `frontend/types/index.ts`
    - `MoneyMapType`: Union type for category values
    - `MonthSummary`: Month financial data with percentages and score
    - `TransactionResponse`: Individual transaction with categorization
    - `PaginationInfo`: Pagination metadata
    - `MonthsListResponse`: List response wrapper
    - `MonthDetailResponse`: Complete month detail response
    - `DashboardPageState`: State machine discriminator
    - `DashboardState`: Complete state interface
    - `DashboardAction`: Discriminated union of all reducer actions
    - Follow pattern from existing `ImportState` and `ImportAction` types
  - [x] 1.3 Add utility functions to `frontend/lib/utils.ts`
    - `CATEGORY_COLORS`: Hex colors for pie chart (violet, amber, emerald)
    - `CATEGORY_TAILWIND`: Tailwind classes for metric card accents
    - `THRESHOLDS`: Business rule constants (Core: 50, Choice: 30, Compound: 20)
    - `meetsThreshold(category, percentage)`: Check if threshold is met
    - `formatTransactionDate(dateString)`: Format date as DD/MM
  - [x] 1.4 Add API client functions to `frontend/lib/api-client.ts`
    - `getMonthsList()`: Fetch all imported months
    - `getMonthDetail(year, month, page, pageSize)`: Fetch month with transactions
    - Follow existing pattern with try-catch and `extractErrorMessage()`
    - Use URL SearchParams for pagination query parameters

**Acceptance Criteria:**

- Dependencies installed without errors
- TypeScript compiles without type errors
- Utility functions are exportable and typed
- API functions follow existing error handling pattern

---

### UI Components Layer

#### Task Group 2: Score Card Component

**Dependencies:** Task Group 1

- [x] 2.0 Complete score card component
  - [x] 2.1 Write 3 focused tests for ScoreCard
    - Test renders correct score format "X/3"
    - Test renders correct label (Poor/Need Improvement/Okay/Great)
    - Test applies correct color class based on score
  - [x] 2.2 Create `frontend/components/dashboard/score-card.tsx`
    - Props: `score`, `scoreLabel`, `monthDisplay`
    - Use shadcn Card component as container
    - Display month name prominently (e.g., "October 2025")
    - Show "Score: X/3 (Label)" with colored Badge
    - Apply background tint based on `SCORE_COLORS[score]`
    - Full-width layout matching wireframe
  - [x] 2.3 Ensure score card tests pass
    - Run ONLY tests from 2.1

**Acceptance Criteria:**

- Component renders all 4 score states correctly
- Colors match spec: green (3), yellow (2), orange (1), red (0)
- Month display uses French locale format

---

#### Task Group 3: Metric Card Component

**Dependencies:** Task Group 1

- [x] 3.0 Complete metric card component
  - [x] 3.1 Write 4 focused tests for MetricCard
    - Test renders category title and formatted amount
    - Test renders percentage for non-Income categories
    - Test shows checkmark when threshold met
    - Test shows X icon when threshold exceeded
  - [x] 3.2 Create `frontend/components/dashboard/metric-card.tsx`
    - Props: `title`, `amount`, `percentage?`, `isSuccess?`, `colorClass`
    - Use shadcn Card with left border accent
    - Display title in uppercase
    - Format amount with `formatCurrency()` (Euro, French locale)
    - Show percentage below amount (except Income card)
    - Render Check icon (green) or X icon (red) based on `isSuccess`
    - Use lucide-react icons: `Check`, `X`
  - [x] 3.3 Ensure metric card tests pass
    - Run ONLY tests from 3.1

**Acceptance Criteria:**

- Income card shows only amount (no percentage, no indicator)
- Core/Choice/Compound cards show amount, percentage, and indicator
- Colors match spec: blue (Income), violet (Core), amber (Choice), emerald (Compound)

---

#### Task Group 4: Spending Pie Chart Component

**Dependencies:** Task Group 1

- [x] 4.0 Complete pie chart component
  - [x] 4.1 Write 3 focused tests for SpendingPieChart
    - Test renders pie chart with three segments
    - Test displays legend with category names
    - Test handles empty/zero values gracefully
  - [x] 4.2 Create `frontend/components/dashboard/spending-pie-chart.tsx`
    - Props: `core`, `choice`, `compound`
    - Use Recharts: `PieChart`, `Pie`, `Cell`, `Legend`, `ResponsiveContainer`, `Tooltip`
    - Three segments with `CATEGORY_COLORS` (violet, amber, emerald)
    - Show legend below chart with category names
    - Add tooltip showing amount on hover
    - Handle case where all values are 0 (show empty state message)
  - [x] 4.3 Ensure pie chart tests pass
    - Run ONLY tests from 4.1

**Acceptance Criteria:**

- Chart renders correctly with real data
- Legend displays Core, Choice, Compound labels
- Tooltip shows formatted Euro amounts
- Empty state handled without errors

---

#### Task Group 5: Month Selector Component

**Dependencies:** Task Group 1

- [x] 5.0 Complete month selector component
  - [x] 5.1 Write 3 focused tests for MonthSelector
    - Test renders dropdown with month options
    - Test calls onMonthChange when selection changes
    - Test disables dropdown when isDisabled is true
  - [x] 5.2 Create `frontend/components/dashboard/month-selector.tsx`
    - Props: `months`, `selectedYear`, `selectedMonth`, `onMonthChange`, `isDisabled`
    - Use shadcn Select: `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`
    - Format options as "Oct 2025" using `formatMonthDisplay()`
    - Use `formatMonthKey()` as option value
    - Most recent month at top (assume backend returns sorted)
    - Disable when `isDisabled` is true
  - [x] 5.3 Ensure month selector tests pass
    - Run ONLY tests from 5.1

**Acceptance Criteria:**

- Dropdown shows all imported months
- Selection triggers callback with year and month
- Disabled state prevents interaction

---

#### Task Group 6: Transaction Table Component

**Dependencies:** Task Group 1

- [x] 6.0 Complete transaction table component
  - [x] 6.1 Write 4 focused tests for TransactionTable
    - Test renders table with correct columns (Date, Description, Amount, Category)
    - Test formats date as DD/MM
    - Test formats amount with sign (+/-)
    - Test renders pagination controls
  - [x] 6.2 Create `frontend/components/dashboard/transaction-table.tsx`
    - Props: `transactions`, `pagination`, `onPageChange`, `isLoading`
    - Use shadcn Table: `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`
    - Columns: Date (DD/MM), Description, Amount (signed Euro), Category (Badge)
    - Category badge with color based on `money_map_type`
    - Use `formatTransactionDate()` and `formatCurrency()` utilities
  - [x] 6.3 Add pagination controls to transaction table
    - Display "Page X of Y" in table header
    - Previous/Next buttons using shadcn Button
    - Disable Previous on page 1, Next on last page
    - Show loading overlay when `isLoading` is true
  - [x] 6.4 Ensure transaction table tests pass
    - Run ONLY tests from 6.1

**Acceptance Criteria:**

- Table displays all transaction columns correctly
- Pagination controls work and disable appropriately
- Loading state shows visual indicator
- Empty state shows "No transactions" message

---

### Orchestrator Layer

#### Task Group 7: Dashboard Client Component

**Dependencies:** Task Groups 1-6

- [x] 7.0 Complete dashboard client orchestrator
  - [x] 7.1 Write 5 focused tests for DashboardClient
    - Test initial load fetches months list
    - Test auto-selects most recent month on load
    - Test month change triggers data fetch
    - Test pagination change fetches new page
    - Test error state displays with retry button
  - [x] 7.2 Create `frontend/components/dashboard/dashboard-client.tsx` with reducer
    - Add `'use client'` directive
    - Define `dashboardReducer` function with all action handlers
    - Define `initialState` with pageState: "loading"
    - Implement action handlers: LOAD_START, MONTHS_LOADED, MONTH_DETAIL_LOADED, SELECT_MONTH, SET_PAGE, LOAD_ERROR, RETRY
  - [x] 7.3 Implement data fetching logic in dashboard client
    - `useEffect` on mount: call `getMonthsList()`, dispatch MONTHS_LOADED
    - `useEffect` on selectedMonth change: call `getMonthDetail()`, dispatch MONTH_DETAIL_LOADED
    - `useEffect` on currentPage change: refetch with new page
    - Wrap API calls in try-catch, dispatch LOAD_ERROR on failure
  - [x] 7.4 Implement callback handlers with useCallback
    - `handleMonthChange(year, month)`: dispatch SELECT_MONTH
    - `handlePageChange(page)`: dispatch SET_PAGE
    - `handleRetry()`: dispatch RETRY, re-trigger data load
  - [x] 7.5 Implement conditional rendering by pageState
    - "loading": Show centered spinner with "Loading..." text
    - "empty": Show empty state card with "No months imported" message and Link to `/import`
    - "error": Show Alert with error message and "Try Again" button
    - "loaded": Render all dashboard components
  - [x] 7.6 Wire up all sub-components in loaded state
    - MonthSelector with months list and handlers
    - ScoreCard with month detail data
    - 4 MetricCards (Income, Core, Choice, Compound) with computed props
    - SpendingPieChart with category totals
    - TransactionTable with transactions and pagination
    - Apply grid layout matching wireframe
  - [x] 7.7 Ensure dashboard client tests pass
    - Run ONLY tests from 7.1

**Acceptance Criteria:**

- All page states render correctly (loading, empty, error, loaded)
- Month selection and pagination work end-to-end
- Error handling displays user-friendly messages with retry
- Layout matches wireframe structure

---

### Integration Layer

#### Task Group 8: Route Integration and Polish

**Dependencies:** Task Group 7

- [x] 8.0 Complete route integration
  - [x] 8.1 Update `frontend/app/page.tsx` to render dashboard
    - Remove existing redirect to `/import`
    - Import and render `<DashboardClient />`
    - Keep as server component wrapper (no 'use client')
  - [x] 8.2 Add navigation header to dashboard
    - App title "Money Map Manager" on left
    - Navigation links on right: "Import" → `/import`, "History" → `/history` (disabled/placeholder)
    - Use consistent styling with existing app
  - [x] 8.3 Apply responsive layout adjustments
    - Desktop: 3+1 grid for metric cards, pie chart beside Compound
    - Tablet: 2x2 grid for metric cards, pie chart below
    - Mobile: Stack all cards vertically
    - Use Tailwind responsive classes (sm:, md:, lg:)
  - [x] 8.4 Manual integration testing
    - Test with no months imported (empty state)
    - Test with imported months (loaded state)
    - Test month switching
    - Test pagination navigation
    - Test error handling (stop backend, verify error state)

**Acceptance Criteria:**

- Dashboard loads at `/` route
- Navigation links work correctly
- Layout responds to screen size changes
- All states testable manually

---

### Testing Layer

#### Task Group 9: Test Review and Gap Analysis

**Dependencies:** Task Groups 1-8

- [x] 9.0 Review tests and fill critical gaps
  - [x] 9.1 Review all tests from Task Groups 2-7
    - ScoreCard: 3 tests (Task 2.1)
    - MetricCard: 4 tests (Task 3.1)
    - SpendingPieChart: 3 tests (Task 4.1)
    - MonthSelector: 3 tests (Task 5.1)
    - TransactionTable: 4 tests (Task 6.1)
    - DashboardClient: 5 tests (Task 7.1)
    - Total existing: 22 tests
  - [x] 9.2 Identify critical coverage gaps
    - Focus on integration points between components
    - Check edge cases: 0 income, all thresholds met/failed
    - Verify error recovery flow
  - [x] 9.3 Write up to 8 additional strategic tests
    - Test full data flow: API → state → render
    - Test threshold indicator logic for all categories
    - Test empty transaction list handling
    - Test pagination boundary conditions
  - [x] 9.4 Run all dashboard-related tests
    - Execute full test suite for dashboard feature
    - Expected total: approximately 25-30 tests
    - Verify all tests pass

**Acceptance Criteria:**

- All 25-30 dashboard tests pass
- Critical user workflows covered
- No more than 8 additional tests added
- Feature ready for production

---

## Execution Order

| Order | Task Group                 | Reason                                          |
| ----- | -------------------------- | ----------------------------------------------- |
| 1     | Task Group 1: Foundation   | Types and utilities required by all components  |
| 2     | Task Groups 2-6            | Presentational components (can be parallelized) |
| 3     | Task Group 7: Orchestrator | Wires all components together                   |
| 4     | Task Group 8: Integration  | Final routing and polish                        |
| 5     | Task Group 9: Testing      | Verify complete feature                         |

**Parallelization Note:** Task Groups 2, 3, 4, 5, and 6 have no dependencies on each other. They can be implemented in parallel after Task Group 1 is complete.

---

## Files to Create/Modify

| File                                                   | Action | Task Group |
| ------------------------------------------------------ | ------ | ---------- |
| `frontend/types/index.ts`                              | Modify | 1          |
| `frontend/lib/utils.ts`                                | Modify | 1          |
| `frontend/lib/api-client.ts`                           | Modify | 1          |
| `frontend/components/dashboard/score-card.tsx`         | Create | 2          |
| `frontend/components/dashboard/metric-card.tsx`        | Create | 3          |
| `frontend/components/dashboard/spending-pie-chart.tsx` | Create | 4          |
| `frontend/components/dashboard/month-selector.tsx`     | Create | 5          |
| `frontend/components/dashboard/transaction-table.tsx`  | Create | 6          |
| `frontend/components/dashboard/dashboard-client.tsx`   | Create | 7          |
| `frontend/app/page.tsx`                                | Modify | 8          |
