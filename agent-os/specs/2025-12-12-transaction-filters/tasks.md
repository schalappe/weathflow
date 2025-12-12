# Task Breakdown: Transaction Filters

## Overview

Total Tasks: 22
Estimated Complexity: Medium
Primary Stack: FastAPI (Python) + Next.js (TypeScript)

## Task List

### Backend Layer

#### Task Group 1: Multi-Category Filter Support

**Dependencies:** None

- [x] 1.0 Complete backend multi-category filtering
  - [x] 1.1 Write 4 focused tests for multi-category filtering
    - Test single category filter returns only matching transactions
    - Test multiple categories filter (comma-separated) returns union of matches
    - Test invalid category values are silently ignored
    - Test empty/no category filter returns all transactions
  - [x] 1.2 Update router parameter from `category_type` to `category`
    - File: `backend/app/routers/months.py`
    - Change `category_type: MoneyMapType | None` to `category: str | None`
    - Add description: "Comma-separated category types (e.g., CORE,CHOICE)"
    - Parse comma-separated string into list of validated types
  - [x] 1.3 Update service function signature and filter logic
    - File: `backend/app/services/months.py`
    - Change `category_type: str | None` to `category_types: list[str] | None`
    - Replace equality filter with `Transaction.money_map_type.in_(category_types)`
  - [x] 1.4 Ensure backend tests pass
    - Run ONLY the 4 tests from 1.1
    - Verify existing single-category behavior still works

**Acceptance Criteria:**

- All 4 tests pass
- `GET /api/months/{year}/{month}?category=CORE,CHOICE` returns transactions matching either category
- Invalid category values in comma-separated list are ignored
- Empty category parameter returns all transactions (no filter)

---

### Frontend Foundation Layer

#### Task Group 2: Add Required Dependencies and Utilities

**Dependencies:** None (can run parallel with Task Group 1)

- [x] 2.0 Complete frontend foundation setup
  - [x] 2.1 Install shadcn/ui components
    - Run: `bun x shadcn@latest add input popover calendar`
    - Verify components appear in `frontend/components/ui/`
  - [x] 2.2 Create useDebounce hook
    - File: `frontend/lib/hooks/use-debounce.ts`
    - Accept generic value and delay (ms)
    - Return debounced value using setTimeout/clearTimeout pattern
  - [x] 2.3 Add TransactionFilters type and DEFAULT_FILTERS constant
    - File: `frontend/types/index.ts`
    - Interface: `categoryTypes: MoneyMapType[]`, `dateFrom: string | null`, `dateTo: string | null`, `searchQuery: string`
    - Export `DEFAULT_FILTERS` with empty arrays and null values
  - [x] 2.4 Add getActiveFilterCount utility function
    - File: `frontend/lib/utils.ts`
    - Count non-empty categoryTypes, non-null dates, non-empty searchQuery
    - Return total count (0-4)

**Acceptance Criteria:**

- Input, Popover, Calendar components available in `components/ui/`
- useDebounce hook works with 300ms delay
- TransactionFilters type exported from types/index.ts
- getActiveFilterCount returns correct count for various filter combinations

---

#### Task Group 3: Update API Client

**Dependencies:** Task Group 1, Task Group 2

- [x] 3.0 Complete API client filter support
  - [x] 3.1 Write 3 focused tests for API client filter params
    - Test filters are correctly appended as URL search params
    - Test empty filters don't add unnecessary params
    - Test category array is joined with commas
  - [x] 3.2 Update getMonthDetail function signature
    - File: `frontend/lib/api-client.ts`
    - Add optional `filters?: TransactionFilters` parameter
  - [x] 3.3 Implement filter param serialization
    - Add `category` param if `filters.categoryTypes.length > 0` (comma-joined)
    - Add `start_date` param if `filters.dateFrom` is set
    - Add `end_date` param if `filters.dateTo` is set
    - Add `search` param if `filters.searchQuery.trim()` is non-empty
  - [x] 3.4 Ensure API client tests pass
    - Run ONLY the 3 tests from 3.1

**Acceptance Criteria:**

- All 3 tests pass
- getMonthDetail correctly builds URL with filter params
- Empty filters result in clean URL (no empty params)

---

### Frontend State Management Layer

