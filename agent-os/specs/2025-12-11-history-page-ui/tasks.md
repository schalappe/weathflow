# Task Breakdown: History Page UI

## Overview

Total Tasks: 12
Estimated Complexity: Low
Primary Stack: Next.js + TypeScript + shadcn/ui

## Task List

### Frontend Components

#### Task Group 1: Period Selector Component

**Dependencies:** None

- [x] 1.0 Complete period selector component
  - [x] 1.1 Write 3 focused tests for PeriodSelector
    - Test renders with default value (12)
    - Test onChange callback fires with correct value
    - Test all 4 options are present (3, 6, 12, 0)
  - [x] 1.2 Create PeriodSelector component
    - File: `frontend/components/history/period-selector.tsx`
    - Props: `{ value: number; onChange: (months: number) => void; disabled?: boolean }`
    - Use shadcn/ui Select component
    - Define PERIOD_OPTIONS constant: `[{ label: '3 mois', value: 3 }, ...]`
  - [x] 1.3 Style period selector
    - Match dashboard's MonthSelector styling pattern
    - Ensure dropdown width accommodates all labels
  - [x] 1.4 Ensure period selector tests pass
    - Run ONLY the 3 tests from 1.1
    - Do NOT run entire test suite

**Acceptance Criteria:**

- All 3 tests pass
- Dropdown shows 4 French options
- onChange fires correctly when selection changes
- Component is controlled (value prop works)

---

#### Task Group 2: History Client State Management

**Dependencies:** Task Group 1

- [x] 2.0 Complete history client state management
  - [x] 2.1 Write 4 focused tests for state management
    - Test initial state is loading with period=12
    - Test LOAD_SUCCESS sets pageState to "loaded" and stores months
    - Test LOAD_EMPTY sets pageState to "empty"
    - Test SET_PERIOD updates period and triggers loading
  - [x] 2.2 Define TypeScript types for state and actions
    - File: `frontend/components/history/history-client.tsx`
    - HistoryState: `{ pageState, period, months, error }`
    - HistoryAction: discriminated union with LOAD_START, LOAD_SUCCESS, LOAD_EMPTY, LOAD_ERROR, SET_PERIOD
  - [x] 2.3 Implement historyReducer function
    - Handle all 5 action types
    - SET_PERIOD should set pageState to "loading" (triggers refetch)
    - LOAD_SUCCESS should check if months array is empty → dispatch LOAD_EMPTY instead
  - [x] 2.4 Ensure state management tests pass
    - Run ONLY the 4 tests from 2.1
    - Do NOT run entire test suite

**Acceptance Criteria:**

- All 4 tests pass
- Reducer handles all action types correctly
- Types are properly defined
- State transitions are predictable

---

#### Task Group 3: History Client Data Fetching

**Dependencies:** Task Group 2

- [x] 3.0 Complete history client data fetching
  - [x] 3.1 Write 3 focused tests for data fetching
    - Test initial mount fetches data with period=12
    - Test error state displays when API fails
    - Test period change triggers new fetch
  - [x] 3.2 Implement useEffect for data fetching
    - Call `getMonthsHistory(state.period)` from `@/lib/api-client`
    - Use `isMounted` cleanup pattern (prevent memory leaks)
    - Dispatch LOAD_SUCCESS, LOAD_EMPTY, or LOAD_ERROR based on result
  - [x] 3.3 Implement handlePeriodChange callback
    - Use `useCallback` for memoization
    - Dispatch SET_PERIOD action with new value
    - useEffect dependency on `state.period` triggers refetch
  - [x] 3.4 Ensure data fetching tests pass
    - Run ONLY the 3 tests from 3.1
    - Do NOT run entire test suite

**Acceptance Criteria:**

- All 3 tests pass
- Data fetches on mount with default period
- Period changes trigger refetch
- Errors are caught and displayed
- No memory leaks (cleanup works)

---

#### Task Group 4: History Client UI Rendering

**Dependencies:** Task Group 3

