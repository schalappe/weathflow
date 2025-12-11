# Task Breakdown: Advice Panel UI

## Overview

Total Tasks: 18
Estimated Complexity: Medium
Primary Stack: Next.js + TypeScript + shadcn/ui

## Task List

### Foundation Layer

#### Task Group 1: TypeScript Types and API Client

**Dependencies:** None

- [x] 1.0 Complete foundation layer
  - [x] 1.1 Add advice TypeScript types to `types/index.ts`
    - Add `ProblemArea` interface: category (string), amount (number), trend (string)
    - Add `AdviceData` interface: analysis, problem_areas, recommendations, encouragement
    - Add `GetAdviceResponse` interface: success, advice, generated_at, exists
    - Add `GenerateAdviceResponse` interface: success, advice, generated_at, was_cached
    - Mirror backend models from `backend/app/responses/advice.py`
  - [x] 1.2 Add `getAdvice()` function to `lib/api-client.ts`
    - GET request to `/api/advice/{year}/{month}`
    - Follow existing pattern: try/catch for network, extractErrorMessage, safeParseJson
    - Return `Promise<GetAdviceResponse>`
  - [x] 1.3 Add `generateAdvice()` function to `lib/api-client.ts`
    - POST request to `/api/advice/generate`
    - Body: `{ year, month, regenerate }`
    - Headers: `Content-Type: application/json`
    - Return `Promise<GenerateAdviceResponse>`
  - [x] 1.4 Add `formatAdviceTimestamp()` helper to `lib/utils.ts`
    - Return relative time for recent advice (< 24h): "il y a X heures"
    - Return absolute date for older advice: "15 octobre 2025"
    - Use French locale formatting

**Acceptance Criteria:**

- Types compile without errors
- API functions follow existing patterns
- Timestamp formatter handles edge cases

---

### Component Layer

#### Task Group 2: AdvicePanel State Management

**Dependencies:** Task Group 1

- [x] 2.0 Complete state management
  - [x] 2.1 Create `advice-panel.tsx` with state types and reducer
    - Define `AdvicePanelState` type: 'loading' | 'loaded' | 'empty' | 'error'
    - Define `AdviceState` interface: panelState, advice, generatedAt, isRegenerating, error
    - Create discriminated union `AdviceAction` type with 7 action types
    - Implement `adviceReducer` function with all state transitions
  - [x] 2.2 Implement data fetching useEffect
    - Fetch on mount and when year/month props change
    - Use `isMounted` cleanup flag to prevent memory leaks
    - Dispatch FETCH_START, FETCH_SUCCESS, FETCH_EMPTY, or FETCH_ERROR
  - [x] 2.3 Implement generate/regenerate handler
    - Use `useCallback` to memoize handler
    - Dispatch REGENERATE_START, then call generateAdvice API
    - Dispatch REGENERATE_SUCCESS or REGENERATE_ERROR based on result
    - Pass `regenerate: true` when panelState is 'loaded'

**Acceptance Criteria:**

- Reducer handles all state transitions correctly
- useEffect cleanup prevents memory leaks
- Regenerate keeps existing advice visible during loading

---

#### Task Group 3: AdvicePanel Sub-components

**Dependencies:** Task Group 2

- [x] 3.0 Complete sub-components
  - [x] 3.1 Create `AdviceSkeletonLoader` sub-component
    - Use animate-pulse with bg-slate-200 rounded divs
    - Mimic layout of loaded state (3 sections with varying widths)
    - Follow existing skeleton patterns from dashboard
  - [x] 3.2 Create `EmptyState` sub-component
    - Props: `onGenerate`, `isLoading`
    - Centered layout with Sparkles icon in rounded bg-slate-100
    - "Aucun conseil disponible" heading
    - Description text about generating advice
    - Button with Loader2 spinner when loading
  - [x] 3.3 Create `ErrorState` sub-component
    - Props: `error`, `onRetry`
    - Use Alert with variant="destructive"
    - AlertCircle icon + error message + retry Button
    - Follow pattern from history-client.tsx error state
  - [x] 3.4 Create `ProblemAreaItem` sub-component
    - Props: `area: ProblemArea`, `index: number`
    - Display: index, category, formatCurrency(amount), trend
    - Trend color: red for +, green for -, gray for neutral
    - Use `cn()` for conditional className

**Acceptance Criteria:**

- Sub-components render correctly in isolation
- Color coding matches spec (red=bad, green=good)
- Empty and error states follow existing patterns

---

#### Task Group 4: AdvicePanel Content Display

**Dependencies:** Task Group 3