#### Task Group 4: Dashboard Reducer Filter State

**Dependencies:** Task Group 2

- [x] 4.0 Complete dashboard filter state management
  - [x] 4.1 Write 4 focused tests for filter state management
    - Test SET_FILTERS action updates filters and resets page to 1
    - Test SELECT_MONTH action resets filters to DEFAULT_FILTERS
    - Test filters persist during SET_PAGE action
    - Test initial state includes DEFAULT_FILTERS
  - [x] 4.2 Extend DashboardState with filters property
    - File: `frontend/types/index.ts`
    - Add `filters: TransactionFilters` to DashboardState interface
  - [x] 4.3 Add SET_FILTERS action type
    - File: `frontend/types/index.ts`
    - Add to DashboardAction union: `{ type: "SET_FILTERS"; payload: TransactionFilters }`
  - [x] 4.4 Update reducer to handle SET_FILTERS
    - File: `frontend/components/dashboard/dashboard-client.tsx`
    - Update filters state and reset currentPage to 1
    - Set pageState to "loading" to trigger refetch
  - [x] 4.5 Update SELECT_MONTH case to reset filters
    - Reset filters to DEFAULT_FILTERS when month changes
  - [x] 4.6 Update initialState with DEFAULT_FILTERS
    - Add `filters: DEFAULT_FILTERS` to initial reducer state
  - [x] 4.7 Ensure reducer tests pass
    - Run ONLY the 4 tests from 4.1

**Acceptance Criteria:**

- All 4 tests pass
- SET_FILTERS updates state and resets page
- Month change resets filters
- Initial state has empty filters

---

#### Task Group 5: Dashboard Data Fetching with Filters

**Dependencies:** Task Group 3, Task Group 4

- [x] 5.0 Complete filter-aware data fetching
  - [x] 5.1 Update useEffect dependency array
    - File: `frontend/components/dashboard/dashboard-client.tsx`
    - Add `state.filters` to the dependency array of the monthDetail fetch effect
  - [x] 5.2 Pass filters to getMonthDetail call
    - Update the API call to include `state.filters` parameter
  - [x] 5.3 Create handleFiltersChange callback
    - Create memoized callback using useCallback
    - Dispatch SET_FILTERS action with new filters

**Acceptance Criteria:**

- Changing filters triggers API refetch
- Filters are passed correctly to getMonthDetail
- handleFiltersChange callback is stable (memoized)

---

### Frontend UI Components Layer

#### Task Group 6: TransactionFilters Component

**Dependencies:** Task Group 2

- [x] 6.0 Complete TransactionFilters component
  - [x] 6.1 Write 5 focused tests for TransactionFilters
    - Test renders all filter controls (category, date from, date to, search, clear)
    - Test category checkbox toggle calls onFiltersChange
    - Test search input debounces by 300ms
    - Test clear button only visible when filters active
    - Test date pickers constrained to month bounds
  - [x] 6.2 Create component file and props interface
    - File: `frontend/components/dashboard/transaction-filters.tsx`
    - Props: `filters`, `onFiltersChange`, `monthBounds: { minDate, maxDate }`, `disabled?`
  - [x] 6.3 Implement category multi-select dropdown
    - Use Popover with checkboxes inside
    - Map MONEY_MAP_TYPES to checkbox items
    - Use CATEGORY_BADGE_CLASSES for color indicators
    - Toggle category in/out of categoryTypes array on click
  - [x] 6.4 Implement date range pickers
    - Two Popover + Calendar combos for dateFrom and dateTo
    - Constrain min/max dates using monthBounds prop
    - Clear button for each date field
  - [x] 6.5 Implement debounced search input
    - Local state for immediate input value
    - useDebounce hook with 300ms delay
    - useEffect to sync debounced value to onFiltersChange
  - [x] 6.6 Implement clear filters button and active count badge
    - Show clear button only when getActiveFilterCount > 0
    - Display Badge with active filter count
  - [x] 6.7 Ensure TransactionFilters tests pass
    - Run ONLY the 5 tests from 6.1

**Acceptance Criteria:**

- All 5 tests pass
- All filter controls render and function
- Search is debounced by 300ms
- Clear button visibility tied to active filters

---

#### Task Group 7: Integrate Filters into TransactionTable

