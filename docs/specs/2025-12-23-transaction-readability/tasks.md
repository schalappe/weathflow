# Task Breakdown: Transaction Readability Enhancement

## Overview

Total Task Groups: 4
Total Tasks: 16
Estimated Duration: 3-4 hours

This is a **frontend-only** feature. No backend changes required.

## Task List

### Utilities Layer

#### Task Group 1: Transaction Grouping Utilities

**Dependencies:** None

- [x] 1.0 Complete transaction grouping utilities
  - [x] 1.1 Write 4-6 unit tests for grouping logic
    - Test splitting transactions by amount sign (positive/negative)
    - Test grouping by subcategory
    - Test handling null/empty subcategories as "Autre"
    - Test percentage calculation
    - Test sorting by total amount descending
  - [x] 1.2 Create `frontend/lib/transaction-grouping.ts` with types and functions
    - Define `SubcategoryGroup` interface
    - Define `GroupedTransactions` interface
    - Implement `groupTransactionsBySubcategory()` function
    - Implement `calculatePercentage()` helper
  - [x] 1.3 Add subcategory icon mapping
    - Create `SUBCATEGORY_ICONS` mapping (subcategory name → lucide icon)
    - Include fallback icon for unknown subcategories
  - [x] 1.4 Ensure tests pass (run only grouping tests)

**Acceptance Criteria:**

- All grouping tests pass
- Transactions correctly split by amount sign
- Null subcategories mapped to "Autre"
- Percentages calculated with 1 decimal place

**Files to create/modify:**

- `frontend/lib/transaction-grouping.ts` (new)
- `frontend/__tests__/lib/transaction-grouping.test.ts` (new)

---

### Translations Layer

#### Task Group 2: French Translations

**Dependencies:** None (can run in parallel with Task Group 1)

- [x] 2.0 Complete translation updates
  - [x] 2.1 Add tab labels to `frontend/lib/translations.ts`
    - `transactions.tabs.inputs` = "Entrées"
    - `transactions.tabs.outputs` = "Sorties"
    - `transactions.other` = "Autre"
    - `transactions.transactionCount` = "transaction"
    - `transactions.transactionsCount` = "transactions"

**Acceptance Criteria:**

- All new translation keys accessible via `t` object
- No TypeScript errors

**Files to modify:**

- `frontend/lib/translations.ts`

---

### Components Layer

#### Task Group 3: Grouped Transaction List Component

**Dependencies:** Task Groups 1, 2

- [x] 3.0 Complete GroupedTransactionList component
  - [x] 3.1 Write 4-6 component tests
    - Test tab rendering with correct counts
    - Test subcategory grouping display
    - Test expand/collapse toggle behavior
    - Test transaction click triggers callback
    - Test empty state per tab
  - [x] 3.2 Create `TransactionRow` internal component
    - Render date (DD/MM format), description, amount
    - Handle click to trigger `onTransactionClick`
    - Show pencil icon for manually corrected transactions
    - Apply hover styling for clickable row
  - [x] 3.3 Create `SubcategoryGroup` internal component
    - Render subcategory header row with all elements:
      - Chevron icon (rotates on expand)
      - Category icon (from mapping)
      - Subcategory name (translated)
      - Percentage badge
      - Transaction count
      - Money Map type badge
      - Total amount
    - Handle click to toggle expand/collapse
    - Render `TransactionRow` list when expanded
    - Apply indentation for expanded transactions
  - [x] 3.4 Create `GroupedTransactionList` main component
    - Accept props: `transactions`, `onTransactionClick`, `isLoading`, `totalIncome`, `totalExpenses`
    - Use `useMemo` to group transactions
    - Render Card with Tabs (default to "outputs")
    - Show tab counts in triggers
    - Map subcategory groups per tab
    - Manage expand/collapse state with `useState<Set<string>>`
  - [x] 3.5 Ensure component tests pass

**Acceptance Criteria:**

- Tabs switch between inputs/outputs correctly
- Subcategories sorted by amount descending
- Expand/collapse works independently per subcategory
- Transaction click opens edit modal (callback fired)
- Loading state disables interactions

**Files to create:**

- `frontend/components/dashboard/grouped-transaction-list.tsx` (new)
- `frontend/__tests__/dashboard/grouped-transaction-list.test.tsx` (new)

---

### Integration Layer

#### Task Group 4: Dashboard Integration

**Dependencies:** Task Group 3

- [x] 4.0 Complete dashboard integration
  - [x] 4.1 Modify `dashboard-client.tsx` to use new component
    - Import `GroupedTransactionList`
    - Replace `TransactionTable` with `GroupedTransactionList`
    - Pass required props: `transactions`, `onTransactionClick`, `isLoading`
    - Calculate and pass `totalIncome` from `monthDetail.month.total_income`
    - Calculate and pass `totalExpenses` from month stats
  - [x] 4.2 Remove unused pagination/filter props
    - Remove `pagination` prop passing
    - Remove `onPageChange` handler (no longer needed)
    - Keep `TransactionFilters` import for potential future use (do not delete)
  - [x] 4.3 Manual integration testing
    - Verify tabs display correct transaction counts
    - Verify subcategories expand/collapse
    - Verify edit modal opens on transaction click
    - Verify data refreshes after transaction edit
    - Verify EXCLUDED transactions appear correctly
  - [x] 4.4 Run existing dashboard tests to verify no regression

**Acceptance Criteria:**

- Dashboard renders with new grouped view
- Edit flow works end-to-end (click → modal → save → refresh)
- No console errors or TypeScript warnings
- Existing dashboard tests still pass

**Files to modify:**

- `frontend/components/dashboard/dashboard-client.tsx`

---

## Execution Order

```text
┌─────────────────────────────────┐
│ Task Group 1: Grouping Utils    │──┐
└─────────────────────────────────┘  │
                                     ├──→ Task Group 3: Component
┌─────────────────────────────────┐  │     │
│ Task Group 2: Translations      │──┘     │
└─────────────────────────────────┘        ↓
                                     Task Group 4: Integration
```

**Parallel execution possible:** Task Groups 1 and 2 can run simultaneously.

## Test Summary

| Task Group | Tests Written | Tests Run   |
| ---------- | ------------- | ----------- |
| 1          | 4-6           | 4-6         |
| 2          | 0             | 0           |
| 3          | 4-6           | 4-6         |
| 4          | 0             | Existing    |
| **Total**  | **8-12**      | **8-12+**   |

## Notes

- **No backend changes** — all grouping done client-side
- **Preserve edit modal** — reuse existing `TransactionEditModal` as-is
- **Performance** — use `useMemo` to avoid recalculating groups on every render
- **Icon mapping** — use lucide-react icons already available in project
