# Specification: Score Evolution Chart

## Goal

Build a line chart component showing Money Map score (0-3) progression over the last 12 months, enabling users to visualize their budget adherence trends.

## User Stories

- As a user, I want to see my score evolution over multiple months so I can identify trends and progress.
- As a user, I want to hover over data points to see detailed information about each month's performance.

## Specific Requirements

**Line Chart Display:**

- X-axis: months in abbreviated format (Jan, Feb, Mar...)
- Y-axis: score scale 0-3 with integer tick marks
- Line connecting data points with dots at each month
- Use `connectNulls={false}` to show gaps for missing months

**Score Threshold Zones:**

- Colored background zones indicating score quality:
  - 0-1: Red zone (#ef4444, 10% opacity)
  - 1-2: Orange zone (#f97316, 10% opacity)
  - 2-3: Yellow/Green zone (#eab308, 10% opacity)
- Implement using Recharts `ReferenceArea` component

**Interactive Tooltip:**

- Show on hover: full month name (e.g., "Oct 2025"), exact score, score label
- Custom tooltip component matching app styling
- Hide tooltip when hovering over gaps (null data points)

**Empty State:**

- Display centered message "No historical data available" when no months exist
- Match 250px chart height for layout consistency
- Use `text-muted-foreground` styling

**Data Transformation:**

- Generate last 12 months range regardless of API data
- Map API response to expected range, filling missing months with `null` scores
- Transform `month_label` from API to chart-friendly format

**Responsive Container:**

- Use Recharts `ResponsiveContainer` with `width="100%"` and `height={250}`
- Wrap in shadcn/ui Card with header "Score Evolution (12 derniers mois)"

## Visual Design

**`planning/visuals/wireframe-score.md`**

- Title: "EVOLUTION DU SCORE (12 derniers mois)" in CardHeader
- Chart area showing line graph with Y-axis 0-3
- X-axis with month abbreviations
- Data points connected by line at varying score levels
- Contained within Card component matching dashboard styling

## Existing Code to Leverage

**SpendingPieChart - `frontend/components/dashboard/spending-pie-chart.tsx`**

- What it does: Recharts PieChart with Card wrapper, empty state, tooltip
- How to reuse: Copy structure - `"use client"`, Card wrapper, ResponsiveContainer pattern
- Key methods: Empty state check, data transformation, Tooltip formatter

**Card Component - `frontend/components/ui/card.tsx`**

- What it does: Composable card with CardHeader, CardTitle, CardContent
- How to reuse: Import and wrap chart exactly like SpendingPieChart
- Key methods: `<Card>`, `<CardHeader>`, `<CardTitle>`, `<CardContent>`

**Utils Constants - `frontend/lib/utils.ts`**

- What it does: Color constants (SCORE_COLORS, CATEGORY_COLORS)
- How to reuse: Add new `SCORE_COLORS_HEX` constant following same pattern
- Key methods: `Record<number, string>` type for score-to-hex mapping

**API Client - `frontend/lib/api-client.ts`**

- What it does: Centralized API calls with error handling
- How to reuse: Add `getMonthsHistory()` function following existing patterns
- Key methods: `safeParseJson<T>()`, `extractErrorMessage()`, `API_BASE`

**History API - `GET /api/months/history`**

- What it does: Returns historical month data with scores (already implemented)
- How to reuse: Call with `?months=12` query parameter
- Key methods: Returns `{ months: MonthHistory[], summary: HistorySummary }`

## Architecture Approach

**Component Design:**

- `ScoreChart` component at `frontend/components/history/score-chart.tsx`
- Props interface: `{ months: MonthHistory[] }` - data passed from parent
- Parent component handles fetching and loading states
- Component focuses solely on visualization

**Data Flow:**

1. Parent calls `getMonthsHistory(12)` via API client
2. API returns `HistoryResponse` with months array (chronological order)
3. Parent passes `months` to `ScoreChart`
4. Component transforms data to chart format with gap handling
5. Recharts renders LineChart with ReferenceAreas and custom Tooltip

**Integration Points:**

- New types added to `frontend/types/index.ts`: `MonthHistory`, `HistoryResponse`, `HistorySummary`, `ScoreTrend`
- New constant in `frontend/lib/utils.ts`: `SCORE_COLORS_HEX`
- New function in `frontend/lib/api-client.ts`: `getMonthsHistory()`
- Will be consumed by History Page UI (roadmap item #13)

## Out of Scope

- Period selector dropdown (fixed at 12 months)
- Click-to-navigate to month dashboard
- Animations or transitions
- Data export functionality
- Comparison between multiple metrics on same chart
- Mobile-specific layouts beyond basic responsiveness
- Caching or SWR integration (parent handles this if needed)
- Legend component (single line, self-explanatory)
- Y-axis label text (scale 0-3 is clear from context)
