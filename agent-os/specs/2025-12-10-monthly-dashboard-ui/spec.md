# Specification: Monthly Dashboard UI

## Goal

Build the main dashboard page showing the user's Money Map score, financial metrics by category, spending distribution chart, and paginated transaction list for a selected month.

## User Stories

- As a budget-conscious user, I want to see my Money Map score at a glance so that I know if I'm meeting my 50/30/20 targets
- As a user, I want to view my spending breakdown by Core/Choice/Compound so that I understand where my money goes
- As a user, I want to navigate between imported months so that I can review my financial history

## Specific Requirements

**Score Card Display:**

- Show month name (e.g., "October 2025") prominently
- Display score as "X/3" with label (Poor/Need Improvement/Okay/Great)
- Color-code based on score: 0=red, 1=orange, 2=yellow, 3=green
- Full-width card at top of dashboard

**Metric Cards (4 cards):**

- Income card: amount only, blue accent
- Core card: amount, percentage, threshold indicator (≤50%), violet accent
- Choice card: amount, percentage, threshold indicator (≤30%), amber accent
- Compound card: amount, percentage, threshold indicator (≥20%), emerald accent
- Show checkmark (green) if threshold met, X (red) if exceeded
- Format amounts as Euro with French locale

**Spending Pie Chart:**

- Display Core/Choice/Compound distribution (exclude Income and Excluded)
- Use category colors: violet (Core), amber (Choice), emerald (Compound)
- Show legend with category names
- Handle empty state gracefully

**Transaction Table:**

- Columns: Date, Description, Amount, Category
- Date format: DD/MM
- Amount: signed Euro format (+€ for income, -€ for expenses)
- Category: colored badge (INCOME/CORE/CHOICE/COMPOUND/EXCLUDED)
- Paginated with 50 rows per page
- Previous/Next navigation with "Page X of Y" indicator

**Month Selector:**

- Dropdown listing all imported months
- Format: "Oct 2025" (short month name + year)
- Most recent month at top (reverse chronological)
- Auto-select most recent month on page load
- Disabled during loading states

**State Management:**

- Loading state: spinner during data fetch
- Empty state: "No months imported yet" with CTA to import page
- Error state: alert with error message and retry button
- Reset to page 1 when changing months

## Visual Design

**`planning/visuals/wireframe-monthly-dashboard-ui.md`**

- Header bar with "Money Map Manager" title and navigation links (Import, History)
- Score card banner spanning full width below header
- 4 metric cards in responsive grid (3+1 layout on desktop)
- Pie chart positioned adjacent to metric cards
- Transaction table spanning full width at bottom
- Pagination controls in table header

**Color Palette (from PRD):**

- Score colors: green-500, yellow-500, orange-500, red-500
- Category colors: blue-500 (Income), violet-500 (Core), amber-500 (Choice), emerald-500 (Compound), gray-500 (Excluded)

## Existing Code to Leverage

**Import Page Pattern - `frontend/components/import/import-page-client.tsx`**

- What it does: Orchestrator component using `useReducer` with discriminated union actions
- How to reuse: Replicate state machine pattern (pageState discriminator, typed actions, useCallback handlers)
- Key methods: `dispatch()` for state changes, `useEffect` for data fetching

**API Client - `frontend/lib/api-client.ts`**

- What it does: Centralized API functions with `extractErrorMessage()` helper
- How to reuse: Add `getMonthsList()` and `getMonthDetail()` functions following same pattern
- Key methods: try-catch with user-friendly error messages, typed responses

**Utility Functions - `frontend/lib/utils.ts`**

- What it does: Formatting and helper functions
- How to reuse: Use existing `formatCurrency()`, `formatMonthDisplay()`, `SCORE_COLORS`
- Key methods: Add `CATEGORY_COLORS`, `meetsThreshold()`, `formatTransactionDate()`

**Type Definitions - `frontend/types/index.ts`**

- What it does: TypeScript types mirroring backend responses
- How to reuse: Add `MonthSummary`, `TransactionResponse`, `MonthDetailResponse`, dashboard state types
- Key methods: Discriminated union pattern for actions

**shadcn/ui Components - `frontend/components/ui/`**

- What it does: Pre-built accessible components
- How to reuse: Card, Badge, Button, Alert, Table, Tooltip (already installed)
- Key methods: Need to install Select component via `bunx shadcn@latest add select`

## Architecture Approach

**Component Design:**

- `dashboard-client.tsx`: Main orchestrator with reducer, handles all state and API calls
- `score-card.tsx`: Displays score with color and label, receives props only
- `metric-card.tsx`: Single metric display with threshold indicator
- `spending-pie-chart.tsx`: Recharts pie chart for category distribution
- `transaction-table.tsx`: Table with pagination, emits onPageChange callback
- `month-selector.tsx`: Select dropdown, emits onMonthChange callback

**Data Flow:**

```sql
Page Load → LOAD_START → getMonthsList() → MONTHS_LOADED
         → Auto-select latest → getMonthDetail() → MONTH_DETAIL_LOADED
         → Render components with monthDetail data

Month Change → SELECT_MONTH → Reset page to 1 → getMonthDetail() → Update UI

Page Change → SET_PAGE → getMonthDetail(newPage) → Update table only
```

**State Shape:**

```typescript
interface DashboardState {
  pageState: "loading" | "loaded" | "empty" | "error";
  monthsList: MonthSummary[];
  selectedMonth: { year: number; month: number } | null;
  monthDetail: MonthDetailResponse | null;
  currentPage: number;
  error: string | null;
}
```

**Integration Points:**

- Backend API: `GET /api/months` and `GET /api/months/{year}/{month}`
- Navigation: Link to `/import` in empty state, navigation links in header
- Recharts: Install via `bun add recharts`

## Out of Scope

- Transaction filtering by category, date range, or search text (Item #17)
- Inline transaction editing or category correction (Item #9)
- Score evolution chart or historical trends (Item #11)
- Spending breakdown chart over multiple months (Item #12)
- Advice panel with AI recommendations (Item #16)
- Data export functionality (Item #18)
- Mobile-optimized layout (basic responsive support only)
- Transaction sorting by column
- Keyboard shortcuts for navigation
- Dark mode theming
