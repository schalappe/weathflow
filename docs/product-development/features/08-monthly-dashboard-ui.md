# Monthly Dashboard UI - Product Requirements Document

## 1. Overview

### 1.1 Roadmap Item

> **#8**: Monthly Dashboard UI — Create the main dashboard showing score card, Core/Choice/Compound metric cards with percentage indicators, pie chart breakdown, and transaction table `L`

### 1.2 Purpose

The Monthly Dashboard is the main landing page of Money Map Manager. It provides users with an at-a-glance view of their financial health for a selected month, displaying:

- The overall Money Map score (0-3)
- Income and spending breakdown by category (Core/Choice/Compound)
- Visual representation via pie chart
- Detailed transaction list with filtering

### 1.3 User Story (UC2)

```txt
En tant qu'utilisateur,
Je veux voir mon score Money Map du mois,
Afin de savoir si je respecte mes objectifs budgétaires.
```

---

## 2. Acceptance Criteria

- [ ] Display month selector to navigate between imported months
- [ ] Show totals for Income, Core, Choice, Compound
- [ ] Display percentages vs income for Core, Choice, Compound
- [ ] Calculate and display score (0-3) with visual indicator
- [ ] Display score label (Great/Okay/Need Improvement/Poor)
- [ ] Show success/warning indicators on metric cards based on thresholds
- [ ] Render pie chart showing Core/Choice/Compound distribution
- [ ] Display paginated transaction table with basic columns
- [ ] Handle empty state when no months are imported
- [ ] Handle loading states during data fetching
- [ ] Handle error states gracefully

---

## 3. UI Specification

### 3.1 Page Layout (Wireframe)

```txt
┌────────────────────────────────────────────────────────────────┐
│  Money Map Manager                        [Import] [History]   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           OCTOBRE 2025 - SCORE: 2/3 (Okay)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │    INCOME     │ │     CORE      │ │    CHOICE     │         │
│  │   €2,823.29   │ │   €1,245.00   │ │    €678.50    │         │
│  │               │ │     44.1%     │ │     24.0%     │         │
│  │               │ │      ✓        │ │       ✓       │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                │
│  ┌───────────────┐                                             │
│  │   COMPOUND    │     ┌─────────────────────────────────┐     │
│  │    €899.79    │     │   [Graphique camembert]         │     │
│  │     31.9%     │     │   Core / Choice / Compound      │     │
│  │      ✓        │     └─────────────────────────────────┘     │
│  └───────────────┘                                             │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ TRANSACTIONS                                 [Page 1/5] │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Date       Description          Montant    Catégorie    │   │
│  │ 29/10     CB Domoro             -2.50€     CHOICE       │   │
│  │ 29/10     Virement Salaire    +2823.29€    INCOME       │   │
│  │ ...                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Components

| Component        | Description                                     | States                                                              |
| ---------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| ScoreCard        | Displays score with color code and label        | Great (green), Okay (yellow), Need Improvement (orange), Poor (red) |
| MetricCard       | Displays a metric (Income/Core/Choice/Compound) | Normal, Warning (>threshold), Success (≤threshold)                  |
| SpendingPieChart | Pie chart showing Core/Choice/Compound          | Loading, Loaded, Empty                                              |
| TransactionTable | Paginated table of transactions                 | Loading, Loaded, Empty                                              |
| MonthSelector    | Dropdown/navigation to select month             | Default                                                             |

### 3.3 Color Palette

```css
/* Score Labels */
--score-great: #22c55e;        /* Green - Tailwind green-500 */
--score-okay: #eab308;         /* Yellow - Tailwind yellow-500 */
--score-improvement: #f97316;  /* Orange - Tailwind orange-500 */
--score-poor: #ef4444;         /* Red - Tailwind red-500 */

/* Categories */
--category-income: #3b82f6;    /* Blue - Tailwind blue-500 */
--category-core: #8b5cf6;      /* Purple - Tailwind violet-500 */
--category-choice: #f59e0b;    /* Amber - Tailwind amber-500 */
--category-compound: #10b981;  /* Emerald - Tailwind emerald-500 */
--category-excluded: #6b7280;  /* Gray - Tailwind gray-500 */
```

---

## 4. Data Requirements

### 4.1 API Endpoint

**GET** `/api/months/{year}/{month}`

Already implemented in `backend/app/routers/months.py`.

### 4.2 Response Schema

```typescript
interface MonthSummary {
  id: number;
  year: number;
  month: number;
  total_income: number;
  total_core: number;
  total_choice: number;
  total_compound: number;
  core_percentage: number;      // 0-100
  choice_percentage: number;    // 0-100
  compound_percentage: number;  // 0-100
  score: number;                // 0-3
  score_label: "Poor" | "Need Improvement" | "Okay" | "Great" | null;
  transaction_count: number;
  created_at: string;
  updated_at: string;
}

