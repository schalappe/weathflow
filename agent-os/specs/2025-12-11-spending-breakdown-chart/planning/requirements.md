# Spec Requirements: Spending Breakdown Chart

## Initial Description

Create a stacked bar chart showing Core/Choice/Compound distribution month-over-month `S`

## Source Documentation

Existing spec found at: `docs/product-development/features/12-spending-breakdown-chart.md`

## Requirements Discussion

### Pre-existing Specification

A detailed specification already exists in the codebase. The following requirements are extracted from that document.

**Q1:** Should the chart display absolute amounts or percentages?
**Answer:** Percentages stacked to 100% (Y-axis: 0-100%)

**Q2:** How many months should be displayed by default?
**Answer:** 12 months (configurable via period selector on History page, which is Feature #13)

**Q3:** Which categories should be included?
**Answer:** Core, Choice, and Compound only (INCOME and EXCLUDED are not part of spending breakdown)

**Q4:** What colors should be used?
**Answer:** From PRD Annexes:

- Core: Purple (#8b5cf6)
- Choice: Amber (#f59e0b)
- Compound: Emerald (#10b981)

**Q5:** How should axes be labeled?
**Answer:** X-axis: Month names (Jan, Feb, Mar...), Y-axis: Percentage (0-100%)

**Q6:** Should tooltips be included?
**Answer:** Yes, show exact percentages on hover

**Q7:** What about empty months?
**Answer:** Empty months should not be displayed

**Q8:** What is explicitly out of scope?
**Answer:**

- Period selector (part of Feature #13 - History Page UI)
- Drill-down into specific month details
- Export chart as image

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Score Evolution Chart - Path: `frontend/components/history/score-chart.tsx`
- Feature: Spending Pie Chart - Path: `frontend/components/dashboard/spending-pie-chart.tsx`
- Components to potentially reuse: Recharts setup, color constants, responsive container patterns
- Backend logic to reference: Historical Data API (`GET /api/months/history?months=12`)

### Follow-up Questions

None required - existing spec is comprehensive.

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

ASCII wireframe included in spec document:

```txt
┌─────────────────────────────────────────────────────────┐
│  REPARTITION PAR MOIS                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  [Graphique en barres empilees]                  │   │
│  │  Core | Choice | Compound                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Requirements Summary

### Functional Requirements

- Display stacked bar chart showing Core/Choice/Compound percentages
- Show last 12 months of data (from Historical Data API)
- Each bar represents 100% of spending for that month
- Bars stacked in order: Core (bottom), Choice (middle), Compound (top)
- Include legend with category names and color indicators
- Show tooltips with exact percentages on hover
- Responsive design adapting to container width
- Skip months with no data

### Reusability Opportunities

- Score Evolution Chart (`frontend/components/history/score-chart.tsx`) - same Recharts setup, history folder location
- Spending Pie Chart (`frontend/components/dashboard/spending-pie-chart.tsx`) - color constants, category styling
- Historical Data API already exists and returns required data structure

### Scope Boundaries

**In Scope:**

- Stacked bar chart component
- Core/Choice/Compound percentage visualization
- Month labels on X-axis
- Percentage scale on Y-axis (0-100%)
- Legend display
- Hover tooltips
- Responsive layout

**Out of Scope:**

- Period selector (Feature #13)
- Drill-down to transactions
- Export as image
- Animation customization

### Technical Considerations

- Component location: `frontend/components/history/breakdown-chart.tsx`
- Uses existing Historical Data API: `GET /api/months/history?months=12`
- Chart library: Recharts (already in stack)
- Must follow existing component API pattern with `data` and `className` props

### Component API (from spec)

```typescript
interface SpendingBreakdownChartProps {
  data: MonthHistory[];
  className?: string;
}

interface MonthHistory {
  year: number;
  month: number;
  core_percentage: number;
  choice_percentage: number;
  compound_percentage: number;
}
```

### Integration Notes

This component will be integrated into the History Page (Feature #13) alongside the Score Evolution Chart (Feature #11).
