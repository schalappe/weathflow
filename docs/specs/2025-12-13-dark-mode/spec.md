# Specification: Dark Mode

## Goal

Add a theme toggle to the frontend that allows users to switch between light and dark modes, with the preference persisted in localStorage for consistent experience across sessions.

## User Stories

- As a user, I want to toggle between light and dark themes so that I can use the app comfortably in different lighting conditions
- As a user, I want my theme preference to persist so that I don't have to re-select it every time I visit the app

## Specific Requirements

**Theme Toggle Button:**

- Icon button placed in the top navigation header, after the navigation links
- Uses Moon icon when in light mode (indicates "switch to dark")
- Uses Sun icon when in dark mode (indicates "switch to light")
- Uses Button component with `variant="ghost"` and `size="icon-sm"`
- Accessible with descriptive `aria-label`

**Theme Switching:**

- Instant theme switch (no animation)
- Applies `.dark` class to `<html>` element to activate dark mode
- All existing pages automatically adapt via CSS variables
- No flash of wrong theme on page load (prevented by inline script)

**State Persistence:**

- Theme preference stored in localStorage under key `'theme'`
- Values: `'light'` or `'dark'`
- Default to light mode if no preference is stored
- Client-side only (no backend persistence)

**Theme Provider:**

- React Context provider wrapping the entire application
- Provides `theme` value and `toggleTheme` function
- Custom `useTheme()` hook for consuming theme context

## Visual Design

No mockups provided. Design will follow shadcn/ui's built-in dark theme system which uses CSS variables with oklch color space for accessible, consistent colors.

## Existing Code to Leverage

**Dark Mode CSS Variables — `frontend/app/globals.css`**

- What it does: Defines complete color palettes for both light (`:root`) and dark (`.dark`) modes
- How to reuse: Already fully implemented - just needs `.dark` class applied to `<html>`
- Key details: Lines 56-89 (light), lines 91-123 (dark), Tailwind v4 custom variant on line 4

**Button Component — `frontend/components/ui/button.tsx`**

- What it does: CVA-based button with multiple variants and sizes
- How to reuse: Import and use with `variant="ghost"` and `size="icon-sm"` for toggle
- Key methods: Standard Button props interface

**NavBar Component — `frontend/app/layout.tsx`**

- What it does: Sticky header with logo and navigation links (lines 23-52)
- How to reuse: Add ThemeToggle after navigation links
- Key details: Currently inline in layout, uses flex layout

**Hooks Directory — `frontend/lib/hooks/`**

- What it does: Contains custom hooks (e.g., `use-debounce.ts`)
- How to reuse: Follow same naming pattern for `use-theme.ts`

**Lucide React Icons:**

- What it does: Icon library already in use throughout codebase
- How to reuse: Import Sun and Moon icons
- Key pattern: `<Moon className="h-4 w-4" />`

## Architecture Approach

**Component Design:**

- `ThemeProvider` (`components/ui/theme-provider.tsx`): Context provider managing theme state, localStorage sync, and `.dark` class application
- `ThemeToggle` (`components/ui/theme-toggle.tsx`): Icon button that consumes context and triggers toggle
- `useTheme` hook (`lib/hooks/use-theme.ts`): Context consumer hook with error boundary

**Data Flow:**

- Entry: User clicks ThemeToggle button
- State update: `toggleTheme()` flips theme state in ThemeProvider
- Side effects: useEffect applies/removes `.dark` class on `<html>`, persists to localStorage
- Output: CSS variables automatically swap colors, all components re-render with new theme

**Integration Points:**

- `layout.tsx`: Wrap body contents with ThemeProvider, add ThemeToggle to NavBar
- Flash prevention: Inline script in `<head>` reads localStorage and applies `.dark` class before React hydrates
- `<html>` element: Add `suppressHydrationWarning` to handle class mismatch between server and client

## Out of Scope

- System preference detection (auto mode based on OS settings)
- Backend persistence of theme preference
- Custom color themes beyond light/dark
- Per-page theme settings
- Scheduled theme changes (time-based switching)
- Transition animations between themes
- Theme selection dropdown (only toggle button)
- Color customization UI
