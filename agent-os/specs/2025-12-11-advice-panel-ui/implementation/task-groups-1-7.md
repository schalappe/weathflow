# Implementation: Advice Panel UI (Task Groups 1-7)

**Date:** 2025-12-11
**Task Groups:** 1-7 (Complete Feature)
**Implementer:** implement-task command

## Summary

Implemented the complete Advice Panel UI feature, which displays AI-generated financial advice on the History page. The component fetches existing advice via GET `/api/advice/{year}/{month}` and allows users to generate or regenerate advice via POST `/api/advice/generate`. The panel shows four advice sections (Analysis, Problem Areas, Recommendations, Encouragement) with proper state management for loading, empty, error, and loaded states.

## Architecture Approach

**Selected:** Minimal approach - single `advice-panel.tsx` file with all logic.

**Rationale:**
- Matches existing `history-client.tsx` pattern in the codebase
- Component is self-contained (~380 lines) and doesn't warrant extraction
- Single file is easier to navigate and maintain for this scope
- Sub-components are internal functions for readability, not separate files

## Files Modified

- `frontend/types/index.ts` - Added advice-related TypeScript types (ProblemArea, AdviceData, GetAdviceResponse, GenerateAdviceResponse)
- `frontend/lib/api-client.ts` - Added `getAdvice()` and `generateAdvice()` functions following existing patterns
- `frontend/lib/utils.ts` - Added `formatAdviceTimestamp()` helper with French locale support
- `frontend/components/history/history-client.tsx` - Integrated AdvicePanel below charts grid
- `frontend/__tests__/utils/test-factories.ts` - Added `createMockAdviceData()` factory function

## Files Created

- `frontend/components/history/advice-panel.tsx` - Main AdvicePanel component with state management, sub-components (AdviceSkeletonLoader, EmptyState, ErrorState, ProblemAreaItem, AdviceContent), and all rendering logic
- `frontend/__tests__/history/advice-panel.test.tsx` - 10 component tests covering all states and interactions
- `frontend/__tests__/lib/api-client-advice.test.ts` - 8 API client function tests

## Key Implementation Details

### State Management
- Uses `useReducer` with discriminated union actions for type-safe state transitions
- 4 panel states: `loading`, `loaded`, `empty`, `error`
- Separate `isRegenerating` flag preserves existing advice during regeneration
- `isMounted` cleanup flag prevents memory leaks in useEffect

### Trend Color Coding
- Positive trends (`+20%`) = red (spending increased = bad)
- Negative trends (`-15%`) = green (spending decreased = good)
- Neutral trends = gray

### Timestamp Formatting
- < 1 minute: "a l'instant"
- < 1 hour: "il y a X minutes"
- < 24 hours: "il y a X heures"
- >= 24 hours: absolute date in French locale ("11 decembre 2025")

### French Locale
All user-facing text is in French:
- "Conseils Personnalises" (card title)
- "Aucun conseil disponible" (empty state)
- "Generer des conseils" / "Regenerer" (buttons)
- "Analyse des tendances", "Points d'attention", "Recommandations", "Encouragement" (sections)

## Integration Points

### History Page Integration
```tsx
// In history-client.tsx, after charts grid
{state.months.length > 0 && (
  <AdvicePanel
    year={state.months[state.months.length - 1].year}
    month={state.months[state.months.length - 1].month}
  />
)}
```

The AdvicePanel receives the most recent month from the history data and manages its own state independently.

### API Endpoints Used
- `GET /api/advice/{year}/{month}` - Fetch existing advice
- `POST /api/advice/generate` - Generate new advice (with `regenerate: true` to replace cached)

## Testing Notes

### Component Tests (10 tests)
1. Shows skeleton loader in loading state
2. Shows empty state when exists=false
3. Shows advice content when loaded
4. Shows error state with retry button on error
5. Trend colors are correct (red for +, green for -)
6. Regenerate button shows spinner while loading
7. Generates advice when empty state button clicked
8. Regenerates advice when loaded state button clicked
9. Retries fetch when error retry button clicked
10. Refetches advice when year/month props change

### API Client Tests (8 tests)
1. getAdvice returns typed response on success
2. getAdvice returns exists=false when no advice
3. getAdvice throws on network failure
4. getAdvice throws on API error response
5. generateAdvice sends correct payload with regenerate=false
6. generateAdvice sends correct payload with regenerate=true
7. generateAdvice returns typed response on success
8. generateAdvice throws on errors

### Test Utilities
- `createMockAdviceData()` factory function added to test-factories.ts
- Uses `vi.mock()` to isolate API client from component tests
