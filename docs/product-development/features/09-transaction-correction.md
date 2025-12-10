# Transaction Correction Feature Specification

## Overview

**Feature**: Transaction Correction (Roadmap Item #9)
**Size**: Medium (M)
**Status**: Not Started

Add inline editing capability to change transaction categories with automatic score recalculation when corrections are made.

---

## Problem Statement

The AI categorization via Claude API achieves ~90% accuracy, but the remaining ~10% of transactions may be incorrectly categorized. Users currently have no way to correct these mistakes, which:

1. Leads to inaccurate budget scores
2. Undermines trust in the system
3. Prevents users from achieving precise financial tracking

**Target metric**: Manual correction rate < 10% of total transactions.

---

## User Story

```text
En tant qu'utilisateur,
Je veux pouvoir corriger la catégorisation d'une transaction,
Afin que mon score Money Map reflète fidèlement mes dépenses.
```

---

## Acceptance Criteria

- [ ] User can click on a transaction row to open an edit modal
- [ ] Modal displays current category (INCOME/CORE/CHOICE/COMPOUND/EXCLUDED) and subcategory
- [ ] User can select a new Money Map type from a dropdown
- [ ] User can select a new subcategory from a filtered dropdown (based on selected type)
- [ ] On save, the transaction is updated in the database
- [ ] The `is_manually_corrected` flag is set to `true`
- [ ] The month's totals, percentages, and score are automatically recalculated
- [ ] The UI reflects the updated values immediately (optimistic or after refetch)
- [ ] Manually corrected transactions display a visual indicator (badge/icon)
- [ ] Error states are handled gracefully with user feedback

---

## Scope

### In Scope

- Edit modal for single transaction correction
- Dropdown selection for Money Map type and subcategory
- Automatic month stats recalculation
- Visual indicator for corrected transactions
- API endpoint for transaction update

### Out of Scope

- Bulk editing of multiple transactions
- Undo/revert functionality
- Correction history/audit log
- Re-categorization via AI (different feature)

---

## Technical Specification

### Data Model

The `Transaction` model already has the required field:

```python
is_manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
```

**No schema changes required.**

### Money Map Categories Reference

| Type       | Subcategories                                                                                                                                      |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `INCOME`   | Job                                                                                                                                                |
| `CORE`     | Housing, Groceries, Utilities, Healthcare, Transportation, Basic clothing, Phone and internet, Insurance, Debt payments                            |
| `CHOICE`   | Dining out, Entertainment, Travel and vacations, Electronics and gadgets, Hobby supplies, Fancy clothing, Subscription services, Home decor, Gifts |
| `COMPOUND` | Emergency Fund, Education Fund, Investments, Other                                                                                                 |
| `EXCLUDED` | (no subcategory required)                                                                                                                          |

### API Endpoint

**Endpoint**: `PATCH /api/transactions/{transaction_id}`

**Request Body**:

```json
{
  "money_map_type": "CORE",
  "money_map_subcategory": "Groceries"
}
```

**Response** (Success - 200):

```json
{
  "success": true,
  "transaction": {
    "id": 123,
    "date": "2025-10-29",
    "description": "CB Carrefour",
    "amount": -45.50,
    "money_map_type": "CORE",
    "money_map_subcategory": "Groceries",
    "is_manually_corrected": true
  },
  "updated_month_stats": {
    "total_income": 2823.29,
    "total_core": 1290.50,
    "total_choice": 633.00,
    "total_compound": 899.79,
    "core_percentage": 45.7,
    "choice_percentage": 22.4,
    "compound_percentage": 31.9,
    "score": 3,
    "score_label": "Great"
  }
}
```

**Error Responses**:

- `404`: Transaction not found
- `400`: Invalid money_map_type or subcategory
- `500`: Internal server error

### Backend Implementation

#### 1. Request/Response Models

**Location**: `backend/app/responses/transactions.py`

```python
class UpdateTransactionRequest(BaseModel):
    money_map_type: MoneyMapType
    money_map_subcategory: str | None = None

class UpdateTransactionResponse(BaseModel):
    success: bool
    transaction: TransactionResponse
    updated_month_stats: MonthSummary
```

#### 2. Service Layer

**Location**: `backend/app/services/transactions.py`

Functions required:

- `update_transaction(db, transaction_id, money_map_type, money_map_subcategory)` - Update transaction and set `is_manually_corrected = True`
- `recalculate_month_stats(db, month_id)` - Recalculate totals, percentages, and score for the affected month

#### 3. Router

**Location**: `backend/app/routers/transactions.py`

```python
@router.patch("/{transaction_id}", response_model=UpdateTransactionResponse)
async def update_transaction(
    transaction_id: int,
    request: UpdateTransactionRequest,
    db: Session = Depends(get_db)
):
    # 1. Validate transaction exists
    # 2. Update transaction category
    # 3. Recalculate month stats
    # 4. Return updated data
```

### Frontend Implementation

#### 1. API Client

**Location**: `frontend/lib/api-client.ts`

```typescript
interface UpdateTransactionPayload {
  money_map_type: MoneyMapType
  money_map_subcategory: string | null
}

export async function updateTransaction(
  transactionId: number,
  payload: UpdateTransactionPayload
): Promise<UpdateTransactionResponse>
```

#### 2. Edit Modal Component

**Location**: `frontend/components/dashboard/transaction-edit-modal.tsx`

Props:

- `transaction: Transaction` - The transaction to edit
- `isOpen: boolean` - Modal visibility state
- `onClose: () => void` - Close handler
- `onSave: (response: UpdateTransactionResponse) => void` - Success callback

Features:

- Form with two dropdowns (type and subcategory)
- Subcategory dropdown filters based on selected type
- Loading state during API call
- Error display on failure
- Disable save button when no changes made

#### 3. Transaction Table Updates

**Location**: `frontend/components/dashboard/transaction-table.tsx`

Changes:

- Add click handler on transaction rows to open edit modal
- Add visual indicator (icon/badge) for `is_manually_corrected === true`
- Refresh data or update local state after successful edit

### Month Recalculation Logic

When a transaction category changes, the month stats must be recalculated:

```python
# Pseudocode
def recalculate_month_stats(db: Session, month_id: int) -> Month:
    transactions = get_all_transactions_for_month(month_id)

    total_income = sum(t.amount for t in transactions if t.money_map_type == "INCOME" and t.amount > 0)
    total_core = abs(sum(t.amount for t in transactions if t.money_map_type == "CORE" and t.amount < 0))
    total_choice = abs(sum(t.amount for t in transactions if t.money_map_type == "CHOICE" and t.amount < 0))
    total_compound = total_income - total_core - total_choice

    core_pct = (total_core / total_income * 100) if total_income > 0 else 0
    choice_pct = (total_choice / total_income * 100) if total_income > 0 else 0
    compound_pct = (total_compound / total_income * 100) if total_income > 0 else 0

    score = calculate_score(core_pct, choice_pct, compound_pct)

    # Update month record
    month.total_income = total_income
    month.total_core = total_core
    # ... etc

    return month
```

---

## UI/UX Design

### Edit Modal Wireframe

```text
┌────────────────────────────────────────────────┐
│  Edit Transaction                          [X] │
├────────────────────────────────────────────────┤
│                                                │
│  Transaction: CB Carrefour                     │
│  Amount: -45.50 EUR                            │
│  Date: 29/10/2025                              │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │ Category Type                         ▼  │  │
│  │ CORE                                     │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │ Subcategory                           ▼  │  │
│  │ Groceries                                │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│           [Cancel]        [Save Changes]       │
│                                                │
└────────────────────────────────────────────────┘
```

### Visual Indicator for Corrected Transactions

In the transaction table, show a small icon (pencil or checkmark) next to manually corrected transactions:

```text
│ 29/10  CB Carrefour ✏️      -45.50€    CORE 🏠   │
```

---

## Testing Requirements

### Backend Tests

1. **Unit tests** for `update_transaction()` service function
2. **Unit tests** for `recalculate_month_stats()` function
3. **Integration tests** for `PATCH /api/transactions/{id}` endpoint:
   - Happy path: valid update
   - 404: transaction not found
   - 400: invalid category type
   - Verify month stats are recalculated correctly

### Frontend Tests

1. **Component tests** for edit modal (render, form validation)
2. **Integration tests** for update flow (mock API, verify UI updates)

---

## Implementation Checklist

### Backend

- [ ] Create `backend/app/responses/transactions.py` with request/response models
- [ ] Create `backend/app/services/transactions.py` with update and recalculation logic
- [ ] Create `backend/app/routers/transactions.py` with PATCH endpoint
- [ ] Register router in `backend/app/main.py`
- [ ] Write unit tests for services
- [ ] Write integration tests for endpoint

### Frontend

- [ ] Add `updateTransaction()` function to `frontend/lib/api-client.ts`
- [ ] Add types for update request/response in `frontend/types/index.ts`
- [ ] Create `frontend/components/dashboard/transaction-edit-modal.tsx`
- [ ] Update `frontend/components/dashboard/transaction-table.tsx` with edit trigger and indicator
- [ ] Add subcategory constants/mapping for dropdown options
- [ ] Handle loading and error states

---

## Dependencies

- None (builds on existing infrastructure)

## Risks

| Risk                                               | Mitigation                                      |
| -------------------------------------------------- | ----------------------------------------------- |
| Race condition if user edits while data is loading | Disable edit while fetching                     |
| Subcategory validation mismatch                    | Share category mapping between frontend/backend |

---

## Success Metrics

- Users can correct categorization errors without re-importing data
- Month scores update correctly after corrections
- Manual correction rate stays below 10% of transactions
