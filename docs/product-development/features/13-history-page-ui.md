# Feature 13: History Page UI

## Overview

Combine evolution charts into a dedicated history page with period selector, providing users a unified view of their budget trends over time.

**Size:** M (Medium)
**Dependencies:** Feature #11 (Score Evolution Chart), Feature #12 (Spending Breakdown Chart)

## User Story

From UC3 - Suivi de l'evolution:

```txt
En tant qu'utilisateur,
Je veux voir l'evolution de mon score sur plusieurs mois,
Afin d'identifier mes tendances et progres.
```

### Acceptance Criteria (from PRD)

- [ ] Graphique d'evolution du score
- [ ] Graphique d'evolution Core/Choice/Compound
- [ ] Comparaison mois par mois
- [ ] Period selector to choose time range

## Technical Specifications

### Page Location

```txt
frontend/
  app/
    history/
      page.tsx           # History page (server component)
  components/
    history/
      score-chart.tsx        # Feature #11 (existing)
      breakdown-chart.tsx    # Feature #12 (existing)
      period-selector.tsx    # New: period selection component
```

### Data Source

Uses the existing Historical Data API endpoint:

```txt
GET /api/months/history?months={period}
```

Where `period` is controlled by the period selector (default: 12).

Response structure:

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

## UI Specifications

### Visual Design

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

### Period Selector Options

| Option       | Value | Description                |
| ------------ | ----- | -------------------------- |
| 3 months     | 3     | Last quarter               |
| 6 months     | 6     | Last semester              |
| 12 months    | 12    | Last year (default)        |
| All time     | 0     | All available data         |

### Page Layout

1. **Header:** Page title with navigation breadcrumb
2. **Period Selector:** Dropdown in top-right corner of chart section
3. **Score Evolution Chart:** Line chart showing score trend (Feature #11)
4. **Spending Breakdown Chart:** Stacked bar chart showing category distribution (Feature #12)
5. **Responsive Design:** Stack charts vertically on mobile, side-by-side on large screens

## Component API

### Period Selector

```typescript
interface PeriodSelectorProps {
  value: number;
  onChange: (months: number) => void;
  className?: string;
}

// Options
const PERIOD_OPTIONS = [
  { label: '3 mois', value: 3 },
  { label: '6 mois', value: 6 },
  { label: '12 mois', value: 12 },
  { label: 'Tout', value: 0 },
];
```

### Page State

```typescript
interface HistoryPageState {
  period: number;           // Selected period (default: 12)
  data: MonthHistory[];     // Fetched history data
  isLoading: boolean;       // Loading state
  error: string | null;     // Error message
}
```

## Implementation Notes

### Data Fetching Strategy

- Use client-side fetching with `useEffect` to allow period changes without full page reload
- Show loading skeleton while fetching
- Cache previous period data to avoid re-fetching on period switch back

### Empty State

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

### Error State

Display user-friendly error message with retry button.

## Technology Stack

| Technology | Purpose                     |
| ---------- | --------------------------- |
| Next.js    | Page routing and rendering  |
| Recharts   | Chart components            |
| shadcn/ui  | Period selector (Select)    |
| TypeScript | Type safety                 |

## Integration

This page integrates:

- Score Evolution Chart (Feature #11) - **Completed**
- Spending Breakdown Chart (Feature #12) - **Completed**
- Navigation from main layout header

## Out of Scope

- Advice panel (Feature #16 - separate implementation)
- Data export from this page (Feature #18)
- Drill-down into specific month from charts
