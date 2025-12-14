# Spec Requirements: Advice Page

## Initial Description

The current history page only allows seeing advice for the current month but not to navigate between old and new advice. Create a new dedicated page for advice. This page should allow to regenerate/generate advice for the current and n-1 month.

## Requirements Discussion

### Questions & Answers

**Q1:** I assume you want to display advice for one month at a time with navigation to switch between months. Is that correct, or would you prefer a side-by-side comparison view showing both current and previous month advice?
**A:** Yes, that is it. One month at a time with navigation to switch between months.

**Q2:** For the month selector, I'm thinking a dropdown showing only months that have imported data. Should it also allow selecting months without advice yet (showing a "generate" prompt), or only months with existing advice?
**A:** Allow selecting months without advice yet.

**Q3:** I assume the new page should be accessible at `/advice` with a link in the main navigation. Is that correct, or should it remain accessible from the History page with a "View All Advice" button?
**A:** Yes, accessible at /advice. Advice should all be visible on advice page.

**Q4:** Should the page automatically default to showing the most recent month's advice? When the user switches months, should they see a loading state while fetching that month's advice?
**A:** Yes to both. Default to most recent month, and show loading state when switching months.

**Q5:** I assume you want to keep the existing AdvicePanel on the History page as a preview/summary, but add a "View Details" link to the new page. Is that correct, or should we remove the AdvicePanel from History entirely?
**A:** No, remove the AdvicePanel from History entirely.

**Q6:** What should be explicitly OUT OF SCOPE for this feature?
**A:** Only work on advice page.

### Existing Code References

- `frontend/components/history/advice-panel.tsx` - Existing advice display component to reuse
- `frontend/components/history/period-selector.tsx` - Month selector pattern reference
- `backend/app/api/advice.py` - Existing API endpoints for advice
- `backend/app/services/advice/service.py` - Advice generation service

### Follow-up Questions

None required - requirements are clear.

## Visual Assets

### Files Found

No visual assets provided.

### Visual Insights

N/A

## Requirements Summary

### Functional Requirements

- Create a new dedicated page at `/advice` route
- Display advice for one month at a time
- Month selector dropdown showing all months with imported data (including months without advice)
- Default to the most recent month on page load
- Show loading state when switching between months
- Generate advice for months that don't have advice yet
- Regenerate advice for months that already have advice
- Reuse existing `AdvicePanel` component for advice display

### UI Changes

- Add `/advice` to main navigation
- Remove `AdvicePanel` from History page (`history-client.tsx`)
- Create new Advice page with month selector + advice panel

### Reusability Opportunities

- Reuse `AdvicePanel` component from `frontend/components/history/advice-panel.tsx`
- Adapt month selector pattern from `PeriodSelector` component
- Use existing API client functions: `getAdvice`, `generateAdvice`
- Use existing `getMonthsHistory` to fetch available months

### Scope Boundaries

**In Scope:**

- New `/advice` page with month navigation
- Month selector for months with imported data
- Advice display, generation, and regeneration
- Remove AdvicePanel from History page

**Out of Scope:**

- Side-by-side month comparison
- Exporting advice
- Filtering by problem area type
- Any changes to other pages beyond removing AdvicePanel from History

### Technical Considerations

- Backend API already supports advice for any month (no changes needed)
- Need to fetch list of available months (can use existing history endpoint)
- State management for selected month and advice data
- Handle empty state when no months have data yet
