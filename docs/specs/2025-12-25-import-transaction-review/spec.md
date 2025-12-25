# Specification: Import Transaction Review

## Goal

Enable users to review and correct AI-categorized transactions immediately after CSV import, before finalizing the import process, by clicking the currently disabled "Voir les transactions pour vérifier" button.

## User Stories

- As a user who just imported transactions, I want to review the AI categorization before finishing so that I can correct any mistakes immediately
- As a user reviewing transactions, I want to see which months have low-confidence categorizations so that I can prioritize my review
- As a user editing a transaction, I want the change to be reflected immediately so that I know my correction was saved

## Specific Requirements

**Enable Review Button:**

- Remove the `disabled` attribute from the "Voir les transactions pour vérifier" button in `results-summary.tsx`
- Remove the tooltip showing "Bientôt disponible"
- Wire button to open the transaction review sheet

**Month Selection via Tabs:**

- Display horizontal tabs for each categorized month (from `MonthResult[]`)
- Format tabs as "Nov 2024", "Dec 2024" (localized month names)
- Show amber warning icon on tabs where `low_confidence_count > 0`
- Auto-select the first month when sheet opens
- Switching tabs fetches transactions for that month via API

**Transaction Review Sheet:**

- Use shadcn/ui Sheet component sliding from right (`side="right"`)
- Width: full on mobile, max 800px on desktop (`w-full sm:max-w-[800px]`)
- Header shows "Vérifier les transactions" with close button
- Content area is scrollable with fixed header/footer

**Transaction List Display:**

- Show all transactions for selected month in a table format
- Columns: Date, Description, Amount, Category (badge)
- Display total count and low-confidence count in header: "12 transactions dont 3 a faible confiance"
- Clicking a row opens the edit modal for that transaction

**Inline Category Editing:**

- Reuse existing `TransactionEditModal` from dashboard (no modifications needed)
- On save success, update the transaction in the local list
- On save error, display error in modal (existing behavior)

**Low-Confidence Indication:**

- Display count badge at month level (in tab and list header)
- Individual transaction highlighting not possible (no per-transaction confidence flag in API response)
- Inform users some transactions may need review

**Return Flow:**

- Closing the sheet returns user to the results summary
- User can then click "Terminer l'import" to go to dashboard
- Changes made during review are persisted immediately via API

**Scope Limitation:**

- Only show transactions from months in `state.categorizeResponse.months_processed`
- Do not show historical transactions from previous imports

## Existing Code to Leverage

**TransactionEditModal — `frontend/components/dashboard/transaction-edit-modal.tsx`**

- What it does: Full category editing UI with type/subcategory dropdowns
- How to reuse: Import and render inside sheet, pass transaction and callbacks
- Key methods: Props interface accepts `transaction`, `isOpen`, `onClose`, `onSave`, `isSaving`, `error`

**Import State Machine — `frontend/components/import/import-page-client.tsx`**

- What it does: Manages import flow with useReducer (5 states)
- How to reuse: Add `isReviewSheetOpen` state and corresponding actions
- Key methods: `dispatch({ type: "OPEN_REVIEW_SHEET" })` and `CLOSE_REVIEW_SHEET`

**API Client — `frontend/lib/api-client.ts`**

- What it does: Centralized API calls with error handling
- How to reuse: Call `getMonthDetail(year, month)` to fetch transactions
- Key methods: `getMonthDetail()`, `updateTransaction()`

**Category Styling — `frontend/components/dashboard/transaction-table.tsx`**

- What it does: Consistent badge styling per MoneyMapType
- How to reuse: Import `CATEGORY_STYLES` mapping for category badges
- Key methods: Object mapping type to Tailwind classes

**shadcn/ui Sheet — To be added via CLI:**

- What it does: Accessible slide-in panel with focus management
- How to reuse: `bunx shadcn@latest add sheet`
- Key methods: `<Sheet>`, `<SheetContent>`, `<SheetHeader>`, `<SheetTitle>`

## Architecture Approach

**Component Design:**

```text
ImportPageClient
├── ResultsSummary (modified: add onReviewClick prop)
└── TransactionReviewSheet (new)
    ├── Tabs (month selection)
    ├── TransactionReviewList (new)
    │   └── Transaction rows with category badges
    └── TransactionEditModal (reused from dashboard)
```

**Data Flow:**

```bash
Button click → OPEN_REVIEW_SHEET action
    → Sheet opens with tabs for each MonthResult
    → User selects month tab
    → getMonthDetail(year, month) API call
    → Transactions displayed in list
    → User clicks row → Edit modal opens
    → User saves → updateTransaction() API call
    → Success → Local list updated
    → User closes sheet → CLOSE_REVIEW_SHEET action
    → Back to results summary
```

**State Management:**

| Component              | State Approach                                       |
| ---------------------- | ---------------------------------------------------- |
| ImportPageClient       | Add `isReviewSheetOpen: boolean` to reducer          |
| TransactionReviewSheet | Internal useState for transactions, loading, editing |
| TransactionEditModal   | Reused as-is (props-driven)                          |

**Integration Points:**

- ResultsSummary receives new `onReviewClick` callback prop
- Sheet receives `monthResults` from `state.categorizeResponse.months_processed`
- Edit modal receives `TransactionResponse` from sheet's local state
- API calls use existing authenticated fetch client

## Out of Scope

- Bulk editing multiple transactions at once
- Advanced filtering by confidence level
- Filtering/sorting transactions within the review list
- Changes to backend API
- Reviewing old/historical transactions (only current import)
- New page routes (feature stays within import flow)
- Dashboard modifications
- Per-transaction low-confidence highlighting (data not available)
- Pagination within the review list (fetch all for simplicity)
- Score recalculation display in sheet (handled on dashboard)
