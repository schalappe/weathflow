# Specification: Sankey Cash Flow Diagram

## Goal

Add a Sankey diagram to the history page that visualizes cash flow from Income through spending categories (Core/Choice/Compound) to individual subcategories, with a "Deficit" node shown in red when spending exceeds income.

## User Stories

- As a budget-conscious user, I want to see how my income flows into different spending categories so that I can visualize where my money goes
- As a Money Map follower, I want to see subcategory breakdowns (Groceries, Housing, Entertainment, etc.) so that I can identify specific areas to optimize
- As an overspender, I want to see a clear deficit indicator so that I understand when my spending exceeds my income

## Specific Requirements

**Sankey Diagram Visualization:**

- Display a Sankey diagram showing: Income → Categories → Subcategories
- Categories are: Core (orange), Choice (yellow), Compound (green)
- Subcategories flow from their parent category (e.g., Core → Groceries, Housing, Transportation)
- Use existing CATEGORY_COLORS for consistent theming
- Static visualization (no click/drill-down interactivity)
- Show hover tooltip with flow amount

**Deficit Handling:**

- When Core + Choice > Income, display a "Deficit" node
- Deficit node uses red color (#c45a3b) to indicate overspending
- Deficit flows into the category that caused the overspending
- Calculate: `deficit = max(0, core_total + choice_total - income_total)`

**Period Selection:**

- Integrate with existing PeriodSelector component (3, 6, 12 months, or all)
- Aggregate totals across the selected period
- Use `months=0` parameter for "all time" selection

**UI Placement:**

- Add as third card below the existing 2-column chart grid
- Full-width card spanning both columns
- Follow existing Card styling: border-0 shadow-lg, gradient icon background
- Chart height: 300px (slightly taller than existing 250px charts)

**Backend Endpoint:**

- New endpoint: `GET /api/months/cashflow?months=12`
- Return aggregated data grouped by money_map_type and money_map_subcategory
- Include category totals and subcategory breakdowns
- Include calculated deficit amount

**Empty State:**

- Show centered message when no transaction data exists
- Follow existing empty state pattern from breakdown-chart

## Existing Code to Leverage

**SpendingBreakdownChart - `frontend/components/history/breakdown-chart.tsx`**

- What it does: Recharts stacked bar chart with Card wrapper, custom tooltip, ErrorBoundary
- How to reuse: Replicate Card structure, tooltip pattern, empty state handling
- Key methods: `transformToChartData()`, `CustomTooltipContent`, ChartConfig pattern

**History Client - `frontend/components/history/history-client.tsx`**

- What it does: State management with useReducer, period-based data fetching
- How to reuse: Extend reducer state for cashflow data, add parallel fetch
- Key methods: `historyReducer`, `handlePeriodChange`, useEffect fetch pattern

**History API - `backend/app/api/months.py`**

- What it does: GET /api/months/history endpoint with period parameter
- How to reuse: Same Query parameter pattern, error handling, dependency injection
- Key methods: `get_history()`, MonthRepo/TransactionRepo injection

**Transaction Repository - `backend/app/repositories/transaction.py`**

- What it does: SQL aggregation with func.sum(), func.abs() for expenses
- How to reuse: Add new aggregate method with GROUP BY subcategory
- Key methods: `aggregate_totals()`, SQLAlchemy func patterns

**Utils - `frontend/lib/utils.ts`**

- What it does: Color constants, formatting utilities
- How to reuse: Import CATEGORY_COLORS, formatCurrency
- Key methods: CATEGORY_COLORS constant, formatCurrency()

## Architecture Approach

**Component Design:**

- `SankeyChart` - Presentational component receiving `CashFlowData` prop
- `transformToSankeyData()` - Pure function converting API response to Recharts format
- `CustomNode` - Custom node renderer applying category colors
- `CustomTooltipContent` - Tooltip showing flow source, target, and amount

**Data Flow:**

1. User selects period → dispatch SET_PERIOD action
2. useEffect triggers parallel fetch: `getMonthsHistory()` + `getCashFlow()`
3. Backend aggregates transactions by category/subcategory using SQL GROUP BY
4. Response contains category totals + subcategory breakdowns + deficit
5. Frontend transforms to Sankey format: nodes[] + links[]
6. Recharts renders diagram with custom styling

**Integration Points:**

- Extends existing `HistoryState` with `cashFlowData: CashFlowData | null`
- Reuses `PeriodSelector` component without modification
- Follows existing ErrorBoundary wrapper pattern
- Uses translation system (t.sankeyChart.*)

## Out of Scope

- Interactive features (click to filter, drill-down to transactions)
- Animations or transitions on data load
- Export functionality for the Sankey diagram
- Comparison between different periods
- Mobile-specific responsive layout
- Custom color selection by user
- Modifying existing ScoreChart or BreakdownChart
- Adding new subcategory classification logic
- Historical trend of cash flow over time
- Percentage view toggle (amounts only)
