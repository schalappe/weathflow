# Specification: Spending Breakdown Chart

## Goal

Create a stacked bar chart component that visualizes Core/Choice/Compound spending distribution month-over-month, enabling users to track budget allocation trends across multiple months.

## User Stories

- As a budget-conscious user, I want to see my spending breakdown over time so that I can identify trends in my Core/Choice/Compound allocation
- As a user tracking my Money Map score, I want to compare my budget distribution across months so that I can see if I'm improving my spending habits

## Specific Requirements

**Stacked Bar Chart Visualization:**

- Display percentages stacked to 100% (not absolute amounts)
- Stack order from bottom to top: Core, Choice, Compound
- Each bar represents total spending distribution for one month
- Skip months with no spending data (do not display empty bars)

**Color Palette:**

- Core: Purple (#8b5cf6) - matches existing CATEGORY_COLORS.CORE
- Choice: Amber (#f59e0b) - matches existing CATEGORY_COLORS.CHOICE
- Compound: Emerald (#10b981) - matches existing CATEGORY_COLORS.COMPOUND
- Import colors from `@/lib/utils` for consistency

**Axis Configuration:**

- X-axis: Short month labels (Jan, Feb, Mar...) with fontSize 12
- Y-axis: Percentage scale 0-100% with ticks at 0, 25, 50, 75, 100
- Y-axis tick formatter: append "%" suffix
- Y-axis width: 40px to accommodate percentage labels

**Interactive Elements:**

- Custom tooltip showing full month name (e.g., "January 2025")
- Tooltip displays each category with color indicator and exact percentage (one decimal)
- Legend showing Core, Choice, Compound with color indicators
- Tooltip styling: `rounded-md border bg-background p-2 shadow-md` (matches ScoreChart)

**Data Transformation:**

- Filter out months where all percentages are zero
- Sort months chronologically using `sortMonthsChronologically` utility
- Transform MonthHistory to chart-friendly format with label and fullLabel fields

**Empty State:**

- Display "No spending data available" message when no valid months exist
- Maintain 250px height for consistent layout
- Use `data-testid="empty-state"` for testing

**Responsive Layout:**

- Use ResponsiveContainer with width="100%" and height={250}
- Chart automatically scales to container width
- Consistent with ScoreChart dimensions

**Component Structure:**

- Location: `frontend/components/history/breakdown-chart.tsx`
- Client component (`"use client"` directive required for Recharts)
- Wrapped in Card component with CardHeader and CardContent
- Accept optional className prop for layout customization

## Visual Design

No visual mockups provided. ASCII wireframe from PRD:

```txt
┌─────────────────────────────────────────────────────────┐
│  REPARTITION PAR MOIS                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  [Graphique en barres empilees]                  │   │
│  │  Core | Choice | Compound                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

Title should be "Spending Breakdown by Month" (English).

## Existing Code to Leverage

**Score Evolution Chart - `frontend/components/history/score-chart.tsx`**

- What it does: Line chart showing score progression over 12 months with custom tooltip
- How to reuse: Copy component structure, Card wrapper pattern, empty state handling, ResponsiveContainer setup
- Key patterns: `transformToChartData()` function, CustomTooltip component, data-testid attributes
- Found by: code-explorer analysis of similar feature

**Category Colors - `frontend/lib/utils.ts` (lines 72-78)**

- What it does: Centralized color constants for Money Map categories
- How to reuse: Import `CATEGORY_COLORS` directly - already has CORE, CHOICE, COMPOUND hex values
- Key exports: `CATEGORY_COLORS`, `sortMonthsChronologically`, `cn`
- Found by: code-explorer analysis of spending-pie-chart

**TypeScript Types - `frontend/types/index.ts` (lines 186-198)**

- What it does: Defines MonthHistory interface with percentage fields
- How to reuse: Import `MonthHistory` type for props interface
- Key exports: `MonthHistory` with `core_percentage`, `choice_percentage`, `compound_percentage`
- Found by: code-explorer analysis of Historical Data API

**API Client - `frontend/lib/api-client.ts` (lines 211-239)**

- What it does: Fetches historical month data from backend
- How to reuse: Data already fetched by parent component (History Page), passed as props
- Key exports: `getMonthsHistory()` returns `HistoryResponse` with `months: MonthHistory[]`
- Found by: code-explorer analysis of Historical Data API

**Spending Pie Chart - `frontend/components/dashboard/spending-pie-chart.tsx`**

- What it does: Pie chart showing category distribution with same colors
- How to reuse: Reference for CATEGORY_COLORS usage, empty state pattern
- Key patterns: Color application via Cell components, empty state check
- Found by: code-explorer analysis of color patterns

## Architecture Approach

**Component Design:**

- Single exported function: `SpendingBreakdownChart`
- Internal helper: `transformToChartData()` for data processing
- Internal component: `CustomTooltip` for hover interactions
- Internal interface: `BreakdownChartDataPoint` for chart data shape

**Data Flow:**

- Parent (History Page) fetches data via `getMonthsHistory()`
- Parent passes `MonthHistory[]` to component via `data` prop
- Component transforms data: filter empty → sort → map to chart format
- Recharts renders stacked bars with transformed data

**Integration Points:**

- Will be imported by History Page (Feature #13)
- Shares same data source as ScoreChart (`HistoryResponse.months`)
- Grid layout alongside ScoreChart: `md:grid-cols-2`

## Out of Scope

- Period selector (Feature #13 - History Page UI responsibility)
- Drill-down to individual month transactions
- Export chart as image
- Animation customization
- Click interactions on bars
- Data fetching (parent component responsibility)
- Absolute amount display (percentages only)
- Custom legend styling beyond Recharts defaults
- Bar width customization
- Grid lines on chart
