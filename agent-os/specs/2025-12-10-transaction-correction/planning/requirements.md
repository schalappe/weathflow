# Spec Requirements: Transaction Correction

## Initial Description

Add inline editing capability to change transaction categories with automatic score recalculation when corrections are made (Roadmap Item #9, Size: M).

## Requirements Discussion

### First Round Questions

**Q1:** I assume the inline editing happens directly in the transaction table on the Monthly Dashboard (clicking a category to edit it). Is that correct, or would you prefer a modal/drawer-based editing experience?
**Answer:** Modal-based editing. User clicks on a transaction row to open an edit modal (per existing spec at `docs/product-development/features/09-transaction-correction.md`).

**Q2:** I'm thinking the category selector should be a simple dropdown showing all Money Map categories (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED). Should we also allow editing the transaction description, or just the category?
**Answer:** Category only. Modal displays transaction description, amount, and date as read-only. User can only edit Money Map type and subcategory via dropdowns.

**Q3:** I assume the score recalculation should happen immediately after a category change (optimistic UI update with backend sync). Is that correct, or would you prefer a "Save Changes" button approach?
**Answer:** Save button approach. Modal has Cancel and Save Changes buttons. Score recalculation happens after user clicks Save.

**Q4:** I'm thinking we should show visual feedback when a transaction has been manually corrected (e.g., a small indicator or different styling) so users can distinguish AI-categorized vs. user-corrected transactions. Is this needed, or should corrected transactions look identical to others?
**Answer:** Yes, visual indicator needed. Show a pencil icon (✏️) next to manually corrected transactions in the transaction table.

**Q5:** Should there be any confirmation before changing a category, or should the change apply immediately on selection?
**Answer:** No additional confirmation. The modal itself with Cancel/Save buttons provides sufficient confirmation flow.

**Q6:** I assume we do NOT need batch editing (selecting multiple transactions to change their category at once) for this feature. Correct?
**Answer:** Correct. Bulk editing is explicitly out of scope.

**Q7:** What should be explicitly OUT of scope for this feature?
**Answer:** Out of scope includes: bulk editing of multiple transactions, undo/revert functionality, correction history/audit log, and re-categorization via AI.

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Monthly Dashboard - Path: `frontend/components/dashboard/`
- Feature: Transaction Table - Path: `frontend/components/dashboard/transaction-table.tsx`
- Feature: API Client - Path: `frontend/lib/api-client.ts`
- Feature: Score Calculation Service - Path: `backend/app/services/`
- Feature: Months Router - Path: `backend/app/routers/months.py`

### Follow-up Questions

**Follow-up 1:** The existing spec at `docs/product-development/features/09-transaction-correction.md` is comprehensive. Should I use this spec as-is or enhance it with code exploration?
**Answer:** Follow the workflow - create requirements document and proceed with spec writing phase including code exploration.

## Visual Assets

### Files Provided

- `model-wireframe.md`: ASCII wireframe showing edit modal layout with:
  - Header: "Edit Transaction" with close button [X]
  - Read-only fields: Transaction name, Amount, Date
  - Editable dropdowns: Category Type and Subcategory
  - Action buttons: Cancel and Save Changes

### Visual Insights

- Modal is simple and focused - only two editable fields
- Clear hierarchy: transaction info displayed first, then edit controls
- Standard modal pattern with header, body, footer layout
- Low-fidelity ASCII wireframe - use application's existing shadcn/ui styling

## Requirements Summary

### Functional Requirements

- User can click on a transaction row in the dashboard to open edit modal
- Modal displays transaction details (description, amount, date) as read-only
- User can select new Money Map type from dropdown (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED)
- User can select new subcategory from filtered dropdown (options depend on selected type)
- Subcategory is optional for EXCLUDED type
- On save, transaction is updated with `is_manually_corrected = true`
- Month totals, percentages, and score are automatically recalculated
- UI reflects updated values after successful save
- Manually corrected transactions display pencil icon indicator
- Error states handled gracefully with user feedback
- Save button disabled when no changes made

### Data Model

- Uses existing `is_manually_corrected` field on Transaction model
- No schema changes required

### API Contract

- Endpoint: `PATCH /api/transactions/{transaction_id}`
- Request: `{ money_map_type, money_map_subcategory }`
- Response: Updated transaction + recalculated month stats
- Error codes: 404 (not found), 400 (invalid category), 500 (server error)

### Money Map Categories Reference

| Type     | Subcategories                                                                                                                                      |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| INCOME   | Job                                                                                                                                                |
| CORE     | Housing, Groceries, Utilities, Healthcare, Transportation, Basic clothing, Phone and internet, Insurance, Debt payments                            |
| CHOICE   | Dining out, Entertainment, Travel and vacations, Electronics and gadgets, Hobby supplies, Fancy clothing, Subscription services, Home decor, Gifts |
| COMPOUND | Emergency Fund, Education Fund, Investments, Other                                                                                                 |
| EXCLUDED | (no subcategory required)                                                                                                                          |

### Reusability Opportunities

- Existing transaction table component for adding click handler and indicator
- shadcn/ui Dialog component for modal
- shadcn/ui Select component for dropdowns
- Existing API client pattern for new endpoint
- Existing score calculation service for recalculation logic

### Scope Boundaries

**In Scope:**

- Edit modal for single transaction correction
- Dropdown selection for Money Map type and subcategory
- Automatic month stats recalculation on save
- Visual indicator (pencil icon) for corrected transactions
- API endpoint for transaction update
- Loading and error states

**Out of Scope:**

- Bulk editing of multiple transactions
- Undo/revert functionality
- Correction history/audit log
- Re-categorization via AI (different feature)
- Editing transaction description, amount, or date
- Inline editing (using modal instead)

### Technical Considerations

- Race condition mitigation: disable edit while data is fetching
- Subcategory validation: share category mapping between frontend and backend
- Optimistic vs server update: use server response to update UI (safer approach)
- Existing `is_manually_corrected` field available - no migration needed

### Success Metrics

- Users can correct categorization errors without re-importing data
- Month scores update correctly after corrections
- Manual correction rate stays below 10% of transactions
