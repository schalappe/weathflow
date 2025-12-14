# Implementation: Dedicated Advice Page (Task Groups 1-6)

**Date:** 2025-12-14
**Task Groups:** 1-6 (All)

## Summary

Implemented a dedicated advice page at `/advice` route that allows users to view, generate, and regenerate personalized financial advice for any month with imported data. The implementation follows the Clean Refactoring architecture approach, extracting `AdvicePanelContent` as a reusable component.

## Architecture Approach

**Selected:** Clean Refactoring (Approach B)

**Rationale:** User requested hiding the AdvicePanel header on the new page while keeping it on the history page. Rather than adding a prop flag, we extracted the content into a separate component:

- `AdvicePanelContent` - All logic and rendering (headless)
- `AdvicePanel` - Card wrapper with header (for history page)
- `AdvicePageClient` - Page-level state + MonthSelector + AdvicePanelContent

**Trade-offs:**
- Clean separation of concerns
- No prop pollution
- Slightly more files but clearer intent

## Files Modified

- `frontend/lib/translations.ts` — Added `t.nav.advice` and `t.advicePage.*` translation keys
- `frontend/app/layout.tsx` — Added Lightbulb nav link for `/advice` route
- `frontend/components/history/history-client.tsx` — Removed AdvicePanel import and usage
- `frontend/components/history/advice-panel.tsx` — Refactored to thin wrapper using AdvicePanelContent

## Files Created

- `frontend/components/history/advice-panel-content.tsx` — Extracted content component with all logic
- `frontend/components/advice/advice-page-client.tsx` — New page client component with month selection
- `frontend/app/advice/page.tsx` — Server component wrapper with ErrorBoundary
- `frontend/__tests__/advice/advice-page-client.test.tsx` — 7 tests covering all page states

## Key Details

### State Management Pattern

Used `useReducer` with discriminated union actions consistent with existing patterns:
- `LOAD_START` - Begin loading months
- `MONTHS_LOADED` - Months fetched, auto-select most recent
- `LOAD_ERROR` - Handle fetch errors
- `SELECT_MONTH` - User changed month selection

### Component Composition

```text
AdvicePageClient
├── MonthSelector (from dashboard)
└── Card
    └── AdvicePanelContent
        ├── AdviceSkeletonLoader
        ├── EmptyState
        ├── ErrorState
        └── AdviceContent
```

### Key Implementation Details

1. **Auto-selection:** Most recent month (first in array) is auto-selected on load
2. **Key prop:** `AdvicePanelContent` uses `key={year-month}` for clean remount on month change
3. **Error handling:** Distinguishes network errors (retry) from data errors (import link)
4. **Translations:** All UI text uses centralized French translations

## Integration Points

- Reuses `MonthSelector` from `@/components/dashboard/month-selector`
- Reuses `getMonthsList()` from `@/lib/api-client`
- Follows same reducer pattern as `history-client.tsx` and `dashboard-client.tsx`
- Navigation added after History link with Lightbulb icon

## Testing Notes

7 tests written for `AdvicePageClient`:
1. Loading state renders skeleton
2. Empty state shows import CTA
3. Error state shows retry button
4. Loaded state renders MonthSelector and AdvicePanel
5. Retry functionality reloads months
6. Auto-selects most recent month
7. Month selection updates AdvicePanel

Existing `AdvicePanel` tests (31 tests) continue to pass as the component API is unchanged.
