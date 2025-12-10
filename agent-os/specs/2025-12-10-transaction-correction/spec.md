# Specification: Transaction Correction

## Goal

Allow users to correct AI-categorized transactions via a modal dialog, automatically recalculating the month's Money Map score when corrections are saved.

## User Stories

- As a budget-conscious user, I want to correct miscategorized transactions so that my Money Map score accurately reflects my spending habits.
- As a user reviewing my monthly dashboard, I want to see which transactions I've manually corrected so I can track AI accuracy.

## Specific Requirements

**Edit Modal Trigger:**

- User clicks any transaction row in the dashboard table to open the edit modal
- TableRow receives `onClick` handler and `cursor-pointer` class for visual feedback
- Modal receives the clicked transaction's full data for display

**Transaction Details Display:**

- Modal header shows "Edit Transaction" with close button
- Transaction description, amount (formatted with currency), and date displayed as read-only
- Read-only fields provide context without allowing unintended edits

**Category Type Selection:**

- Dropdown with 5 options: INCOME, CORE, CHOICE, COMPOUND, EXCLUDED
- Pre-populated with transaction's current `money_map_type`
- Changing type clears subcategory selection and repopulates subcategory options

**Subcategory Selection:**

- Dropdown filtered based on selected Money Map type
- EXCLUDED type has no subcategory (dropdown hidden or disabled)
- Pre-populated with transaction's current `money_map_subcategory`

**Save Behavior:**

- Save button disabled when no changes made (type and subcategory match original)
- On save: API call to `PATCH /api/transactions/{id}`
- Loading state shown during API call (spinner on button, form disabled)
- On success: close modal, refetch month detail to update dashboard
- On error: show error message in modal, keep modal open for retry

**Visual Indicator for Corrected Transactions:**

- Pencil icon (✏️) displayed next to description for transactions where `is_manually_corrected === true`
- Icon has tooltip "Manually corrected" for accessibility
- Uses existing Badge or inline icon pattern from codebase

**Month Stats Recalculation:**

- Backend recalculates totals, percentages, and score after transaction update
- Uses existing `calculate_and_update_month()` service function
- Response includes updated `MonthSummary` for immediate UI refresh

**API Endpoint:**

- `PATCH /api/transactions/{transaction_id}`
- Request body: `{ money_map_type: string, money_map_subcategory: string | null }`
- Response: `{ success: boolean, transaction: TransactionResponse, updated_month_stats: MonthSummary }`
- Error responses: 404 (transaction not found), 400 (invalid category type)

**Error Handling:**

- Network errors: "Unable to connect to server" message
- HTTP errors: Extract and display error message from API response
- Validation: Frontend prevents invalid submissions via disabled save button

## Visual Design

**`planning/visuals/model-wireframe.md`**

- Modal with header containing title and close button [X]
- Body section with transaction info (description, amount, date) as text
- Category Type dropdown (full width)
- Subcategory dropdown (full width, below type)
- Footer with Cancel button (secondary) and Save Changes button (primary)
- Use shadcn/ui Dialog, Select, and Button components
- Low-fidelity wireframe: apply existing app styling, not exact wireframe appearance

## Existing Code to Leverage

**Transaction Table - `frontend/components/dashboard/transaction-table.tsx`**

- What it does: Renders paginated transaction list with Badge for category display
- How to reuse: Add `onTransactionClick` prop, pass to TableRow onClick, add cursor-pointer class
- Key exports: `TransactionTableProps` interface, uses shadcn/ui Table primitives
- Found by: code-explorer analysis of dashboard components

**API Client - `frontend/lib/api-client.ts`**

- What it does: Centralized fetch wrapper with `safeParseJson()` and `extractErrorMessage()` helpers
- How to reuse: Add `updateTransaction()` function following same pattern (try-catch, error extraction)
- Key exports: `API_BASE` constant, helper functions for error handling
- Found by: code-explorer analysis of API patterns

**Calculator Service - `backend/app/services/calculator.py`**

- What it does: Calculates month stats and score from transaction totals
- How to reuse: Call `calculate_and_update_month(db, month_id)` after transaction update
- Key exports: `calculate_and_update_month()`, `calculate_month_stats()`, `calculate_score()`
- Found by: code-explorer analysis of backend services

**Dashboard Client State - `frontend/components/dashboard/dashboard-client.tsx`**

- What it does: Manages dashboard state via useReducer pattern
- How to reuse: Add modal state fields and actions to existing reducer
- Key exports: `DashboardState`, `DashboardAction` types, reducer function
- Found by: code-explorer analysis of state management patterns

**Response Models - `backend/app/responses/months.py`**

- What it does: Pydantic models for API responses with `from_model()` factory methods
- How to reuse: Import `TransactionResponse` and `MonthSummary` for new endpoint response
- Key exports: `TransactionResponse`, `MonthSummary`, `MonthDetailResponse`
- Found by: code-explorer analysis of backend response patterns

## Architecture Approach

**Component Design:**

- `TransactionEditModal`: New presentational component with form state (selectedType, selectedSubcategory)
- `TransactionTable`: Modified to accept `onTransactionClick` callback and display pencil icon
- `DashboardClient`: Extended reducer with modal state (editingTransaction, isEditModalOpen, isSaving)
- Backend: New `transactions.py` router and service, new `responses/transactions.py` models

**Data Flow:**

- Click row → dispatch OPEN_EDIT_MODAL → modal renders with transaction data
- User edits → local form state updates → Save enabled when changes detected
- Save clicked → dispatch SAVE_START → API PATCH call → backend updates DB + recalculates
- Success → dispatch SAVE_SUCCESS → close modal → refetch month detail → UI updates
- Error → dispatch SAVE_ERROR → show error in modal → allow retry

**Integration Points:**

- Frontend modal integrates with existing reducer pattern in DashboardClient
- Backend router registered in `main.py` alongside existing routers
- Score recalculation reuses existing `calculate_and_update_month()` service
- Transaction update sets `is_manually_corrected = True` flag in database

## Out of Scope

- Bulk editing of multiple transactions at once
- Undo/revert functionality for corrections
- Correction history or audit log
- Re-categorization via AI (triggering Claude to re-categorize)
- Editing transaction description, amount, or date
- Inline editing (using modal approach instead)
- Teaching AI from corrections (learning from user feedback)
- Keyboard shortcuts for modal navigation
- Optimistic UI updates (using server response instead)
- Mobile-specific modal behavior
