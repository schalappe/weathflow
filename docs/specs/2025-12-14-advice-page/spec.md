# Specification: Dedicated Advice Page

## Goal

Create a standalone `/advice` page that allows users to view, generate, and regenerate personalized financial advice for any month with imported data, replacing the embedded advice panel in the History page.

## User Stories

- As a user, I want to navigate to a dedicated advice page so that I can focus on my personalized recommendations without distraction
- As a user, I want to select any month with imported data so that I can review past advice or generate new advice for different periods
- As a user, I want the page to default to my most recent month so that I immediately see relevant advice

## Specific Requirements

**Month Navigation:**

- Display a month selector dropdown showing all months with imported transaction data
- Include months without existing advice (show generate prompt when selected)
- Default to the most recent month on page load
- Show loading state when switching between months

**Advice Display:**

- Display advice content for the selected month (analysis, problem areas, recommendations, encouragement)
- Show empty state with "Generate" button for months without advice
- Show "Regenerate" button for months with existing advice
- Display timestamp showing when advice was generated

**Page Structure:**

- Route: `/advice`
- Header with page title, subtitle, and month selector
- Main content area with advice panel
- Empty state when no months have imported data (prompt to import)

**Navigation Integration:**

- Add "Conseils" link to main navigation bar
- Use Lightbulb icon for consistency with advice theme
- Position after History link

**History Page Cleanup:**

- Remove AdvicePanel component from History page entirely
- All advice viewing happens exclusively on the new `/advice` page

## Visual Design

No visual assets provided. Follow existing UI patterns from History and Dashboard pages.

## Existing Code to Leverage

**AdvicePanel Component — `frontend/components/history/advice-panel.tsx`**

- What it does: Self-contained component that fetches, displays, generates, and regenerates advice
- How to reuse: Import directly and pass `year`, `month` props; component handles all internal state
- Key methods: Internal `getAdvice()`, `generateAdvice()` via useEffect and callbacks

**MonthSelector Component — `frontend/components/dashboard/month-selector.tsx`**

- What it does: Dropdown showing available months with year/month selection
- How to reuse: Import and pass `months`, `selectedYear`, `selectedMonth`, `onMonthChange` props
- Key methods: `formatMonthKey()`, `formatMonthDisplay()` for value/label formatting

**API Client Functions — `frontend/lib/api-client.ts`**

- `getMonthsList()`: Fetch all months with imported data
- `getAdvice(year, month)`: Check if advice exists for a month
- `generateAdvice(year, month, regenerate)`: Generate or regenerate advice

**Page Structure Pattern — `frontend/components/history/history-client.tsx`**

- What it does: Demonstrates useReducer pattern with loading/loaded/empty/error states
- How to reuse: Replicate state shape, action types, and reducer pattern
- Key methods: Effect-based data fetching triggered by pageState changes

**Navigation — `frontend/app/layout.tsx`**

- What it does: Global navigation with NavLink components
- How to reuse: Add new NavLink with Lightbulb icon for `/advice` route

## Architecture Approach

**Component Design:**

- `AdvicePageClient`: Main client component managing month selection and page state
- Reuses existing `AdvicePanel` for advice display (no modifications needed)
- Reuses existing `MonthSelector` for month dropdown

**State Management:**

```sql
State Shape:
- pageState: "loading" | "loaded" | "empty" | "error"
- monthsList: MonthSummary[]
- selectedYear: number | null
- selectedMonth: number | null
- error: string | null

Actions:
- LOAD_START: Begin fetching months list
- MONTHS_LOADED: Months fetched successfully, auto-select most recent
- LOAD_ERROR: Failed to fetch months
- SELECT_MONTH: User changed month selection
```

**Data Flow:**

1. Page mounts → Fetch months list via `getMonthsList()`
2. On success → Auto-select most recent month, render MonthSelector + AdvicePanel
3. User changes month → Update selectedYear/selectedMonth in state
4. AdvicePanel receives new props → Internally fetches advice for new month
5. AdvicePanel handles its own loading/empty/error states for advice content

**Integration Points:**

- Import `AdvicePanel` from `@/components/history/advice-panel`
- Import `MonthSelector` from `@/components/dashboard/month-selector`
- Add NavLink in `layout.tsx` navigation
- Remove AdvicePanel usage from `history-client.tsx`

**Files to Create:**

- `frontend/app/advice/page.tsx` — Server component wrapper
- `frontend/components/advice/advice-page-client.tsx` — Main client component

**Files to Modify:**

- `frontend/app/layout.tsx` — Add navigation link
- `frontend/components/history/history-client.tsx` — Remove AdvicePanel
- `frontend/lib/translations.ts` — Add new translations

## Out of Scope

- Side-by-side month comparison view
- Exporting advice to file
- Filtering by problem area type
- Advice history/versioning (only latest advice per month)
- Backend API modifications
- Moving AdvicePanel to a shared components folder
- Caching advice at page level (AdvicePanel handles this internally)
- Any changes to Dashboard or Import pages
