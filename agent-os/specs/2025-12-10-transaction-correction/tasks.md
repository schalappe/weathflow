# Task Breakdown: Transaction Correction

## Overview

Total Tasks: 22
Estimated Complexity: Medium
Primary Stack: FastAPI (Python) + Next.js (TypeScript)

## Task List

### Backend Layer

#### Task Group 1: Response Models and Exception

**Dependencies:** None

- [x] 1.0 Complete backend response models and exception handling
  - [x] 1.1 Write 3 focused tests for transaction update validation
    - Test valid MoneyMapType values are accepted
    - Test invalid MoneyMapType returns 400 error
    - Test subcategory validation per type
  - [x] 1.2 Create `TransactionNotFoundError` exception class
    - Add to `backend/app/services/exceptions.py`
    - Include `transaction_id` attribute for programmatic access
    - Follow existing exception pattern in file
  - [x] 1.3 Create `backend/app/responses/transactions.py` with request/response models
    - `UpdateTransactionRequest`: money_map_type (MoneyMapType), money_map_subcategory (str | None)
    - `UpdateTransactionResponse`: success (bool), transaction (TransactionResponse), updated_month_stats (MonthSummary)
    - Reuse `TransactionResponse` and `MonthSummary` from `responses/months.py`
  - [x] 1.4 Ensure validation tests pass
    - Run ONLY the 3 tests from 1.1
    - Verify Pydantic validation works correctly

**Acceptance Criteria:**

- All 3 tests from 1.1 pass
- Request model validates MoneyMapType enum values
- Response model correctly reuses existing types
- Exception class follows existing pattern

#### Task Group 2: Transaction Service

**Dependencies:** Task Group 1

- [x] 2.0 Complete transaction service layer
  - [x] 2.1 Write 4 focused tests for transaction service
    - Test update sets `is_manually_corrected = True`
    - Test update changes `money_map_type` and `money_map_subcategory`
    - Test update triggers month stats recalculation
    - Test update raises `TransactionNotFoundError` for invalid ID
  - [x] 2.2 Create `backend/app/services/transactions.py` with `update_transaction_category()` function
    - Parameters: `db: Session`, `transaction_id: int`, `money_map_type: MoneyMapType`, `money_map_subcategory: str | None`
    - Returns: `tuple[Transaction, Month]`
    - Fetch transaction or raise `TransactionNotFoundError`
    - Update fields and set `is_manually_corrected = True`
    - Call `calculate_and_update_month(db, transaction.month_id)` from calculator service
  - [x] 2.3 Ensure service tests pass
    - Run ONLY the 4 tests from 2.1
    - Verify recalculation integration works

**Acceptance Criteria:**

- All 4 tests from 2.1 pass
- Service correctly updates transaction fields
- Service triggers month recalculation
- Service raises proper exception for missing transaction

#### Task Group 3: Transaction Router

**Dependencies:** Task Group 2

- [x] 3.0 Complete transaction router
  - [x] 3.1 Write 4 focused integration tests for PATCH endpoint
    - Test valid update returns 200 with updated data
    - Test non-existent transaction returns 404
    - Test invalid category type returns 400
    - Test response includes recalculated month stats
  - [x] 3.2 Create `backend/app/routers/transactions.py` with PATCH endpoint
    - Route: `PATCH /api/transactions/{transaction_id}`
    - Path validation: `transaction_id: int = Path(..., ge=1)`
    - Request body: `UpdateTransactionRequest`
    - Response model: `UpdateTransactionResponse`
    - Follow pattern from `routers/months.py`
  - [x] 3.3 Add exception handlers for `TransactionNotFoundError` (404) and validation errors (400)
    - Return proper HTTP status codes
    - Include descriptive error messages
  - [x] 3.4 Register router in `backend/app/main.py`
    - Import: `from app.routers import transactions`
    - Add: `app.include_router(transactions.router)`
  - [x] 3.5 Ensure router tests pass
    - Run ONLY the 4 tests from 3.1
    - Verify end-to-end API flow works

**Acceptance Criteria:**

- All 4 tests from 3.1 pass
- PATCH endpoint accessible at `/api/transactions/{id}`
- Proper error responses for 404 and 400 cases
- Response includes updated transaction and month stats

### Frontend Layer

#### Task Group 4: Types and API Client

**Dependencies:** Task Group 3

