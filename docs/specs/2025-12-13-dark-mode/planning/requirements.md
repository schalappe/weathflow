# Spec Requirements: Dark Mode

## Initial Description

Add a dark mode to the frontend.

## Requirements Discussion

### Questions & Answers

**Q1:** I assume you want a toggle-based approach where users can manually switch between light and dark themes. Is that correct, or should we also detect the user's system preference automatically?
**A:** Yes, user can switch between mode

**Q2:** I'm thinking the theme preference should persist across sessions (stored in localStorage). Should we also save it to the backend (user profile), or is client-side storage sufficient for this local-first app?
**A:** Not necessary, just frontend is good

**Q3:** I assume dark mode should apply to all existing pages (Dashboard, History, Import, Advice). Is there a specific page or component that should be prioritized, or should it be a full rollout?
**A:** Yes (full rollout)

**Q4:** For the color scheme, should we invert the current light theme, use a carefully designed dark palette, or follow shadcn/ui's built-in dark theme defaults?
**A:** I let use the best color

**Q5:** Where should the theme toggle be placed?
**A:** A button in the top navigation/header

**Q6:** Should there be a transition animation when switching themes?
**A:** No animation

**Q7:** What should be explicitly OUT of scope for this feature?
**A:** Just dark mode

### Existing Code References

None identified by user. To be discovered during specification writing phase.

### Follow-up Questions

None required - requirements are clear.

## Visual Assets

### Files Found

No visual assets provided.

### Visual Insights

N/A - Will use shadcn/ui's built-in dark theme system as the design foundation.

## Requirements Summary

### Functional Requirements

- Toggle button in top navigation/header to switch between light and dark themes
- Theme preference persisted in localStorage (client-side only)
- Dark mode applies to all existing pages: Dashboard, History, Import, Advice
- Instant theme switch (no animation)
- Use shadcn/ui's built-in dark theme system for consistent, accessible colors

### Reusability Opportunities

- shadcn/ui components have built-in dark mode support via Tailwind CSS
- Tailwind CSS dark mode classes (`dark:` prefix) are available
- Existing header/navigation component will host the toggle

### Scope Boundaries

**In Scope:**

- Theme toggle button in header
- Dark/light theme switching
- localStorage persistence
- Dark mode styling for all existing pages and components

**Out of Scope:**

- System preference detection (auto mode)
- Backend persistence of theme preference
- Custom color themes beyond light/dark
- Per-page theme settings
- Scheduled theme changes
- Transition animations

### Technical Considerations

- shadcn/ui uses CSS variables for theming - dark mode is typically enabled by adding `dark` class to `<html>` element
- Tailwind CSS dark mode should be configured in `tailwind.config.js` (likely already set up for shadcn/ui)
- Theme context or hook needed to manage state and localStorage sync
- All existing components should inherit dark mode automatically via Tailwind/shadcn
