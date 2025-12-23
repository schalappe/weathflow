# Spec Requirements: Transaction Readability Enhancement

## Initial Description

In the homepage, the transactions are too numerous and difficult to read and understand. To enhance readability, split transactions into two tabs: Inputs (Entrées) and Outputs (Sorties). Group transactions by subcategories (restaurant, courses, salaire, etc.), showing only subcategories with total amounts. Users can click on a subcategory to expand and see individual transactions in a dropdown. Must preserve the ability to edit transactions (non-regression).

## Requirements Discussion

### Questions & Answers

**Q1:** I assume "Inputs" (Entrées) means INCOME transactions and "Outputs" (Sorties) means CORE + CHOICE + COMPOUND expenses. Is that correct, or should we also include EXCLUDED transactions somewhere?
**A:** Inputs means positive amounts, Outputs means negative amounts. Include EXCLUDED transactions - they are still transactions and can be input or output. EXCLUDED should be shown in their own "Excluded" subcategory.

**Q2:** The backend already stores `money_map_subcategory` for each transaction. I assume we use this field for grouping. Is that correct?
**A:** Yes, use that field.

**Q3:** For layout, should we use two separate cards side-by-side or tabs like Bankin'?
**A:** Option B - tabs seem more appealing (single card with tab switching).

**Q4:** Should we show percentage of total spending + transaction count, only count, or percentage + count + Money Map type badge?
**A:** Option C - percentage + count + Money Map type badge (gives more information).

**Q5:** Should subcategories have colored icons, colored dots matching Money Map type, or no icons?
**A:** Option A - add icons to subcategories (Money Map type badge is already shown per Q4).

**Q6:** When user clicks a subcategory to expand, what should individual transactions show?
**A:** Option A - minimal (date + description + amount only). To edit, user clicks on the transaction row to open edit modal (preserve current behavior).

**Q7:** What should be explicitly OUT of scope for this feature?
**A:** Only working on transactions (improving readability). Anything else is out of scope.

### Existing Code References

| File                                                       | Purpose                                                                       |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `frontend/components/dashboard/transaction-table.tsx`      | Current flat transaction list (to be replaced)                                |
| `frontend/components/dashboard/transaction-edit-modal.tsx` | Edit modal (must preserve, non-regression)                                    |
| `frontend/components/dashboard/transaction-filters.tsx`    | Current filters (may need adaptation)                                         |
| `frontend/types/index.ts`                                  | TypeScript types including `TransactionResponse` with `money_map_subcategory` |
| `backend/app/responses/cashflow.py`                        | Backend already has subcategory breakdown logic                               |

### Follow-up Questions

None required.

## Visual Assets

### Files Found

No visual assets provided.

### Visual Guidelines

- Use shadcn/ui components to stay conform with tech stack
- Reference Bankin' app design (provided in conversation) for UX inspiration
- Icons for subcategories need to be created/mapped

## Requirements Summary

### Functional Requirements

1. **Tab-based Layout**
   - Single card with two tabs: "Entrées" (Inputs) and "Sorties" (Outputs)
   - Inputs tab: transactions with positive amounts
   - Outputs tab: transactions with negative amounts

2. **Subcategory Grouping**
   - Group transactions by `money_map_subcategory` field
   - Each subcategory row displays:
     - Icon (mapped to subcategory name)
     - Subcategory name
     - Percentage of total (within that tab)
     - Transaction count
     - Money Map type badge (CORE/CHOICE/COMPOUND/EXCLUDED)
     - Total amount

3. **Expandable Subcategories**
   - Click subcategory to expand/collapse
   - Expanded view shows individual transactions
   - Transaction row: date + description + amount (minimal)
   - Click transaction row to open edit modal

4. **EXCLUDED Handling**
   - EXCLUDED transactions appear in their own "Excluded" subcategory
   - Can appear in either Inputs or Outputs tab based on amount sign

5. **Edit Capability (Non-regression)**
   - Preserve existing edit modal functionality
   - Click on transaction row triggers edit modal
   - After edit, recalculate groupings and totals

### Reusability Opportunities

- `transaction-edit-modal.tsx` - reuse as-is
- Backend `CashFlowData` structure already groups by subcategory
- shadcn/ui `Tabs`, `Collapsible`, `Badge` components

### Scope Boundaries

**In Scope:**

- Transaction display restructuring (tabs + grouped subcategories)
- Subcategory expand/collapse interaction
- Icon mapping for subcategories
- Percentage and count calculations per subcategory
- Preserve edit transaction functionality

**Out of Scope:**

- Changes to other dashboard components (score card, metric cards, charts)
- Backend API changes (unless required for grouping)
- Filter functionality changes
- Pagination changes
- Any non-transaction related features

### Technical Considerations

- Frontend-only change (grouping can be done client-side from existing data)
- Need to create subcategory-to-icon mapping
- Must handle null/empty subcategories gracefully
- Recalculate percentages when transactions are updated
- Consider performance with large transaction counts (159+ transactions)