- [ ] 4.0 Complete frontend types and API client
  - [ ] 4.1 Add TypeScript types to `frontend/types/index.ts`
    - `UpdateTransactionPayload`: `{ money_map_type: MoneyMapType, money_map_subcategory: string | null }`
    - `UpdateTransactionResponse`: `{ success: boolean, transaction: TransactionResponse, updated_month_stats: MonthSummary }`
  - [ ] 4.2 Add `updateTransaction()` function to `frontend/lib/api-client.ts`
    - Parameters: `transactionId: number`, `payload: UpdateTransactionPayload`
    - Returns: `Promise<UpdateTransactionResponse>`
    - Use PATCH method with JSON body
    - Follow existing error handling pattern (try-catch, extractErrorMessage)
  - [ ] 4.3 Create `frontend/lib/category-options.ts` with subcategory mappings
    - `MONEY_MAP_TYPES: MoneyMapType[]` array
    - `SUBCATEGORY_OPTIONS: Record<MoneyMapType, string[]>` mapping
    - Include all subcategories per type from requirements

**Acceptance Criteria:**

- Types compile without errors
- API client function follows existing patterns
- Category options match spec requirements table

#### Task Group 5: UI Component Setup

**Dependencies:** Task Group 4

- [ ] 5.0 Complete UI component prerequisites
  - [ ] 5.1 Install shadcn/ui Dialog component
    - Run: `cd frontend && bunx shadcn@latest add dialog`
    - Verify `frontend/components/ui/dialog.tsx` is created
  - [ ] 5.2 Verify lucide-react Pencil icon is available
    - Check lucide-react is in package.json (should be installed with shadcn)
    - Test import: `import { Pencil } from 'lucide-react'`

**Acceptance Criteria:**

- Dialog component installed and importable
- Pencil icon available from lucide-react

#### Task Group 6: Transaction Edit Modal

**Dependencies:** Task Group 5

- [ ] 6.0 Complete transaction edit modal component
  - [ ] 6.1 Write 4 focused tests for TransactionEditModal
    - Test renders transaction details as read-only
    - Test filters subcategory options when type changes
    - Test save button disabled when no changes made
    - Test calls onSave with correct payload
  - [ ] 6.2 Create `frontend/components/dashboard/transaction-edit-modal.tsx`
    - Props interface: `transaction: TransactionResponse | null`, `isOpen: boolean`, `onClose: () => void`, `onSave: (payload: UpdateTransactionPayload) => void`, `isSaving: boolean`, `error: string | null`
    - Internal state: `selectedType`, `selectedSubcategory`
    - Use Dialog, Select, Button from shadcn/ui
  - [ ] 6.3 Implement read-only transaction details section
    - Display description, amount (formatted), date
    - Match wireframe layout: `planning/visuals/model-wireframe.md`
  - [ ] 6.4 Implement category type dropdown
    - Pre-populate with current `money_map_type`
    - On change: clear subcategory and repopulate options
  - [ ] 6.5 Implement subcategory dropdown
    - Filter options based on selected type
    - Hide/disable for EXCLUDED type
    - Pre-populate with current `money_map_subcategory`
  - [ ] 6.6 Implement save/cancel buttons with loading state
    - Save disabled when no changes or isSaving
    - Show spinner on save button when isSaving
    - Display error message when error prop is set
  - [ ] 6.7 Ensure modal tests pass
    - Run ONLY the 4 tests from 6.1

**Acceptance Criteria:**

- All 4 tests from 6.1 pass
- Modal displays correctly per wireframe
- Form state tracks changes properly
- Loading and error states work correctly

#### Task Group 7: Transaction Table Updates

**Dependencies:** Task Group 6

- [ ] 7.0 Complete transaction table modifications
  - [ ] 7.1 Write 2 focused tests for transaction table updates
    - Test click handler is called with transaction data
    - Test pencil icon displays for manually corrected transactions
  - [ ] 7.2 Add `onTransactionClick` prop to `TransactionTableProps` interface
    - Type: `(transaction: TransactionResponse) => void`
    - Update interface in `frontend/components/dashboard/transaction-table.tsx`
  - [ ] 7.3 Add click handler and cursor style to TableRow
    - Pass `onClick={() => onTransactionClick(tx)}` to TableRow
    - Add `className="cursor-pointer"` for visual feedback
  - [ ] 7.4 Add pencil icon indicator for corrected transactions
    - Import `Pencil` from lucide-react
    - Conditionally render when `tx.is_manually_corrected === true`
    - Add tooltip: "Manually corrected"
    - Position next to description
  - [ ] 7.5 Ensure table tests pass
    - Run ONLY the 2 tests from 7.1

