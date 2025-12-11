# Specification: Advice Panel UI

## Goal

Build an advice display component that shows AI-generated financial analysis, problem areas, recommendations, and encouragement on the History page, with a button to regenerate new advice.

## User Stories

- As a user, I want to see personalized advice based on my last 3 months of spending so that I can improve my Money Map score.
- As a user, I want to regenerate advice when my situation changes so that I get updated recommendations.

## Specific Requirements

**AdvicePanel Component:**

- Create `frontend/components/history/advice-panel.tsx` as a self-contained component
- Accept props: `year`, `month`, `className?`
- Use `useReducer` for state management with discriminated union actions
- Fetch advice on mount and when `year`/`month` props change
- Use `isMounted` cleanup flag in useEffect to prevent memory leaks

**Component States:**

- Loading: Show skeleton loader while fetching advice
- Empty: Show call-to-action when `exists: false` from API
- Loaded: Display all four advice sections with regenerate button
- Error: Show Alert with error message and retry button
- Regenerating: Keep existing advice visible, show spinner on button

**Advice Display Sections:**

- Analysis: Icon + heading + paragraph text
- Problem Areas: Numbered list with category, amount (EUR), trend percentage
- Recommendations: Numbered list of actionable suggestions
- Encouragement: Motivational closing message
- Use section icons: BarChart3, AlertTriangle, CheckCircle2, Sparkles from lucide-react

**Trend Color Coding:**

- Red (`text-red-600`) for positive trends (e.g., "+20%" - spending increased, bad)
- Green (`text-green-600`) for negative trends (e.g., "-15%" - spending decreased, good)
- Gray (`text-slate-500`) for neutral (0%)

**Regenerate Button:**

- Show "Générer des conseils" in empty state
- Show "Régénérer" in loaded state (outline variant, sm size)
- Disable button and show Loader2 spinner during regeneration
- Call API with `regenerate: true` when advice already exists

**Timestamp Display:**

- Show relative time for recent advice (e.g., "il y a 2 heures")
- Show absolute date for older advice (e.g., "15 octobre 2025")
- Display below content, left-aligned, with muted text style

**Error Handling:**

- Network errors: "Unable to connect to server..."
- API errors: Display message from server response
- Regenerate errors: Show inline Alert without clearing existing advice
- All errors include retry/regenerate action

**API Client Functions:**

- Add `getAdvice(year, month)` to `lib/api-client.ts`
- Add `generateAdvice(year, month, regenerate)` to `lib/api-client.ts`
- Follow existing patterns: try/catch for network, extractErrorMessage, safeParseJson

**TypeScript Types:**

- Add `ProblemArea`, `AdviceData`, `GetAdviceResponse`, `GenerateAdviceResponse` to `types/index.ts`
- Mirror backend response models from `backend/app/responses/advice.py`

## Existing Code to Leverage

**history-client.tsx - `frontend/components/history/history-client.tsx`**

- What it does: Main History page component with useReducer state machine
- How to reuse: Follow same reducer pattern, action types, useEffect cleanup
- Key methods: `historyReducer`, loading/error/empty state rendering patterns

**Card Components - `frontend/components/ui/card.tsx`**

- What it does: Composable Card with CardHeader, CardTitle, CardContent, CardFooter
- How to reuse: Import directly for AdvicePanel container
- Key exports: `Card`, `CardHeader`, `CardTitle`, `CardContent`

**Button Component - `frontend/components/ui/button.tsx`**

- What it does: Button with variants (default, outline, destructive) and sizes (sm, default, lg)
- How to reuse: Import directly, use variant="outline" size="sm" for regenerate
- Key exports: `Button`

**Alert Component - `frontend/components/ui/alert.tsx`**

- What it does: Alert banner with variant="destructive" for errors
- How to reuse: Import directly for error state display
- Key exports: `Alert`, `AlertDescription`

**API Client - `frontend/lib/api-client.ts`**

- What it does: Centralized API functions with consistent error handling
- How to reuse: Add getAdvice/generateAdvice following existing pattern
- Key methods: `extractErrorMessage`, `safeParseJson`, `getErrorMessage`

## Architecture Approach

**Component Design:**

- Self-contained AdvicePanel manages its own state (no coupling to History page state)
- useReducer with 5 states: loading, loaded, empty, error + isRegenerating flag
- Sub-components: AdviceSkeletonLoader, EmptyState, ErrorState, AdviceContent, ProblemAreaItem

**Data Flow:**

- Props (year, month) → useEffect triggers fetch → dispatch actions → render based on state
- Generate button → dispatch REGENERATE_START → API call → dispatch success/error
- State transitions: loading→loaded/empty/error, regenerating keeps loaded visible

**Integration Points:**

- Import AdvicePanel in history-client.tsx
- Render below charts grid when months.length > 0
- Pass most recent month: `months[months.length - 1].year/month`

## Out of Scope

- Advice history (viewing previous months' advice)
- Advice comparison across months
- Export advice to PDF/text
- Push notifications for new advice
- Auto-generate advice on page load
- Collapsible/expandable panel
- Advice caching on frontend
- Printing advice
- Sharing advice
- Multi-language support (French only)
