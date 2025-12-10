# Spec Requirements: Monthly Dashboard UI

## Initial Description

> **#8**: Monthly Dashboard UI — Create the main dashboard showing score card, Core/Choice/Compound metric cards with percentage indicators, pie chart breakdown, and transaction table `L`

## Requirements Discussion

### Source Document

Requirements gathered from comprehensive PRD: `docs/product-development/features/08-monthly-dashboard-ui.md`

### First Round Questions

**Q1:** Score Card Display - visual indicator and color-coding?
**Answer:** PRD specifies score card with color code (Great=green, Okay=yellow, Need Improvement=orange, Poor=red) and label display.

**Q2:** Month Selection - dropdown or navigation?
**Answer:** PRD specifies MonthSelector component as "Dropdown/navigation to select month" defaulting to most recent.

**Q3:** Metric Cards Layout - what elements to include?
**Answer:** PRD specifies: Category name, Amount (€), Percentage vs income, Success/Warning indicator (✓/✗). Four cards: Income, Core, Choice, Compound.

**Q4:** Pie Chart Details - amounts on hover?
**Answer:** PRD shows pie chart for Core/Choice/Compound distribution. States: Loading, Loaded, Empty.

**Q5:** Transaction Table - pagination style?
**Answer:** PRD specifies paginated table with columns: Date, Description, Amount, Category. Shows "[Page 1/5]" format.

**Q6:** Empty State handling?
**Answer:** PRD specifies: "Show empty state with CTA to import" when no months imported.

**Q7:** Out of Scope items?
**Answer:** PRD explicitly excludes:

- Transaction filtering by category/date/search (Item #17)
- Inline transaction editing/correction (Item #9)
- Score evolution chart (Item #11)
- Advice panel (Item #16)

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Import Page UI - Path: `frontend/components/import/`
- API Client: `frontend/lib/api-client.ts`
- Types: `frontend/types/index.ts`

User requested code exploration to discover patterns.

### Follow-up Questions

**Follow-up 1:** Reference existing patterns from Import Page?
**Answer:** User said "explore" - proceed with code exploration.

## Visual Assets

### Files Provided

- `wireframe-monthly-dashboard-ui.md`: ASCII wireframe showing page layout

### Visual Insights

- Header with app name and navigation links (Import, History)
- Score card banner at top: "OCTOBRE 2025 - SCORE: 2/3 (Okay)"
- 4 metric cards in grid layout (Income, Core, Choice, Compound)
- Pie chart positioned next to Compound card
- Transaction table at bottom with pagination
- Fidelity level: Low-fidelity ASCII wireframe

## Requirements Summary

### Functional Requirements

From PRD Acceptance Criteria:

- Display month selector to navigate between imported months
- Show totals for Income, Core, Choice, Compound
- Display percentages vs income for Core, Choice, Compound
- Calculate and display score (0-3) with visual indicator
- Display score label (Great/Okay/Need Improvement/Poor)
- Show success/warning indicators on metric cards based on thresholds
- Render pie chart showing Core/Choice/Compound distribution
- Display paginated transaction table with basic columns
- Handle empty state when no months are imported
- Handle loading states during data fetching
- Handle error states gracefully

### Business Rules

**Money Map Thresholds:**

| Category | Target | Condition for Success     |
| -------- | ------ | ------------------------- |
| Core     | ≤ 50%  | core_percentage <= 50     |
| Choice   | ≤ 30%  | choice_percentage <= 30   |
| Compound | ≥ 20%  | compound_percentage >= 20 |

**Score Calculation:**

- Score 3 (Great): All 3 thresholds met
- Score 2 (Okay): 2 thresholds met
- Score 1 (Need Improvement): 1 threshold met
- Score 0 (Poor): No thresholds met

### Color Palette

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

### Components to Build

| Component        | Description                                     | States                                                              |
| ---------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| ScoreCard        | Displays score with color code and label        | Great (green), Okay (yellow), Need Improvement (orange), Poor (red) |
| MetricCard       | Displays a metric (Income/Core/Choice/Compound) | Normal, Warning (>threshold), Success (≤threshold)                  |
| SpendingPieChart | Pie chart showing Core/Choice/Compound          | Loading, Loaded, Empty                                              |
| TransactionTable | Paginated table of transactions                 | Loading, Loaded, Empty                                              |
| MonthSelector    | Dropdown/navigation to select month             | Default                                                             |

### File Structure (from PRD)

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

### API Endpoints (Already Implemented)

- **GET** `/api/months` - Returns list of all imported months
- **GET** `/api/months/{year}/{month}` - Returns month detail with transactions

### Edge Cases

| Case                      | Behavior                                    |
| ------------------------- | ------------------------------------------- |
| No months imported        | Show empty state with CTA to import         |
| Month has 0 income        | Show percentages as 0%, score as 0          |
| Month has no transactions | Show month summary, empty transaction table |
| API error                 | Show error alert with retry option          |
| Network offline           | Show connection error message               |

### Reusability Opportunities

To be discovered via code exploration:

- Components from Import Page UI
- API client patterns
- Table components
- Loading/error state patterns
- Card layouts

### Scope Boundaries

**In Scope:**

- Dashboard page at `/` route
- Month selector navigation
- Score card with color coding
- 4 metric cards with success/warning states
- Pie chart (Core/Choice/Compound)
- Paginated transaction table
- Empty/loading/error states
- Responsive layout (desktop-first)

**Out of Scope:**

- Transaction filtering by category/date/search (Item #17)
- Inline transaction editing/correction (Item #9)
- Score evolution chart (Item #11)
- Advice panel (Item #16)
- Mobile-optimized layout (basic support only)

### Technical Considerations

- Use Recharts for pie chart
- Use shadcn/ui components: Card, Table, Select, Badge
- TypeScript types must match backend response schema
- API client extensions needed for getMonthsList and getMonthDetail

### Definition of Done

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
