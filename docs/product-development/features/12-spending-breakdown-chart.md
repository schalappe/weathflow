# Feature 12: Spending Breakdown Chart

## Overview

Create a stacked bar chart showing Core/Choice/Compound distribution month-over-month, enabling users to visualize their spending patterns and track budget allocation trends across multiple months.

**Size:** S (Small)
**Dependencies:** Feature #10 (Historical Data API)

## User Story

From UC3 - Suivi de l'evolution:

```txt
En tant qu'utilisateur,
Je veux voir l'evolution de mon score sur plusieurs mois,
Afin d'identifier mes tendances et progres.
```

### Acceptance Criteria (from PRD)

- [ ] Graphique d'evolution Core/Choice/Compound
- [ ] Comparaison mois par mois

## Technical Specifications

### Component Location

```txt
frontend/
  components/
    history/
      breakdown-chart.tsx    # Main chart component
```

### Data Source

Uses the existing Historical Data API endpoint:

```txt
GET /api/months/history?months=12
```

Response structure:

```json
{
  "months": [
    {
      "year": 2025,
      "month": 10,
      "score": 3,
      "core_percentage": 44.1,
      "choice_percentage": 24.0,
      "compound_percentage": 31.9
    }
  ]
}
```

### Technology

- **Chart Library:** Recharts (already in stack)
- **Chart Type:** Stacked Bar Chart (StackedBarChart or BarChart with stacked bars)

## UI Specifications

### Visual Design

From PRD wireframe (section 7.1.3):

```txt
┌─────────────────────────────────────────────────────────┐
│  REPARTITION PAR MOIS                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  [Graphique en barres empilees]                  │   │
│  │  Core | Choice | Compound                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Color Palette (from PRD Annexes)

| Category | Color   | Hex Code |
| -------- | ------- | -------- |
| Core     | Purple  | #8b5cf6  |
| Choice   | Amber   | #f59e0b  |
| Compound | Emerald | #10b981  |

### Chart Requirements

1. **X-Axis:** Month labels (e.g., "Jan", "Fev", "Mar")
2. **Y-Axis:** Percentage (0-100%)
3. **Bars:** Stacked showing Core, Choice, Compound proportions
4. **Legend:** Category names with color indicators
5. **Tooltip:** Show exact percentages on hover
6. **Responsive:** Adapt to container width

### Expected Behavior

- Display last N months (default: 12, configurable via period selector on History page)
- Each bar represents 100% of spending for that month
- Bars are stacked in order: Core (bottom), Choice (middle), Compound (top)
- Empty months should not be displayed

## Component API

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

## Integration

This component will be integrated into the History Page (Feature #13) alongside the Score Evolution Chart (Feature #11).

## Out of Scope

- Period selector (part of Feature #13 - History Page UI)
- Drill-down into specific month details
- Export chart as image