- [x] 4.0 Complete history client UI rendering
  - [x] 4.1 Write 4 focused tests for UI states
    - Test loading state shows spinner
    - Test empty state shows French message and import button
    - Test error state shows alert with retry button
    - Test loaded state shows both charts
  - [x] 4.2 Implement loading state UI
    - Centered spinner during initial load
    - Optimistic UI: keep old charts visible during period switch
    - Check `state.pageState === "loading" && state.months.length === 0`
  - [x] 4.3 Implement empty state UI
    - Heading: "Aucune donnee historique"
    - Message: "Importez vos premieres transactions pour voir l'evolution de votre budget."
    - Button: Link to `/import` with text "Importer des transactions"
  - [x] 4.4 Implement error state UI
    - Use Alert component with destructive variant
    - Display `state.error` message
    - "Reessayer" button that dispatches LOAD_START
  - [x] 4.5 Implement loaded state UI
    - Header row with page title "Historique" and PeriodSelector
    - Responsive grid: `grid gap-6 lg:grid-cols-2`
    - Import and render ScoreChart with `months={state.months}`
    - Import and render SpendingBreakdownChart with `months={state.months}`
  - [x] 4.6 Ensure UI rendering tests pass
    - Run ONLY the 4 tests from 4.1
    - Do NOT run entire test suite

**Acceptance Criteria:**

- All 4 tests pass
- All 4 page states render correctly
- French text displays properly
- Charts receive correct data
- Layout is responsive

---

### Page Route & Navigation

#### Task Group 5: Page Route and Navigation

**Dependencies:** Task Group 4

- [x] 5.0 Complete page route and navigation
  - [x] 5.1 Write 2 focused tests for page integration
    - Test /history route renders HistoryClient
    - Test History link in NavBar navigates to /history
  - [x] 5.2 Create history page server component
    - File: `frontend/app/history/page.tsx`
    - Import ErrorBoundary and HistoryClient
    - Wrap HistoryClient in ErrorBoundary
    - Follow pattern from `app/page.tsx`
  - [x] 5.3 Enable History navigation link
    - File: `frontend/app/layout.tsx`
    - Change disabled `<span>` to `<Link href="/history">`
    - Apply same styling as Import link
    - Add active state styling (match current route)
  - [x] 5.4 Ensure page integration tests pass
    - Run ONLY the 2 tests from 5.1
    - Do NOT run entire test suite

**Acceptance Criteria:**

- All 2 tests pass
- /history route accessible
- History link in NavBar works
- ErrorBoundary catches runtime errors

---

### Testing & Verification

#### Task Group 6: Integration Testing & Verification

**Dependencies:** Task Groups 1-5

- [x] 6.0 Complete integration testing and verification
  - [x] 6.1 Review tests from Task Groups 1-5
    - Task Group 1: 3 tests (PeriodSelector)
    - Task Group 2: 4 tests (State management)
    - Task Group 3: 3 tests (Data fetching)
    - Task Group 4: 4 tests (UI rendering)
    - Task Group 5: 2 tests (Page integration)
    - Total: 16 tests
  - [x] 6.2 Identify critical gaps (if any)
    - Focus on end-to-end user workflows
    - Check period selection → chart update flow
    - Verify error recovery (retry button)
  - [x] 6.3 Write up to 4 additional integration tests (if needed)
    - Test full user flow: load page → change period → verify charts update
    - Test retry flow: error state → click retry → data loads
    - Maximum 4 additional tests
  - [x] 6.4 Manual verification checklist
    - [x] Navigate to /history from NavBar
    - [x] Verify default period is 12 months
    - [x] Change period to 3, 6, All - verify charts update
    - [x] Disconnect backend - verify error state appears
    - [x] Click retry - verify recovery
    - [x] Test responsive layout (mobile vs desktop)
  - [x] 6.5 Run all feature tests
    - Run all History Page UI tests (approximately 16-20 total)
    - Verify all tests pass

**Acceptance Criteria:**

- All 16-20 feature tests pass
- Manual verification checklist completed
- No console errors
- Responsive layout works

---

## Execution Order

1. **Task Group 1: Period Selector** - Foundation component, no dependencies
2. **Task Group 2: State Management** - Core logic for the page
3. **Task Group 3: Data Fetching** - Connect to API
4. **Task Group 4: UI Rendering** - Build out all page states
5. **Task Group 5: Page Route** - Wire up navigation
6. **Task Group 6: Integration Testing** - Verify everything works together

## Files to Create

| File                                              | Task Group | Size       |
| ------------------------------------------------- | ---------- | ---------- |
| `frontend/components/history/period-selector.tsx` | 1          | ~50 lines  |
| `frontend/components/history/history-client.tsx`  | 2-4        | ~150 lines |
| `frontend/app/history/page.tsx`                   | 5          | ~15 lines  |

## Files to Modify

| File                      | Task Group | Change                  |
| ------------------------- | ---------- | ----------------------- |
| `frontend/app/layout.tsx` | 5          | Enable History nav link |

## Estimated Total

- **New Code**: ~215 lines
- **Tests**: 16-20 tests
- **Duration**: 3-4 hours total
