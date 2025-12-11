# Spec Requirements: Score Evolution Chart

## Initial Description

Build a line chart component showing score progression over time using Recharts.

## Requirements Discussion

### First Round Questions

**Q1:** I assume the chart should show the Money Map score (0-3) on the Y-axis and months on the X-axis. Is that correct?
**Answer:** Confirmed by documentation - X-axis: months (Jan, Feb, Mar...), Y-axis: score (0-3 scale)

**Q2:** I'm thinking we should display the last 12 months of data by default. Should we allow users to select different time ranges?
**Answer:** Confirmed by documentation - Last N months (default: 12). No period selector mentioned.

**Q3:** I assume the chart should include visual indicators for score thresholds. Is that correct?
**Answer:** Confirmed by documentation - Visual indicators for score thresholds with specific colors:

- Score 3 (Great): Green `#22c55e`
- Score 2 (Okay): Yellow `#eab308`
- Score 1 (Need Improvement): Orange `#f97316`
- Score 0 (Poor): Red `#ef4444`

**Q4:** For months with no data, should we show gaps in the line or zeros?
**Answer:** Show gaps in the line.

**Q5:** Should hovering on a data point show a tooltip with details?
**Answer:** Yes, show a tooltip with details (month name, exact score, score label).

**Q6:** Where will this component be used?
**Answer:** Will be consumed by History Page UI (roadmap item #13). Component location: `frontend/components/history/score-chart.tsx`

**Q7:** Any explicit exclusions?
**Answer:** Nothing excluded.

### Existing Code to Reference

**Similar Features Identified:**

- Feature: SpendingPieChart - Path: `frontend/components/dashboard/spending-pie-chart.tsx`
- Patterns to reuse:
  - Recharts library usage (ResponsiveContainer, Tooltip)
  - shadcn/ui Card wrapper pattern
  - Empty state handling
  - TypeScript interface for props
  - `'use client'` directive

**Backend:**

- Existing API: `GET /api/months/history?months=12` - already completed (roadmap item #10)

### Follow-up Questions

None needed - documentation was comprehensive.

## Visual Assets

### Files Provided

- `wireframe-score.md`: ASCII wireframe showing chart layout

### Visual Insights

- Title: "EVOLUTION DU SCORE (12 derniers mois)"
- Chart area with Y-axis showing scores 0-3
- X-axis showing month abbreviations (J F M A M J J A S O N D)
- Line connecting data points at various score levels
- Contained within a card/box component
- Fidelity level: Low-fidelity ASCII wireframe

## Requirements Summary

### Functional Requirement

- Display Money Map score (0-3) evolution as a line chart
- X-axis: months (abbreviated format: Jan, Feb, Mar...)
- Y-axis: score scale 0-3
- Show last 12 months of data by default
- Visual indicators for score thresholds (colored zones or reference lines)
- Tooltip on hover showing: month name, exact score, score label
- Handle missing months with gaps in the line (not zeros)
- Empty state when no data available

### Data Source

- API: `GET /api/months/history?months=12`
- Response structure:

```json
{
  "months": [
    {
      "year": 2025,
      "month": 10,
      "score": 3,
      "score_label": "Great",
      "core_percentage": 44.1,
      "choice_percentage": 24.0,
      "compound_percentage": 31.9
    }
  ]
}
```

### Score Color Coding

| Score | Label            | Color  | Hex       |
| ----- | ---------------- | ------ | --------- |
| 3     | Great            | Green  | `#22c55e` |
| 2     | Okay             | Yellow | `#eab308` |
| 1     | Need Improvement | Orange | `#f97316` |
| 0     | Poor             | Red    | `#ef4444` |

### Reusability Opportunities

- Recharts patterns from `spending-pie-chart.tsx`
- Card component wrapper from shadcn/ui
- ResponsiveContainer for responsive sizing
- Tooltip component from Recharts
- Empty state pattern

### Scope Boundaries

**In Scope:**

- Line chart component showing score evolution
- 12 months of historical data
- Visual score threshold indicators
- Hover tooltip with month details
- Empty state handling
- Responsive design

**Out of Scope:**

- Period selector dropdown
- Click-to-navigate to month dashboard
- Animations
- Data export
- Comparison between multiple metrics
- Mobile-specific layouts (beyond basic responsiveness)

### Technical Considerations

- Component location: `frontend/components/history/score-chart.tsx`
- Uses Recharts library (already in project via pie chart)
- TypeScript with proper interface
- Client component (`'use client'`)
- Will be consumed by History Page (roadmap item #13)