**Dependencies:** Task Group 5, Task Group 6

- [x] 7.0 Complete TransactionTable filter integration
  - [x] 7.1 Update TransactionTableProps interface
    - File: `frontend/components/dashboard/transaction-table.tsx`
    - Add: `filters`, `onFiltersChange`, `monthBounds`
  - [x] 7.2 Add TransactionFilters component to Card header
    - Import TransactionFilters component
    - Position between Card title and table
    - Pass filters, onFiltersChange, monthBounds props
  - [x] 7.3 Update empty state for filtered results
    - Show "No transactions match your filters" message
    - Add "clear all filters" clickable link
    - Link calls onFiltersChange with DEFAULT_FILTERS
  - [x] 7.4 Update DashboardClient to pass filter props
    - File: `frontend/components/dashboard/dashboard-client.tsx`
    - Calculate monthBounds from selectedMonth
    - Pass filters, handleFiltersChange, monthBounds to TransactionTable

**Acceptance Criteria:**

- Filter bar appears above transaction table
- Filters function end-to-end (change filter → API call → updated table)
- Empty state shows filter-specific message with clear link

---

#### Task Group 8: Responsive Design

**Dependencies:** Task Group 7

- [x] 8.0 Complete responsive filter layout
  - [x] 8.1 Add responsive Tailwind classes to filter bar
    - Desktop (>=1024px): `flex flex-row gap-4`
    - Tablet (768-1023px): `flex flex-wrap gap-3`
    - Mobile (<768px): `flex flex-col gap-2 w-full`
  - [x] 8.2 Make individual filter controls responsive
    - Category dropdown: `w-full lg:w-auto`
    - Date pickers: `w-full sm:w-auto`
    - Search input: `w-full lg:flex-1`
    - Clear button: `w-full sm:w-auto`

**Acceptance Criteria:**

- Filters display correctly at all breakpoints
- Mobile layout is fully stacked
- Desktop layout is single horizontal row

---

### Testing Layer

#### Task Group 9: Test Review and Gap Analysis

**Dependencies:** Task Groups 1-8

- [x] 9.0 Review and fill critical test gaps
  - [x] 9.1 Review all tests from previous task groups
    - Task 1.1: 4 backend filter tests
    - Task 3.1: 3 API client tests
    - Task 4.1: 4 reducer tests
    - Task 6.1: 5 component tests
    - Total: 16 existing tests
  - [x] 9.2 Identify critical integration gaps
    - Focus on end-to-end filter workflows
    - Check pagination + filter interaction
    - Verify month change + filter reset
  - [x] 9.3 Write up to 6 additional integration tests
    - Test: Filter change resets pagination to page 1
    - Test: Changing month clears all active filters
    - Test: Combined filters (category + search + date) work together
    - Test: Empty filter state shows all transactions
    - Test: Clear filters button resets to default state
    - Test: Filter state persists through pagination
  - [x] 9.4 Run all feature-specific tests
    - Run all 22 tests (16 existing + 6 new)
    - Verify all pass

**Acceptance Criteria:**

- All 22 feature tests pass
- Critical integration workflows covered
- No regressions in existing functionality

---

## Execution Order

| Order | Task Group                       | Reason                                           |
| ----- | -------------------------------- | ------------------------------------------------ |
| 1     | Task Group 1 (Backend)           | Foundation - API must support multi-category     |
| 1     | Task Group 2 (Frontend Foundation) | Can run parallel with backend                  |
| 2     | Task Group 3 (API Client)        | Depends on backend + types                       |
| 2     | Task Group 4 (Reducer State)     | Depends on types                                 |
| 3     | Task Group 5 (Data Fetching)     | Depends on API client + reducer                  |
| 3     | Task Group 6 (Filter Component)  | Can run parallel with data fetching              |
| 4     | Task Group 7 (Integration)       | Depends on data fetching + component             |
| 5     | Task Group 8 (Responsive)        | Depends on integration                           |
| 6     | Task Group 9 (Testing)           | Final verification after all implementation      |

**Parallelization Opportunities:**

- Task Groups 1 & 2 can run in parallel (backend + frontend foundation)
- Task Groups 3 & 4 can run in parallel (API client + reducer)
- Task Groups 5 & 6 can run in parallel (data fetching + UI component)
