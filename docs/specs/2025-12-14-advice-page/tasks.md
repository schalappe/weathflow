# Task Breakdown: Dedicated Advice Page

## Overview

Total Tasks: 12
Estimated Complexity: Low
Primary Stack: Next.js (Frontend only)

**Note:** This feature requires no backend changes. All API endpoints already exist.

## Task List

### Translations Layer

#### Task Group 1: Add Translation Keys

**Dependencies:** None

- [x] 1.0 Complete translations layer
  - [x] 1.1 Add navigation translation key
    - Add `t.nav.advice: "Conseils"` to translations.ts
  - [x] 1.2 Add advice page translation keys
    - Add `t.advicePage.title: "Conseils personnalisés"`
    - Add `t.advicePage.subtitle: "Recommandations IA basées sur vos habitudes de dépenses"`
    - Add `t.advicePage.empty.title: "Aucun mois disponible"`
    - Add `t.advicePage.empty.description: "Importez vos transactions pour recevoir des conseils personnalisés."`
    - Add `t.advicePage.empty.button: "Importer des transactions"`
    - Add `t.advicePage.retry: "Réessayer"`

**Acceptance Criteria:**

- All translation keys accessible via `t.nav.advice` and `t.advicePage.*`
- TypeScript type-checks pass

---

### Frontend Components Layer

#### Task Group 2: Create Advice Page Client Component

**Dependencies:** Task Group 1

- [x] 2.0 Complete advice page client component
  - [x] 2.1 Write 4 focused tests for AdvicePageClient
    - Test loading state renders skeleton
    - Test empty state shows import CTA when no months
    - Test error state shows error message with retry button
    - Test loaded state renders MonthSelector and AdvicePanel
  - [x] 2.2 Create `frontend/components/advice/advice-page-client.tsx`
    - Import existing `MonthSelector` from `@/components/dashboard/month-selector`
    - Import existing `AdvicePanel` from `@/components/history/advice-panel`
    - Implement useReducer with state: pageState, monthsList, selectedYear, selectedMonth, error
    - Implement actions: LOAD_START, MONTHS_LOADED, LOAD_ERROR, SELECT_MONTH
    - Reuse pattern from: `frontend/components/history/history-client.tsx`
  - [x] 2.3 Implement page states
    - Loading: Skeleton with header placeholder and content placeholder
    - Empty: Card with Lightbulb icon, message, and "Importer des transactions" button linking to /import
    - Error: Alert with error message and retry button
    - Loaded: Header with title/subtitle + MonthSelector + AdvicePanel
  - [x] 2.4 Implement data fetching effect
    - Fetch months list via `getMonthsList()` on mount
    - Auto-select most recent month (first in array) on success
    - Handle empty array (dispatch LOAD_ERROR with empty message)
  - [x] 2.5 Implement month change handler
    - Dispatch SELECT_MONTH action with year and month
    - AdvicePanel handles its own re-fetching via props change
    - Add `key` prop to AdvicePanel for clean remount: `key={\`${selectedYear}-${selectedMonth}\`}`
  - [x] 2.6 Ensure tests pass
    - Run: `cd frontend && bun test advice-page-client`

**Acceptance Criteria:**

- Component renders all four states correctly
- MonthSelector shows all months from API
- AdvicePanel receives correct year/month props
- Month changes trigger AdvicePanel re-fetch

---

#### Task Group 3: Create Advice Page Route

**Dependencies:** Task Group 2

- [x] 3.0 Complete advice page route
  - [x] 3.1 Create `frontend/app/advice/page.tsx`
    - Server component wrapper
    - Import ErrorBoundary from `@/components/ui/error-boundary`
    - Import AdvicePageClient from `@/components/advice/advice-page-client`
    - Reuse pattern from: `frontend/app/history/page.tsx`
  - [x] 3.2 Verify page loads at `/advice`
    - Start dev server: `cd frontend && bun dev`
    - Navigate to http://localhost:3000/advice
    - Confirm no console errors

**Acceptance Criteria:**

- Page accessible at `/advice` route
- ErrorBoundary catches any render errors
- Page loads without console errors

---

### Navigation Layer

#### Task Group 4: Add Navigation Link

**Dependencies:** Task Group 3

- [x] 4.0 Complete navigation integration
  - [x] 4.1 Update `frontend/app/layout.tsx`
    - Import `Lightbulb` icon from lucide-react
    - Add NavLink after History link: `<NavLink href="/advice" icon={<Lightbulb className="h-4 w-4" />}>{t.nav.advice}</NavLink>`
  - [x] 4.2 Verify navigation works
    - Click "Conseils" link from any page
    - Confirm navigation to /advice
    - Confirm active state styling when on /advice

**Acceptance Criteria:**

- "Conseils" link visible in navigation bar
- Link uses Lightbulb icon
- Link navigates to /advice correctly
- Active state shown when on advice page

---

### Cleanup Layer

#### Task Group 5: Remove AdvicePanel from History

**Dependencies:** Task Group 4

- [x] 5.0 Complete history page cleanup
  - [x] 5.1 Update `frontend/components/history/history-client.tsx`
    - Remove import: `import { AdvicePanel } from "./advice-panel";`
    - Remove AdvicePanel usage (lines 229-234 approximately)
  - [x] 5.2 Update history tests if needed
    - Check `frontend/__tests__/history/` for AdvicePanel references
    - Remove any tests that test AdvicePanel integration in history page
  - [x] 5.3 Verify history page still works
    - Navigate to /history
    - Confirm charts still render
    - Confirm no console errors
    - Confirm AdvicePanel no longer appears

**Acceptance Criteria:**

- History page loads without errors
- Charts still display correctly
- AdvicePanel no longer visible on history page
- No unused imports or dead code

---

### Testing Layer

#### Task Group 6: Final Test Review

**Dependencies:** Task Groups 1-5

- [x] 6.0 Review and fill critical gaps
  - [x] 6.1 Review tests from Task Group 2 (4 tests)
  - [x] 6.2 Identify critical gaps for advice page only
    - Focus on: month selection, state transitions, error handling
  - [x] 6.3 Write max 4 additional tests if gaps found
    - Test month selector integration
    - Test retry functionality
    - Test navigation from empty state to import page
  - [x] 6.4 Run all advice-related tests
    - Run: `cd frontend && bun test advice`
    - Verify all tests pass

**Acceptance Criteria:**

- All advice page tests pass (8 tests maximum)
- Critical user flows covered
- No regression in existing functionality

---

## Execution Order

1. **Task Group 1** (Translations) - Foundation for UI text
2. **Task Group 2** (Client Component) - Core page functionality
3. **Task Group 3** (Page Route) - Make page accessible
4. **Task Group 4** (Navigation) - Add to nav bar
5. **Task Group 5** (Cleanup) - Remove from history page
6. **Task Group 6** (Testing) - Verify everything works

## Files Summary

**Files to Create:**

- `frontend/components/advice/advice-page-client.tsx`
- `frontend/app/advice/page.tsx`
- `frontend/__tests__/advice/advice-page-client.test.tsx`

**Files to Modify:**

- `frontend/lib/translations.ts`
- `frontend/app/layout.tsx`
- `frontend/components/history/history-client.tsx`

**No Changes Required:**

- Backend (all APIs exist)
- `frontend/components/history/advice-panel.tsx` (reused as-is)
- `frontend/components/dashboard/month-selector.tsx` (reused as-is)
- `frontend/lib/api-client.ts` (all functions exist)
