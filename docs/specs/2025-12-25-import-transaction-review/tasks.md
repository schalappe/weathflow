# Task Breakdown: Import Transaction Review

## Overview

Total Task Groups: 4
Total Tasks: 16
Estimated Duration: 3-4 hours

This is a **frontend-only** feature. No backend changes required.

## Task List

### Infrastructure Layer

#### Task Group 1: Setup and Types

**Dependencies:** None

- [ ] 1.0 Complete infrastructure setup
  - [ ] 1.1 Add shadcn/ui Sheet component via CLI (`bunx shadcn@latest add sheet`)
  - [ ] 1.2 Add new action types to `ImportAction` in `frontend/types/index.ts`
  - [ ] 1.3 Add `isReviewSheetOpen: boolean` to `ImportState` interface
  - [ ] 1.4 Add French translations for review UI in `frontend/lib/translations.ts`

**Acceptance Criteria:**

- Sheet component available at `@/components/ui/sheet`
- TypeScript compiles without errors
- New translations accessible via `t.review.*`

**Files to modify:**

- `frontend/types/index.ts` — Add `OPEN_REVIEW_SHEET` and `CLOSE_REVIEW_SHEET` actions
- `frontend/lib/translations.ts` — Add review section translations

**New translations needed:**

```typescript
review: {
  title: "Vérifier les transactions",
  subtitle: "Vérifiez et corrigez les catégories si nécessaire",
  lowConfidence: "à faible confiance",
  noTransactions: "Aucune transaction pour ce mois",
  loading: "Chargement des transactions...",
  close: "Fermer",
  transactions: "transactions",
  of: "dont",
}
```

---

### State Integration Layer

#### Task Group 2: Import State Machine

**Dependencies:** Task Group 1

- [ ] 2.0 Complete state machine integration
  - [ ] 2.1 Add reducer cases for `OPEN_REVIEW_SHEET` and `CLOSE_REVIEW_SHEET` in `import-page-client.tsx`
  - [ ] 2.2 Update `initialState` with `isReviewSheetOpen: false`
  - [ ] 2.3 Add `handleOpenReviewSheet` and `handleCloseReviewSheet` callbacks
  - [ ] 2.4 Verify state transitions work (manual testing)

**Acceptance Criteria:**

- Dispatching `OPEN_REVIEW_SHEET` sets `isReviewSheetOpen: true`
- Dispatching `CLOSE_REVIEW_SHEET` sets `isReviewSheetOpen: false`
- No TypeScript errors

**Files to modify:**

- `frontend/components/import/import-page-client.tsx` — Reducer cases + callbacks

---

### UI Components Layer

#### Task Group 3: Transaction Review Components

**Dependencies:** Task Group 2

- [ ] 3.0 Complete UI components
  - [ ] 3.1 Create `TransactionReviewList` component (`frontend/components/import/transaction-review-list.tsx`)
  - [ ] 3.2 Create `TransactionReviewSheet` component (`frontend/components/import/transaction-review-sheet.tsx`)
  - [ ] 3.3 Integrate `TransactionEditModal` inside sheet
  - [ ] 3.4 Wire up API calls (`getMonthDetail`, `updateTransaction`)
  - [ ] 3.5 Verify component rendering and interactions (manual testing)

**Acceptance Criteria:**

- Sheet slides in from right with correct width
- Tabs display all categorized months with localized names
- Low-confidence badge shows on tabs with `low_confidence_count > 0`
- Transaction list displays with Date, Description, Amount, Category columns
- Clicking a transaction opens edit modal
- Saving updates reflects in the list immediately
- Closing sheet returns to results summary

**Files to create:**

- `frontend/components/import/transaction-review-list.tsx` (~100 lines)
- `frontend/components/import/transaction-review-sheet.tsx` (~150 lines)

**Component props:**

```typescript
// TransactionReviewList
interface TransactionReviewListProps {
  transactions: TransactionResponse[];
  lowConfidenceCount: number;
  isLoading: boolean;
  onTransactionClick: (transaction: TransactionResponse) => void;
}

// TransactionReviewSheet
interface TransactionReviewSheetProps {
  isOpen: boolean;
  onClose: () => void;
  monthResults: MonthResult[];
}
```

---

### Integration Layer

#### Task Group 4: Final Integration

**Dependencies:** Task Group 3

- [ ] 4.0 Complete feature integration
  - [ ] 4.1 Modify `ResultsSummary` to accept `onReviewClick` prop
  - [ ] 4.2 Enable the "Voir les transactions" button (remove `disabled`, remove tooltip)
  - [ ] 4.3 Render `TransactionReviewSheet` in `ImportPageClient`
  - [ ] 4.4 Pass props and wire callbacks between components
  - [ ] 4.5 End-to-end manual testing of complete flow

**Acceptance Criteria:**

- "Voir les transactions pour vérifier" button is enabled and clickable
- Clicking button opens review sheet
- Full flow works: button → sheet → select month → view transactions → edit → save → close
- No console errors
- TypeScript compiles without errors

**Files to modify:**

- `frontend/components/import/results-summary.tsx` — Add `onReviewClick` prop, enable button
- `frontend/components/import/import-page-client.tsx` — Render sheet, pass callbacks

---

## Execution Order

```text
1. Infrastructure (Task Group 1) — ~30 min
   └── shadcn Sheet, types, translations

2. State Integration (Task Group 2) — ~20 min
   └── Reducer actions, callbacks

3. UI Components (Task Group 3) — ~90 min
   └── TransactionReviewList, TransactionReviewSheet

4. Final Integration (Task Group 4) — ~40 min
   └── Wire everything, enable button, test
```

## Testing Strategy

This feature is **UI-focused** with no new business logic. Testing approach:

| Type                | Approach                       |
| ------------------- | ------------------------------ |
| Component rendering | Manual verification            |
| State transitions   | Manual dispatch testing        |
| API integration     | Uses existing tested endpoints |
| User flow           | End-to-end manual testing      |

**Manual test checklist (Task 4.5):**

- [ ] Import a CSV and complete categorization
- [ ] Click "Voir les transactions pour vérifier" — sheet opens
- [ ] Verify tabs show all categorized months
- [ ] Verify low-confidence badge appears on relevant tabs
- [ ] Click different tabs — transactions load for each month
- [ ] Click a transaction — edit modal opens
- [ ] Change category and save — list updates
- [ ] Close sheet — returns to results summary
- [ ] Click "Terminer l'import" — navigates to dashboard

## Notes

- **No backend changes** — All data already available via existing API
- **Reuse existing components** — `TransactionEditModal`, `CATEGORY_STYLES`
- **State isolation** — Sheet manages its own state (transactions, loading, editing)
- **Error handling** — Use existing patterns from dashboard
