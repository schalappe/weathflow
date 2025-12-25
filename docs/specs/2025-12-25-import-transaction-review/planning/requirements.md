# Spec Requirements: Import Transaction Review

## Initial Description

In the import of CSV, after categorization, the app should offer the possibility to view the transactions and fix categorization. Currently, the frontend shows a disabled button "Voir les transactions pour vérifier" (View transactions to verify). The goal is to enable this feature.

## Requirements Discussion

### Questions & Answers

**Q1:** I see you've categorized 10 months (1210 transactions). When clicking "Voir les transactions pour vérifier", should the user see all months in a list and pick which one to review, see all transactions at once, or something else?
**A:** Option A (show months in a list, let user pick) seems good, but open to creative solutions.

**Q2:** For the import review UI, should we open a modal/dialog (stays on import page), navigate to a dedicated review page, or navigate to the dashboard with pre-selected month?
**A:** Option A (modal/dialog showing transactions with inline editing, stays on import page) seems good.

**Q3:** Should transactions with low AI confidence be visually highlighted, shown at the top, or have no special treatment?
**A:** Option A (visually highlighted) seems good, but open to creative solutions.

**Q4:** After the user finishes reviewing/fixing transactions, should they return to results summary, go directly to dashboard, or have both options?
**A:** Option A (return to results summary) seems logical, but choose what works best.

**Q5:** What should be explicitly OUT of scope for this feature?
**A:** The feature is about reviewing imported transactions and correcting them if necessary. Everything else is out of scope. The review concerns ONLY transactions that have been imported in this session, not old transactions.

### Existing Code References

Based on codebase exploration, these components can be reused:

| Component                | File                                                         | Purpose                                                  |
| ------------------------ | ------------------------------------------------------------ | -------------------------------------------------------- |
| `TransactionEditModal`   | `frontend/components/dashboard/transaction-edit-modal.tsx`   | Full category editing UI with type/subcategory dropdowns |
| `GroupedTransactionList` | `frontend/components/dashboard/grouped-transaction-list.tsx` | Groups transactions by subcategory with expand/collapse  |
| `TransactionTable`       | `frontend/components/dashboard/transaction-table.tsx`        | Paginated table with filtering                           |
| `MonthResultCard`        | `frontend/components/import/results-summary.tsx`             | Shows score badge per month                              |

### Follow-up Questions

None needed — requirements are clear.

## Visual Assets

### Files Found

No visual assets provided.

### Visual Insights

- Use shadcn/ui components for consistency with existing UI
- Follow existing patterns from `TransactionEditModal` and dashboard components
- Reference shadcn MCP for component documentation

## Requirements Summary

### Functional Requirements

1. **Enable the disabled button** — The "Voir les transactions pour vérifier" button should become clickable after categorization completes
2. **Month selection** — User should be able to select which month(s) to review from the categorized months
3. **Transaction display** — Show transactions for the selected month in a modal/dialog (stays on import page)
4. **Inline editing** — Allow user to change category type and subcategory for any transaction
5. **Low-confidence highlighting** — Visually indicate transactions where AI had low confidence
6. **Return to results** — After reviewing, user returns to the results summary to finish import
7. **Scope limitation** — Only show transactions from the current import session, not historical data

### Data Available

After categorization, the following data is available in state:

```typescript
// state.categorizeResponse.months_processed contains:
{
  year: number;
  month: number;
  transactions_categorized: number;
  transactions_skipped: number;
  low_confidence_count: number;
  score: number;
  score_label: ScoreLabel;
}[]
```

### API Endpoints to Use

| Endpoint                     | Method | Purpose                                 |
| ---------------------------- | ------ | --------------------------------------- |
| `/api/months/{year}/{month}` | GET    | Fetch full transaction list for a month |
| `/api/transactions/{id}`     | PATCH  | Update transaction category             |

### Reusability Opportunities

- `TransactionEditModal` can be reused as-is for editing
- Modal patterns from shadcn/ui (Dialog, Sheet)
- Existing translations for category labels

### Scope Boundaries

**In Scope:**

- Enable the "Voir les transactions pour vérifier" button
- Modal/dialog showing months to review
- Transaction list display for selected month
- Category editing capability (reuse existing modal)
- Visual highlighting of low-confidence transactions
- Return flow to results summary

**Out of Scope:**

- Bulk editing multiple transactions at once
- Advanced filtering by confidence level
- Changes to backend API
- Reviewing old/historical transactions (only current import)
- New page routes (keep within import flow)
- Dashboard modifications

### Technical Considerations

- Keep state management within the existing `useReducer` pattern in `import-page-client.tsx`
- Reuse existing API client functions (`getMonthDetail`, `updateTransaction`)
- Maintain consistency with existing UI patterns and translations
- Transaction list may need pagination for large months (100+ transactions)

### UI/UX Considerations

- Modal should be large enough to display transaction list comfortably
- Consider using a Sheet (slide-in panel) vs Dialog for better space utilization
- Low-confidence badge should be subtle but noticeable
- Month selection could be tabs, cards, or dropdown depending on number of months