- [x] 4.0 Complete content display
  - [x] 4.1 Create `AdviceContent` sub-component structure
    - Props: advice, generatedAt, onRegenerate, isRegenerating, regenerateError
    - Use space-y-6 for section spacing
    - Add border-t separator before footer
  - [x] 4.2 Implement Analysis section
    - BarChart3 icon + "Analyse des tendances" heading
    - Display advice.analysis as paragraph text
    - Use text-sm text-slate-600 styling
  - [x] 4.3 Implement Problem Areas section
    - AlertTriangle icon + "Points d'attention" heading
    - Map over advice.problem_areas with ProblemAreaItem
    - Conditionally render only if problem_areas.length > 0
  - [x] 4.4 Implement Recommendations section
    - CheckCircle2 icon + "Recommandations" heading
    - Ordered list with list-decimal list-inside
    - Map over advice.recommendations
  - [x] 4.5 Implement Encouragement section
    - Sparkles icon + "Encouragement" heading
    - Display advice.encouragement as paragraph
  - [x] 4.6 Implement footer with timestamp and regenerate button
    - Left: timestamp using formatAdviceTimestamp()
    - Right: Button variant="outline" size="sm"
    - Loader2 spinner when isRegenerating
    - Show regenerateError as inline Alert if present

**Acceptance Criteria:**

- All four advice sections display correctly
- Icons render from lucide-react
- Regenerate button shows loading state

---

#### Task Group 5: AdvicePanel Main Component

**Dependencies:** Task Group 4

- [x] 5.0 Complete main component assembly
  - [x] 5.1 Assemble AdvicePanel with Card container
    - Card with CardHeader and CardTitle "Conseils Personnalisés"
    - CardContent wrapping state-based rendering
    - Accept className prop with cn() merge
  - [x] 5.2 Implement conditional rendering based on panelState
    - loading: render AdviceSkeletonLoader
    - empty: render EmptyState with handlers
    - error: render ErrorState with handlers
    - loaded: render AdviceContent with all props
  - [x] 5.3 Export AdvicePanel component
    - Named export from advice-panel.tsx
    - Ensure all imports are correct (lucide-react icons, shadcn components)

**Acceptance Criteria:**

- Component renders correct state based on panelState
- All sub-components receive correct props
- Component is properly exported

---

### Integration Layer

#### Task Group 6: History Page Integration

**Dependencies:** Task Group 5

- [x] 6.0 Complete integration
  - [x] 6.1 Import AdvicePanel in history-client.tsx
    - Add import statement at top of file
    - Import from './advice-panel'
  - [x] 6.2 Add AdvicePanel below charts grid
    - Render inside loaded/loading state block (where months.length > 0)
    - Pass most recent month: `months[months.length - 1].year` and `.month`
    - Add className="mt-6" for spacing from charts
  - [x] 6.3 Verify end-to-end flow manually
    - Navigate to History page
    - Verify loading state appears
    - Verify empty/loaded state based on API response
    - Test generate and regenerate buttons

**Acceptance Criteria:**

- AdvicePanel appears below charts on History page
- Component receives correct year/month props
- No console errors during rendering

---

### Testing Layer

#### Task Group 7: Component Tests

**Dependencies:** Task Group 6

- [x] 7.0 Complete component tests
  - [x] 7.1 Write 6 focused tests for AdvicePanel
    - Test 1: Shows skeleton loader in loading state
    - Test 2: Shows empty state when exists=false
    - Test 3: Shows advice content when loaded
    - Test 4: Shows error state with retry button on error
    - Test 5: Trend colors are correct (red for +, green for -)
    - Test 6: Regenerate button shows spinner while loading
  - [x] 7.2 Write 2 tests for API client functions
    - Test 1: getAdvice returns typed response
    - Test 2: generateAdvice sends correct payload
  - [x] 7.3 Run feature-specific tests only
    - Run tests for advice-panel component
    - Run tests for api-client advice functions
    - Verify all 8 tests pass

**Acceptance Criteria:**

- All 8 tests pass
- Tests cover critical component behaviors
- Tests use mocked API responses

---

## Execution Order

1. **Task Group 1** (Foundation) - Types and API client needed first
2. **Task Group 2** (State) - State management before UI
3. **Task Group 3** (Sub-components) - Build blocks before assembly
4. **Task Group 4** (Content) - Main content display
5. **Task Group 5** (Main) - Assemble complete component
6. **Task Group 6** (Integration) - Connect to History page
7. **Task Group 7** (Testing) - Verify everything works

## Notes

- **No backend work needed** - Advice API already complete (Feature 15)
- **shadcn/ui components available** - Card, Button, Alert, Skeleton already in project
- **Follow existing patterns** - history-client.tsx has the reducer/useEffect pattern to follow
- **French UI text** - All user-facing strings in French as per requirements
