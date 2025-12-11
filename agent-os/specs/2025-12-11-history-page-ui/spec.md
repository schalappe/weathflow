# Specification: History Page UI

## Goal

Create a dedicated history page that combines the Score Evolution and Spending Breakdown charts with a period selector, providing users a unified view of their budget trends over time.

## User Stories

- As a user, I want to see the evolution of my score over multiple months so I can identify trends and progress
- As a user, I want to select different time periods (3, 6, 12 months, all time) so I can focus on relevant historical data

## Specific Requirements

**History Page Route:**

- Create `/history` route accessible via navigation header
- Enable the currently disabled "History" link in NavBar
- Page title: "Historique" (French)

**Period Selector Component:**

- Dropdown with 4 options: "3 mois", "6 mois", "12 mois" (default), "Tout"
- Values: 3, 6, 12, 0 (where 0 = all time)
- Position: top-right corner of content area
- Uses shadcn/ui Select component
- Controlled component with `value` and `onChange` props

**Chart Integration:**

- Display existing `ScoreChart` component (line chart for score 0-3)
- Display existing `SpendingBreakdownChart` component (stacked bar chart)
- Pass fetched `months[]` data to both components
- Charts handle their own empty states internally

**Data Fetching:**

- Use existing `getMonthsHistory(months)` API client method
- Client-side fetching with `useEffect` to allow period changes without page reload
- Implement `isMounted` cleanup pattern to prevent memory leaks
- Refetch when period changes

**State Management:**

- Use `useReducer` pattern (matching dashboard-client.tsx)
- State shape: `{ pageState, period, months, error }`
- PageState: `"loading" | "loaded" | "empty" | "error"`
- Optimistic UI: show previous data while loading new period data

**Loading State:**

- Show centered loading spinner on initial load
- Keep showing old chart data during period switch (optimistic UI)

**Empty State:**

- French heading: "Aucune donnee historique"
- French message: "Importez vos premieres transactions pour voir l'evolution de votre budget."
- CTA button linking to `/import`: "Importer des transactions"

**Error State:**

- Display error alert with user-friendly message
- "Reessayer" (Retry) button to re-trigger data fetch

**Responsive Layout:**

- Mobile: charts stacked vertically
- Desktop (lg+): charts side-by-side in 2-column grid
- Container: `max-w-6xl mx-auto` matching dashboard

## Visual Design

No visual files provided. ASCII wireframe from PRD:

**`docs/product-development/features/13-history-page-ui.md` wireframe**

- Header bar with [Import] [History] navigation buttons
- Period selector dropdown positioned in top-right of chart section
- Score evolution line chart (Y-axis: 0-3, X-axis: months)
- Spending breakdown stacked bar chart below score chart
- Responsive: vertical stack on mobile, side-by-side on large screens

## Existing Code to Leverage

**ScoreChart - `frontend/components/history/score-chart.tsx`**

- What it does: Line chart showing score evolution over 12-month grid
- How to reuse: Import directly, pass `months: MonthHistory[]` prop
- Key exports: `ScoreChart` component
- Note: Has internal 12-month grid; works with any period but shows gaps

**SpendingBreakdownChart - `frontend/components/history/breakdown-chart.tsx`**

- What it does: Stacked bar chart showing Core/Choice/Compound percentages
- How to reuse: Import directly, pass `months: MonthHistory[]` and optional `className`
- Key exports: `SpendingBreakdownChart` component
- Note: Wrapped in ErrorBoundary, sorts data chronologically

**API Client - `frontend/lib/api-client.ts`**

- What it does: `getMonthsHistory(months)` fetches historical data
- How to reuse: Import and call with period value (3, 6, 12, or 0)
- Key exports: `getMonthsHistory` function returning `HistoryResponse`
- Note: Error handling built-in, throws user-friendly messages

**Dashboard Client Pattern - `frontend/components/dashboard/dashboard-client.tsx`**

- What it does: Establishes state management and data fetching patterns
- How to reuse: Replicate `useReducer` + `useEffect` pattern
- Key patterns: Discriminated union actions, `isMounted` cleanup, optimistic UI

**Types - `frontend/types/index.ts`**

- What it does: Defines `MonthHistory`, `HistoryResponse`, `HistorySummary` types
- How to reuse: Import types for state and props
- Key exports: `MonthHistory`, `HistoryResponse`

## Architecture Approach

**Component Design:**

- `app/history/page.tsx` - Server component wrapper with ErrorBoundary
- `components/history/history-client.tsx` - Main client component (~150 lines)
- `components/history/period-selector.tsx` - Period dropdown (~50 lines)

**Data Flow:**

1. Page mounts → dispatch `LOAD_START` → show spinner
2. useEffect triggers → `getMonthsHistory(period)` → API call
3. Success with data → dispatch `LOAD_SUCCESS` → show charts
4. Success empty → dispatch `LOAD_EMPTY` → show empty state
5. Failure → dispatch `LOAD_ERROR` → show error + retry
6. Period change → dispatch `SET_PERIOD` → keep old data, refetch

**Integration Points:**

- Enable History link in `app/layout.tsx` NavBar (currently disabled span → Link)
- Import existing chart components from `components/history/`
- Use `getMonthsHistory` from `lib/api-client.ts`
- Follow dashboard styling patterns (container, spacing, cards)

## Out of Scope

- Advice panel integration (Feature #16 - separate implementation)
- Data export from history page (Feature #18)
- Drill-down into specific month from chart clicks
- Custom date range picker (start/end month selection)
- Chart image export functionality
- Caching of previous period data
- Summary statistics display (average score, best/worst month)
- Modifying ScoreChart to dynamically adjust grid for different periods