**Acceptance Criteria:**

- All 2 tests from 7.1 pass
- Rows are clickable with pointer cursor
- Pencil icon shows for corrected transactions
- Tooltip is accessible

#### Task Group 8: Dashboard Integration

**Dependencies:** Task Group 7

- [ ] 8.0 Complete dashboard client integration
  - [ ] 8.1 Write 3 focused tests for dashboard modal integration
    - Test clicking row opens modal with transaction data
    - Test successful save closes modal and refreshes data
    - Test error displays in modal without closing
  - [ ] 8.2 Extend `DashboardState` interface with modal state
    - Add: `editingTransaction: TransactionResponse | null`
    - Add: `isEditModalOpen: boolean`
    - Add: `isSaving: boolean`
    - Add: `saveError: string | null`
  - [ ] 8.3 Add reducer actions for modal state
    - `OPEN_EDIT_MODAL`: Set editingTransaction and isEditModalOpen
    - `CLOSE_EDIT_MODAL`: Clear modal state
    - `SAVE_START`: Set isSaving true
    - `SAVE_SUCCESS`: Close modal, clear state
    - `SAVE_ERROR`: Set saveError, keep modal open
  - [ ] 8.4 Implement modal handlers in DashboardClient
    - `handleTransactionClick`: dispatch OPEN_EDIT_MODAL
    - `handleCloseModal`: dispatch CLOSE_EDIT_MODAL
    - `handleSaveTransaction`: API call, dispatch SAVE_START/SUCCESS/ERROR, trigger refetch
  - [ ] 8.5 Render TransactionEditModal in DashboardClient
    - Pass state and handlers as props
    - Position after TransactionTable in JSX
  - [ ] 8.6 Pass `onTransactionClick` to TransactionTable
    - Connect handler to table component
  - [ ] 8.7 Ensure integration tests pass
    - Run ONLY the 3 tests from 8.1

**Acceptance Criteria:**

- All 3 tests from 8.1 pass
- Full edit flow works: click → edit → save → refresh
- Error handling keeps modal open for retry
- Dashboard stats update after save

### Testing Layer

#### Task Group 9: Test Review and Gap Analysis

**Dependencies:** Task Groups 1-8

- [ ] 9.0 Review existing tests and fill critical gaps
  - [ ] 9.1 Review tests from all task groups
    - Backend validation tests (3 from 1.1)
    - Backend service tests (4 from 2.1)
    - Backend router tests (4 from 3.1)
    - Frontend modal tests (4 from 6.1)
    - Frontend table tests (2 from 7.1)
    - Frontend integration tests (3 from 8.1)
    - Total existing: ~20 tests
  - [ ] 9.2 Identify critical coverage gaps
    - Focus on end-to-end user workflows
    - Check integration points between frontend and backend
    - Verify error scenarios are covered
  - [ ] 9.3 Write up to 6 additional strategic tests
    - End-to-end: Complete correction flow from click to updated score
    - Edge case: Correction with EXCLUDED type (no subcategory)
    - Edge case: Changing from one type to another
    - Concurrent edit handling (if applicable)
    - Network error recovery
    - Score recalculation accuracy verification
  - [ ] 9.4 Run feature-specific tests only
    - Run all tests related to transaction correction
    - Expected total: ~26 tests
    - Verify all critical workflows pass

**Acceptance Criteria:**

- All ~26 feature tests pass
- Critical user workflows are covered
- No more than 6 additional tests added
- End-to-end flow verified

## Execution Order

1. **Task Group 1**: Response Models and Exception - Foundation for API contract
2. **Task Group 2**: Transaction Service - Business logic layer
3. **Task Group 3**: Transaction Router - Complete backend API
4. **Task Group 4**: Types and API Client - Frontend-backend bridge
5. **Task Group 5**: UI Component Setup - Install dependencies
6. **Task Group 6**: Transaction Edit Modal - Core UI component
7. **Task Group 7**: Transaction Table Updates - Enable interaction
8. **Task Group 8**: Dashboard Integration - Wire everything together
9. **Task Group 9**: Test Review - Verify complete feature

## Notes

- **No database changes**: Uses existing `is_manually_corrected` field
- **Reuse patterns**: Follow existing router, service, and component patterns
- **Score recalculation**: Leverage existing `calculate_and_update_month()` service
- **Error handling**: Follow established patterns in API client and router
