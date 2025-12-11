# Spec Requirements: History Page UI

## Initial Description

Combine evolution charts into a dedicated history page with period selector, providing users a unified view of their budget trends over time.

## Requirements Discussion

### First Round Questions

**Q1:** Page Location & Navigation - where should the history page be accessed?
**Answer:** New `/history` route accessible from the main navigation header (confirmed via feature doc).

**Q2:** Period Selector Options - what time ranges should be available?
**Answer:** Four preset options: 3 months, 6 months, 12 months (default), and All time (value 0).

**Q3:** Charts to Include - which charts and what layout?
**Answer:** Score Evolution Chart (line) and Spending Breakdown Chart (stacked bar). Vertically stacked on mobile, side-by-side on large screens.

**Q4:** Chart Interactivity - how should users interact with charts?
**Answer:** Tooltips on hover showing exact values. Drill-down into specific month is explicitly out of scope.

**Q5:** Summary Statistics - should stats accompany the charts?
**Answer:** No summary statistics. Charts only.

**Q6:** Empty State - how to handle users with insufficient data?
**Answer:** Display French message "Aucune donnee historique" with explanation and CTA button to import transactions.

**Q7:** Out of Scope items?
**Answer:** Advice panel (Feature #16), data export (Feature #18), drill-down into specific month from charts.

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Score Evolution Chart - Path: `frontend/components/history/score-chart.tsx` (Feature #11, completed)
- Feature: Spending Breakdown Chart - Path: `frontend/components/history/breakdown-chart.tsx` (Feature #12, completed)
- Backend: Historical Data API - Endpoint: `GET /api/months/history?months={period}` (Feature #10, completed)
- Components: shadcn/ui Select component for period selector

### Follow-up Questions

No follow-up questions needed - feature document is comprehensive.

## Visual Assets

### Files Provided

No visual files provided.

### Visual Reference

From PRD wireframe (section 7.1.3):

```txt
+---------------------------------------------------------------------+
|  Money Map Manager                        [Import] [History]        |
+---------------------------------------------------------------------+
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |  EVOLUTION DU SCORE (12 derniers mois)     [Period: 12 mois v]|  |
|  |  +----------------------------------------------------------+ |  |
|  |  |  3 - * - - - * - * - - - - - * - - -                     | |  |
|  |  |  2 - - * - - - - - * - * - - - - * - *                   | |  |
|  |  |  1 - - - - - - - - - - - - - - - - - -                   | |  |
|  |  |  0 - - - - - - - - - - - - - - - - - -                   | |  |
|  |  |    J  F  M  A  M  J  J  A  S  O  N  D                    | |  |
|  |  +----------------------------------------------------------+ |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |  REPARTITION PAR MOIS                                         |  |
|  |  +----------------------------------------------------------+ |  |
|  |  |  [Graphique en barres empilees]                          | |  |
|  |  |  Core | Choice | Compound                                | |  |
|  |  +----------------------------------------------------------+ |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
+---------------------------------------------------------------------+
```

When no historical data exists:

```txt
+---------------------------------------------------------------+
|                                                               |
|              Aucune donnee historique                         |
|                                                               |
|   Importez vos premieres transactions pour voir               |
|   l'evolution de votre budget.                                |
|                                                               |
|              [Importer des transactions]                      |
|                                                               |
+---------------------------------------------------------------+
```

ASCII wireframe from feature document (section 7.1.3 of PRD):

- Header with navigation showing [Import] [History] buttons
- Period selector dropdown in top-right of chart section
- Score evolution line chart (scores 0-3 on Y-axis, months on X-axis)
- Spending breakdown stacked bar chart below
- Responsive layout for mobile/desktop

## Requirements Summary

### Functional Requirements

- Create dedicated `/history` page route
- Implement period selector with 4 options (3, 6, 12 months, All time)
- Display Score Evolution Chart component (existing)
- Display Spending Breakdown Chart component (existing)
- Fetch data via existing `/api/months/history` endpoint
- Client-side data fetching with loading states
- Show empty state when no historical data exists
- Show error state with retry button on fetch failure
- Responsive layout (vertical mobile, side-by-side desktop)

### UI Components Required

- `PeriodSelector` - new component using shadcn/ui Select
- Page layout integrating existing chart components
- Empty state component with import CTA
- Loading skeleton during data fetch
- Error state with retry functionality

### Reusability Opportunities

- Existing `ScoreEvolutionChart` component (Feature #11)
- Existing `SpendingBreakdownChart` component (Feature #12)
- Existing Historical Data API endpoint
- shadcn/ui Select component for period selector
- Existing page layout patterns from dashboard

### Scope Boundaries

**In Scope:**

- New `/history` page with navigation
- Period selector component (3, 6, 12 months, All time)
- Integration of existing chart components
- Client-side data fetching with period parameter
- Loading, empty, and error states
- Responsive layout

**Out of Scope:**

- Advice panel integration (Feature #16)
- Data export from history page (Feature #18)
- Drill-down into specific month from charts
- Custom date range picker (start/end dates)
- Chart image export
- Caching of previous period data (nice-to-have, not required)

### Technical Considerations

- Use client-side fetching with `useEffect` to allow period changes without page reload
- French language for UI text (matching existing app)
- Follow existing component patterns from dashboard
- TypeScript interfaces already defined in feature doc
