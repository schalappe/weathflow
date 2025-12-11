# Score Evolution Chart

Build a line chart component showing Money Map score progression over time using Recharts.

## Overview

Enable users to visualize their budget adherence trends over multiple months through an interactive line chart.

## Related Use Case

**UC3: Suivi de l'evolution**

```text
En tant qu'utilisateur,
Je veux voir l'evolution de mon score sur plusieurs mois,
Afin d'identifier mes tendances et progres.
```

## Acceptance Criteria

- [ ] Display score evolution as a line chart
- [ ] Show data for the last N months (default: 12)
- [ ] X-axis: months (Jan, Feb, Mar...)
- [ ] Y-axis: score (0-3 scale)
- [ ] Visual indicators for score thresholds (Great/Okay/Need Improvement/Poor)

## Data Source

**Existing API:** `GET /api/months/history?months=12`

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

## UI Reference

```text
┌─────────────────────────────────────────────────────────┐
│  EVOLUTION DU SCORE (12 derniers mois)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  3 ─ ● ─ ─ ─ ● ─ ● ─ ─ ─ ─ ─ ● ─ ─ ─             │   │
│  │  2 ─ ─ ● ─ ─ ─ ─ ─ ● ─ ● ─ ─ ─ ─ ● ─ ●           │   │
│  │  1 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─           │   │
│  │  0 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─           │   │
│  │    J  F  M  A  M  J  J  A  S  O  N  D            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Technical Stack

| Technology | Purpose              |
| ---------- | -------------------- |
| Recharts   | Line chart rendering |
| Next.js    | React component      |
| TypeScript | Type safety          |

## Score Color Coding

| Score | Label            | Color   | Hex       |
| ----- | ---------------- | ------- | --------- |
| 3     | Great            | Green   | `#22c55e` |
| 2     | Okay             | Yellow  | `#eab308` |
| 1     | Need Improvement | Orange  | `#f97316` |
| 0     | Poor             | Red     | `#ef4444` |

## Component Location

```text
frontend/components/history/score-chart.tsx
```

## Dependencies

- Item #10 (Historical Data API) - **Completed**
- Item #13 (History Page UI) - Will consume this component

## Size Estimate

**S** (Small) - Single component, data endpoint already exists
