# Task Breakdown: Dark Mode

## Overview

Total Tasks: 10
Estimated Complexity: Low
Primary Stack: Next.js + React (Frontend-only)

## Task List

### Theme Infrastructure

#### Task Group 1: Theme Provider and Hook

**Dependencies:** None

- [ ] 1.0 Complete theme infrastructure
  - [ ] 1.1 Write 3 focused tests for theme functionality
    - Test ThemeProvider renders children
    - Test useTheme returns theme value and toggleTheme function
    - Test useTheme throws error when used outside ThemeProvider
  - [ ] 1.2 Create ThemeProvider component (`components/ui/theme-provider.tsx`)
    - Export `Theme` type (`'light' | 'dark'`)
    - Export `ThemeContext` with `theme` and `toggleTheme`
    - Manage theme state with useState (default: `'light'`)
    - useEffect to read localStorage on mount
    - useEffect to apply `.dark` class to `document.documentElement` and persist to localStorage
  - [ ] 1.3 Create useTheme hook (`lib/hooks/use-theme.ts`)
    - Consume ThemeContext
    - Throw descriptive error if used outside ThemeProvider
  - [ ] 1.4 Ensure tests pass
    - Run ONLY tests from 1.1

**Acceptance Criteria:**

- ThemeProvider manages theme state correctly
- useTheme hook provides theme value and toggle function
- Theme persists to localStorage under key `'theme'`
- `.dark` class applied/removed on `<html>` element

### UI Components

#### Task Group 2: Theme Toggle Button

**Dependencies:** Task Group 1

- [ ] 2.0 Complete theme toggle component
  - [ ] 2.1 Write 2 focused tests for ThemeToggle
    - Test renders Moon icon in light mode
    - Test renders Sun icon in dark mode
  - [ ] 2.2 Create ThemeToggle component (`components/ui/theme-toggle.tsx`)
    - Import Button with `variant="ghost"` and `size="icon-sm"`
    - Import Sun and Moon icons from lucide-react
    - Use useTheme hook to get theme and toggleTheme
    - Render Moon when light, Sun when dark
    - Add descriptive `aria-label` that changes based on theme
  - [ ] 2.3 Ensure tests pass
    - Run ONLY tests from 2.1

**Acceptance Criteria:**

- Button displays correct icon for current theme
- Clicking button toggles theme
- Button is accessible with proper aria-label

### Layout Integration

#### Task Group 3: Integrate into Layout

**Dependencies:** Task Group 1, Task Group 2

- [ ] 3.0 Complete layout integration
  - [ ] 3.1 Write 2 focused tests for layout integration
    - Test ThemeToggle appears in navigation
    - Test theme toggle works end-to-end (click toggles theme)
  - [ ] 3.2 Modify layout.tsx for theme support
    - Add `suppressHydrationWarning` to `<html>` element
    - Add inline script in `<head>` to prevent flash (reads localStorage, applies `.dark` class)
    - Wrap body contents with ThemeProvider
  - [ ] 3.3 Add ThemeToggle to NavBar
    - Position after navigation links (right side of header)
    - Maintain consistent spacing with existing nav items
  - [ ] 3.4 Ensure tests pass
    - Run ONLY tests from 3.1

**Acceptance Criteria:**

- No flash of wrong theme on page load
- ThemeToggle visible in header on all pages
- Theme persists across page refreshes

### Testing

#### Task Group 4: Test Review

**Dependencies:** Task Groups 1-3

- [ ] 4.0 Review and verify feature completeness
  - [ ] 4.1 Review tests from groups 1-3 (7 tests)
  - [ ] 4.2 Manual verification checklist
    - Toggle switches theme instantly
    - Preference persists after page refresh
    - All pages render correctly in dark mode
    - All pages render correctly in light mode
  - [ ] 4.3 Run all dark mode tests

**Acceptance Criteria:**

- All 7 feature tests pass
- Manual verification passes on Dashboard, History, Import pages

## Execution Order

1. **Task Group 1** (Theme Infrastructure) — Foundation: context and hook must exist before components can use them
2. **Task Group 2** (Theme Toggle) — UI component depends on useTheme hook
3. **Task Group 3** (Layout Integration) — Final assembly requires all pieces
4. **Task Group 4** (Test Review) — Verification after implementation complete

## Files to Create

| File                                        | Purpose                    |
| ------------------------------------------- | -------------------------- |
| `frontend/components/ui/theme-provider.tsx` | Context provider component |
| `frontend/components/ui/theme-toggle.tsx`   | Toggle button component    |
| `frontend/lib/hooks/use-theme.ts`           | Context consumer hook      |

## Files to Modify

| File                      | Changes                                       |
| ------------------------- | --------------------------------------------- |
| `frontend/app/layout.tsx` | Add provider, toggle, flash-prevention script |
