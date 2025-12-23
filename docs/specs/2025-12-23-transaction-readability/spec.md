# Specification: Transaction Readability Enhancement

## Goal

Replace the flat transaction list on the dashboard with a grouped, tab-based view that separates inputs (positive amounts) from outputs (negative amounts), grouping transactions by subcategory for improved readability and faster comprehension of spending patterns.

## User Stories

- As a budget-conscious user, I want to see my transactions grouped by subcategory so that I can quickly understand where my money is going without scrolling through a long list.
- As a user reviewing my monthly finances, I want to switch between income and expenses tabs so that I can focus on one flow at a time.
- As a user who spots a miscategorized transaction, I want to expand a subcategory and click on the transaction to edit it, preserving my current workflow.

## Specific Requirements

**Tab-based Layout:**

- Single Card component containing two tabs: "Entrées" (Inputs) and "Sorties" (Outputs)
- Inputs tab: all transactions with `amount >= 0`
- Outputs tab: all transactions with `amount < 0`
- Show transaction count in each tab trigger (e.g., "Entrées (3)")
- Default to "Sorties" tab (users typically review expenses more often)

**Subcategory Grouping:**

- Group transactions by `money_map_subcategory` field
- Null or empty subcategories displayed as "Autre" (Other)
- Each subcategory row displays (left to right):
  - Chevron icon (rotates 90° when expanded)
  - Category icon (mapped to subcategory name)
  - Subcategory name (translated to French)
  - Percentage badge (e.g., "32.5%")
  - Transaction count (e.g., "3 transactions")
  - Money Map type badge (CORE/CHOICE/COMPOUND/EXCLUDED with existing color scheme)
  - Total amount (right-aligned, formatted as currency)
- Sort subcategories by total amount descending (largest first)

**Expandable Subcategory Rows:**

- Click anywhere on subcategory row to toggle expand/collapse
- Expanded state managed locally via `useState<Set<string>>`
- Key format: `${tabName}-${subcategory}` for uniqueness
- Expanded view shows individual transactions in minimal format
- Transaction row: date (DD/MM) | description | amount
- Indent transaction rows visually under parent subcategory

**Edit Capability (Non-regression):**

- Click on transaction row opens existing `TransactionEditModal`
- Preserve exact callback signature: `onTransactionClick(transaction: TransactionResponse)`
- After save, component re-renders with updated groupings automatically
- Manually corrected transactions show pencil icon (existing behavior)

**EXCLUDED Transactions Handling:**

- EXCLUDED type transactions appear in their own "Excluded" subcategory
- Placed in Inputs or Outputs tab based on amount sign
- Use gray badge styling (existing `CATEGORY_BADGE_CLASSES.EXCLUDED`)

**Percentage Calculation:**

- Outputs: `|subcategoryTotal| / totalExpenses * 100`
- Inputs: `subcategoryTotal / totalIncome * 100`
- Display with 1 decimal place (e.g., "32.5%")
- Use `totalIncome` and `totalExpenses` from parent component props

## Existing Code to Leverage

**TransactionEditModal — `frontend/components/dashboard/transaction-edit-modal.tsx`**

- What it does: Modal dialog for editing transaction category and subcategory
- How to reuse: Import and keep existing integration via `onTransactionClick` callback
- Key props: `transaction`, `isOpen`, `onClose`, `onSave`, `isSaving`, `error`

**DashboardClient Reducer — `frontend/components/dashboard/dashboard-client.tsx`**

- What it does: Manages dashboard state including edit modal open/close
- How to reuse: Continue dispatching `OPEN_EDIT_MODAL` action when transaction clicked
- Key actions: `OPEN_EDIT_MODAL`, `CLOSE_EDIT_MODAL`, `TRANSACTION_UPDATED`

**Category Badge Styling — `frontend/lib/utils.ts`**

- What it does: Maps MoneyMapType to Tailwind color classes
- How to reuse: Import `CATEGORY_BADGE_CLASSES` for badge styling
- Key mapping: `CORE: "bg-[#d97757] text-white"`, etc.

**Translations — `frontend/lib/translations.ts`**

- What it does: Centralizes French translations including subcategory names
- How to reuse: Import `t` object, extend with new tab labels
- Key additions needed: `transactions.tabs.inputs`, `transactions.tabs.outputs`, `transactions.other`

**shadcn Components — `frontend/components/ui/`**

- Tabs: Use for Inputs/Outputs layout (`tabs.tsx`)
- Badge: Use for percentage and Money Map type display (`badge.tsx`)
- Card: Use as container (`card.tsx`)

## Architecture Approach

**Component Design:**

| Component                     | Responsibility                                          |
| ----------------------------- | ------------------------------------------------------- |
| `GroupedTransactionList`      | Main component: tabs, grouping logic, expand state      |
| `SubcategoryGroup` (internal) | Single subcategory row with toggle and transactions     |
| `TransactionRow` (internal)   | Minimal transaction display (date, description, amount) |
| `transaction-grouping.ts`     | Pure utility functions for grouping and calculations    |

**Data Flow:**

```text
DashboardClient (fetches MonthDetailResponse)
    ↓ transactions[], totalIncome, totalExpenses
GroupedTransactionList
    ↓ useMemo → groupTransactionsBySubcategory()
    ↓ splits by amount sign, groups by subcategory
    ↓ calculates percentages and totals
Tabs → TabsContent
    ↓ maps SubcategoryGroup[]
SubcategoryGroup
    ↓ renders row header + expanded TransactionRow[]
TransactionRow
    ↓ onClick → onTransactionClick(tx)
DashboardClient
    ↓ dispatch OPEN_EDIT_MODAL
TransactionEditModal (existing)
```

**Integration Points:**

- Replace `TransactionTable` import in `dashboard-client.tsx` with `GroupedTransactionList`
- Remove pagination props (not needed with grouped view)
- Pass `totalIncome` and `totalExpenses` from `monthDetail.month` stats
- Keep `onTransactionClick` callback unchanged

**State Management:**

- Local `useState<Set<string>>` for expand/collapse (no reducer needed)
- State resets on month change (component remounts)
- Grouping memoized with `useMemo` keyed on `transactions` array

## Out of Scope

- Backend API changes (all grouping done client-side)
- Changes to score card, metric cards, or pie chart components
- Filter functionality (removed from grouped view, can be added later)
- Pagination (all transactions shown in grouped view)
- Search functionality
- Sorting options (always sorted by amount descending)
- Persisting expand/collapse state across sessions
- Adding new subcategories or icons
- Changing the edit modal behavior or appearance
