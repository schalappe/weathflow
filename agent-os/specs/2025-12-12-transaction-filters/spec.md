# Specification: Transaction Filters

## Goal

Add filtering capabilities to the transaction table, allowing users to filter by category type (multi-select), date range, and search by description to find specific transactions quickly.

## User Stories

- As a user, I want to filter my transactions by category, date, and description so that I can quickly find specific transactions.
- As a user, I want to clear all filters with one click so that I can reset my view.

## Specific Requirements

**Category Multi-Select Filter:**

- Display dropdown with checkboxes for all five categories: INCOME, CORE, CHOICE, COMPOUND, EXCLUDED
- Allow selecting multiple categories simultaneously
- Empty selection means "show all categories" (no filter applied)
- Use existing `CATEGORY_BADGE_CLASSES` color scheme for visual consistency

**Date Range Filter:**

- Provide "Date From" and "Date To" date pickers
- Constrain selectable dates to the currently selected month's boundaries
- Use Popover + Calendar components from shadcn/ui
- Clear individual date fields independently

**Description Search:**

- Implement case-insensitive text search on transaction descriptions
- Apply 300ms debounce to prevent excessive API calls while typing
- Backend already escapes SQL LIKE wildcards via `_escape_like_pattern()`

**Filter Bar Layout:**

- Position filter controls above the transaction table within the same Card component
- Horizontal row: [Category dropdown] [Date From] [Date To] [Search input] [Clear button]
- Clear button only visible when at least one filter is active
- Display "Active filters: N" badge when filters are applied

**Pagination Reset:**

- Reset to page 1 whenever any filter changes
- Preserve filter state during pagination within the same month
- Reset filters to defaults when changing months

**Empty State:**

- Show "No transactions found" message when filters return zero results
- Include "Try adjusting your filters or clear all filters" with clickable link
- Clear all filters link resets to default state

**Backend Multi-Category Support:**

- Change `category_type` parameter to `category` (comma-separated string)
- Parse comma-separated values and validate against MoneyMapType enum
- Use SQL `IN` clause for filtering multiple categories

**Responsive Design:**

- Desktop (>=1024px): All filters in single horizontal row
- Tablet (768-1023px): Filters wrap to two rows if needed
- Mobile (<768px): Stacked vertical layout, each control full-width

## Visual Design

No mockup files provided. ASCII wireframe from feature spec:

```text
+---------------------------------------------------------------+
|  TRANSACTIONS                                    [Page 1/5]   |
+---------------------------------------------------------------+
|                                                               |
|  [Category v] [Date From] [Date To] [Search...     ] [Clear]  |
|                                                               |
|  Active filters: 2                                            |
|                                                               |
+---------------------------------------------------------------+
|  Date       Description          Amount      Category         |
|  29/10     CB Domoro             -2.50       CHOICE           |
|  29/10     Virement Salaire    +2823.29      INCOME           |
+---------------------------------------------------------------+
```

## Existing Code to Leverage

**TransactionTable Component - `frontend/components/dashboard/transaction-table.tsx`**

- What it does: Displays paginated transactions with category badges, amounts, pagination controls
- How to reuse: Extend props to accept filters and onFiltersChange callback, integrate filter bar
- Key methods/exports: TransactionTableProps interface, CATEGORY_BADGE_CLASSES usage pattern

**Dashboard Reducer - `frontend/components/dashboard/dashboard-client.tsx`**

- What it does: Manages all dashboard state via useReducer pattern with discriminated union actions
- How to reuse: Add `filters` to DashboardState, add `SET_FILTERS` action that resets page to 1
- Key methods/exports: dashboardReducer, DashboardState, DashboardAction types

**Backend Filtering - `backend/app/services/months.py` (get_transactions_filtered)**

- What it does: Applies category, search, date filters to transactions query with pagination
- How to reuse: Change `category_type: str | None` to `category_types: list[str] | None`, use `IN` clause
- Key methods/exports: `_escape_like_pattern()` for SQL injection prevention

**Category Utilities - `frontend/lib/category-options.ts` and `frontend/lib/utils.ts`**

- What it does: Provides MONEY_MAP_TYPES array, CATEGORY_BADGE_CLASSES color mapping
- How to reuse: Import directly for category dropdown options and badge styling
- Key methods/exports: MONEY_MAP_TYPES, CATEGORY_BADGE_CLASSES

**API Client - `frontend/lib/api-client.ts` (getMonthDetail)**

- What it does: Fetches month detail with pagination using URL.searchParams pattern
- How to reuse: Add optional filters parameter, append category/search/date_from/date_to params
- Key methods/exports: getMonthDetail function signature

## Architecture Approach

**Component Design:**

- New `TransactionFilters` component handles all filter UI controls
- Integrates within TransactionTable's Card header area
- Filter state lives in dashboard reducer (collocated with pagination state)
- New `useDebounce` hook created in `frontend/lib/hooks/use-debounce.ts`

**Data Flow:**

- User changes filter → `onFiltersChange` callback → `dispatch({ type: "SET_FILTERS" })`
- Reducer updates `state.filters` and resets `state.currentPage` to 1
- useEffect triggers `getMonthDetail()` with new filters
- API returns filtered transactions → UI updates

**Integration Points:**

- Extend `DashboardState` with `filters: TransactionFilters`
- Extend `DashboardAction` with `SET_FILTERS` action type
- Add shadcn components: Input, Popover, Calendar
- Backend: Change router param from `category_type` to `category` (comma-separated)

**Build Sequence:**

1. Backend: Update router and service for multi-category support
2. Frontend: Add shadcn components and useDebounce hook
3. Frontend: Add types (TransactionFilters, DEFAULT_FILTERS)
4. Frontend: Create TransactionFilters component
5. Frontend: Update dashboard reducer with SET_FILTERS action
6. Frontend: Update API client to pass filters
7. Frontend: Integrate filters into TransactionTable
8. Testing: Unit tests for filters, integration tests for filter + pagination

## Out of Scope

- Saving filter presets
- Exporting filtered results
- Advanced search (regex, multiple terms, exact match)
- Filter by amount range
- Filter by account name
- Filter by subcategory
- URL persistence of filter state
- Server-side only filtering (filters handled client-side before this)
- Collapsible filter section on mobile (optional future enhancement)
- Cross-month date filtering (filters constrained to selected month)