interface TransactionResponse {
  id: number;
  date: string;
  description: string;
  account: string | null;
  amount: number;
  bankin_category: string | null;
  bankin_subcategory: string | null;
  money_map_type: "INCOME" | "CORE" | "CHOICE" | "COMPOUND" | "EXCLUDED" | null;
  money_map_subcategory: string | null;
  is_manually_corrected: boolean;
}

interface PaginationInfo {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

interface MonthDetailResponse {
  month: MonthSummary;
  transactions: TransactionResponse[];
  pagination: PaginationInfo;
}
```

### 4.3 API for Month List

**GET** `/api/months`

Returns list of all imported months for the month selector.

```typescript
interface MonthsListResponse {
  months: MonthSummary[];
  total: number;
}
```

---

## 5. Business Rules

### 5.1 Money Map Thresholds

| Category | Target | Condition for Success       |
| -------- | ------ | --------------------------- |
| Core     | ≤ 50%  | `core_percentage <= 50`     |
| Choice   | ≤ 30%  | `choice_percentage <= 30`   |
| Compound | ≥ 20%  | `compound_percentage >= 20` |

### 5.2 Score Calculation

- Score 3 (Great): All 3 thresholds met
- Score 2 (Okay): 2 thresholds met
- Score 1 (Need Improvement): 1 threshold met
- Score 0 (Poor): No thresholds met

### 5.3 Metric Card Indicators

- **Success** (✓ green): Threshold is met
- **Warning** (✗ red): Threshold is exceeded

---

## 6. Technical Implementation

### 6.1 File Structure

```txt
frontend/
├── app/
│   └── page.tsx                    # Dashboard page (server component wrapper)
├── components/
│   └── dashboard/
│       ├── dashboard-client.tsx    # Client component with state
│       ├── score-card.tsx          # Score display with label
│       ├── metric-card.tsx         # Individual metric (Income/Core/Choice/Compound)
│       ├── spending-pie-chart.tsx  # Recharts pie chart
│       ├── transaction-table.tsx   # Paginated table
│       └── month-selector.tsx      # Month navigation dropdown
├── lib/
│   └── api-client.ts               # Add getMonthDetail, getMonthsList
└── types/
    └── index.ts                    # Add dashboard types
```

### 6.2 Dependencies

- **Recharts**: For pie chart (`bun add recharts`)
- **shadcn/ui**: Card, Table, Select, Badge components

### 6.3 API Client Extensions

Add to `frontend/lib/api-client.ts`:

```typescript
export async function getMonthsList(): Promise<MonthsListResponse>;
export async function getMonthDetail(
  year: number,
  month: number,
  page?: number,
  pageSize?: number
): Promise<MonthDetailResponse>;
```

---

## 7. Edge Cases

| Case                      | Behavior                                    |
| ------------------------- | ------------------------------------------- |
| No months imported        | Show empty state with CTA to import         |
| Month has 0 income        | Show percentages as 0%, score as 0          |
| Month has no transactions | Show month summary, empty transaction table |
| API error                 | Show error alert with retry option          |
| Network offline           | Show connection error message               |

---

## 8. Out of Scope (Handled by Future Items)

- Transaction filtering by category/date/search (Item #17)
- Inline transaction editing/correction (Item #9)
- Score evolution chart (Item #11)
- Advice panel (Item #16)

---

## 9. Definition of Done

- [ ] Dashboard page renders at `/` route
- [ ] Month selector allows navigation between imported months
- [ ] Score card displays with correct color based on score
- [ ] All 4 metric cards display with correct success/warning states
- [ ] Pie chart renders Core/Choice/Compound distribution
- [ ] Transaction table displays with pagination
- [ ] Empty state shown when no data exists
- [ ] Loading states shown during API calls
- [ ] Error handling with user-friendly messages
- [ ] Responsive layout (desktop-first, basic mobile support)
- [ ] TypeScript types match backend response schema
