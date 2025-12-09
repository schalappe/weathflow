# Task Breakdown: Import Page UI

## Overview

Total Tasks: 24
Estimated Complexity: Medium
Primary Stack: Next.js 14 + TypeScript + shadcn/ui + Tailwind CSS

## Task List

### Foundation Layer

#### Task Group 1: Project Setup and Types

**Dependencies:** None

- [ ] 1.0 Complete foundation layer
  - [ ] 1.1 Initialize Next.js project with TypeScript and Tailwind
    - Run `bunx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false`
    - Configure `next.config.ts` with API proxy to backend
    - Update `tailwind.config.ts` with custom colors (score colors, Money Map colors)
  - [ ] 1.2 Initialize shadcn/ui and install required components
    - Run `bunx shadcn@latest init` with default settings
    - Install components: `bunx shadcn@latest add card table checkbox radio-group button progress badge alert`
  - [ ] 1.3 Create TypeScript types mirroring backend schemas
    - Create `types/index.ts`
    - Types: MonthSummaryResponse, UploadResponse, MonthResult, CategorizeResponse
    - Types: ImportState, ImportAction, PageState, ImportMode
  - [ ] 1.4 Create utility functions
    - Create `lib/utils.ts`
    - Add `cn()` for className merging (from shadcn)
    - Add `formatCurrency(amount: number)` for Euro formatting
    - Add `formatMonthDisplay(year, month)` for "MMM YYYY" format
    - Add `formatMonthKey(year, month)` for "YYYY-MM" format
  - [ ] 1.5 Create API client
    - Create `lib/api-client.ts`
    - Implement `uploadCSV(file: File): Promise<UploadResponse>`
    - Implement `categorize(file, months, importMode): Promise<CategorizeResponse>`
    - Use `NEXT_PUBLIC_API_URL` environment variable
  - [ ] 1.6 Verify foundation setup
    - Run `bun run dev` and confirm app starts on port 3000
    - Verify shadcn components render correctly
    - Test API client can reach backend (manual check)

**Acceptance Criteria:**

- Next.js app runs without errors
- All shadcn/ui components installed and importable
- TypeScript types compile without errors
- API client methods defined with correct signatures

---

### UI Components Layer

#### Task Group 2: File Dropzone Component

**Dependencies:** Task Group 1

- [ ] 2.0 Complete file dropzone component
  - [ ] 2.1 Write 3 focused tests for file dropzone
    - Test: CSV file acceptance triggers onFileSelected callback
    - Test: Non-CSV file rejection shows error state
    - Test: Drag-over state shows visual feedback
  - [ ] 2.2 Create file-dropzone.tsx component
    - Create `components/import/file-dropzone.tsx`
    - Props: `{ onFileSelected, file, isDisabled, error }`
    - Use hidden `<input type="file" accept=".csv">` for click-to-browse
  - [ ] 2.3 Implement drag-and-drop handlers
    - `onDragOver`: Set dragging state, prevent default
    - `onDragLeave`: Clear dragging state
    - `onDrop`: Validate file type, call onFileSelected or set error
  - [ ] 2.4 Implement visual states
    - Default: Dashed border, folder icon, "Drag your CSV file here"
    - Dragging: Highlighted border (primary color), "Drop to upload"
    - Uploaded: Solid border, checkmark icon, filename displayed
    - Error: Red border, error message below
  - [ ] 2.5 Ensure dropzone tests pass
    - Run ONLY the 3 tests from 2.1

**Acceptance Criteria:**

- All 3 dropzone tests pass
- Drag-and-drop works for CSV files
- Click-to-browse opens file picker
- Visual states match specification

---

#### Task Group 3: Month Preview Table Component

**Dependencies:** Task Group 1

- [ ] 3.0 Complete month preview table component
  - [ ] 3.1 Write 3 focused tests for month preview table
    - Test: Renders all months with correct columns
    - Test: Checkbox toggle updates selection
    - Test: Select All / Deselect All buttons work correctly
  - [ ] 3.2 Create month-preview-table.tsx component
    - Create `components/import/month-preview-table.tsx`
    - Props: `{ months, selectedMonths, onToggleMonth, onSelectAll, onDeselectAll, isDisabled }`
    - Use shadcn/ui Table and Checkbox components
  - [ ] 3.3 Implement table structure
    - Columns: Checkbox, Month (MMM YYYY), Transactions, Income (€), Expenses (€)
    - Sort months chronologically (oldest first)
    - Format income in blue (#3b82f6), expenses as negative values
  - [ ] 3.4 Implement selection controls
    - "Select All" and "Deselect All" buttons below table
    - Disable all controls when `isDisabled` prop is true
  - [ ] 3.5 Ensure table tests pass
    - Run ONLY the 3 tests from 3.1

**Acceptance Criteria:**

- All 3 table tests pass
- Months display in chronological order
- Currency formatting works correctly
- Selection controls function properly

---

#### Task Group 4: Import Options and Progress Components

**Dependencies:** Task Group 1

- [ ] 4.0 Complete import options and progress components
  - [ ] 4.1 Write 2 focused tests for import options
    - Test: Radio group renders Replace and Merge options
    - Test: Mode change triggers callback with correct value
  - [ ] 4.2 Create import-options.tsx component
    - Create `components/import/import-options.tsx`
    - Props: `{ mode, onModeChange, isDisabled }`
    - Use shadcn/ui RadioGroup component
    - "Merge" selected by default, "Replace" as alternative
  - [ ] 4.3 Create progress-panel.tsx component
    - Create `components/import/progress-panel.tsx`
    - Props: `{ isProcessing, selectedMonthCount }`
    - Show indeterminate Progress bar when processing
    - Display "Processing X months..." message
    - Include Cancel button (triggers page refresh)
  - [ ] 4.4 Ensure options tests pass
    - Run ONLY the 2 tests from 4.1

**Acceptance Criteria:**

- All 2 options tests pass
- Radio buttons toggle correctly
- Progress panel shows indeterminate state
- Cancel button refreshes page

---

#### Task Group 5: Results Summary Component

**Dependencies:** Task Group 1

- [ ] 5.0 Complete results summary component
  - [ ] 5.1 Write 3 focused tests for results summary
    - Test: Renders each month with score, label, and percentages
    - Test: Score badge displays correct color based on score value
    - Test: "View transactions" button is disabled with tooltip
  - [ ] 5.2 Create results-summary.tsx component
    - Create `components/import/results-summary.tsx`
    - Props: `{ results, monthsNotFound, totalApiCalls, onViewTransactions, onFinish }`
    - Use shadcn/ui Card, Badge, Button components
  - [ ] 5.3 Implement score display
    - Map score to color: 3=Green, 2=Yellow, 1=Orange, 0=Red
    - Show score label with emoji (Great, Okay, Need Improvement, Poor)
    - Display Core%, Choice%, Compound% percentages per month
    - Show low confidence count if > 0
  - [ ] 5.4 Implement action buttons
    - "View transactions to verify" button (disabled, tooltip "Coming soon in Dashboard")
    - "Finish import" button (calls onFinish to reset state)
  - [ ] 5.5 Ensure results tests pass
    - Run ONLY the 3 tests from 5.1

**Acceptance Criteria:**

- All 3 results tests pass
- Score colors match specification
- Percentages display correctly
- Disabled button shows tooltip

---

### Integration Layer

#### Task Group 6: Main Page and State Management

**Dependencies:** Task Groups 2, 3, 4, 5

- [ ] 6.0 Complete main page integration
  - [ ] 6.1 Write 4 focused tests for import page client
    - Test: File upload triggers API call and shows preview state
    - Test: Categorize button triggers API call and shows results state
    - Test: Error state displays Alert with retry option
    - Test: State transitions follow correct flow (empty → uploading → preview → categorizing → results)
  - [ ] 6.2 Create import page server wrapper
    - Create `app/import/page.tsx`
    - Simple server component that imports and renders ImportPageClient
  - [ ] 6.3 Create app root layout
    - Create `app/layout.tsx` with minimal shell
    - Include navigation bar with [Import] [History] tabs (History is placeholder)
    - Apply global styles and fonts
  - [ ] 6.4 Create import-page-client.tsx with useReducer
    - Create `components/import/import-page-client.tsx`
    - Implement ImportState and ImportAction types
    - Define reducer with all state transitions
    - Initial state: `{ pageState: 'empty', file: null, ... }`
  - [ ] 6.5 Implement state reducer actions
    - FILE_SELECTED: Set file, trigger upload
    - UPLOAD_START: Set pageState to 'uploading'
    - UPLOAD_SUCCESS: Set uploadResponse, select all months, set pageState to 'preview'
    - UPLOAD_ERROR: Set error, clear file, set pageState to 'error'
    - TOGGLE_MONTH, SELECT_ALL_MONTHS, DESELECT_ALL_MONTHS: Update selectedMonths
    - SET_IMPORT_MODE: Update importMode
    - CATEGORIZE_START: Set pageState to 'categorizing'
    - CATEGORIZE_SUCCESS: Set categorizeResponse, set pageState to 'results'
    - CATEGORIZE_ERROR: Set error, keep file, set pageState to 'error'
    - RESET: Return to initial state
  - [ ] 6.6 Wire up all components
    - Render FileDropzone when pageState is 'empty' or 'error'
    - Render MonthPreviewTable + ImportOptions when pageState is 'preview'
    - Render ProgressPanel when pageState is 'categorizing'
    - Render ResultsSummary when pageState is 'results'
    - Render Alert when error exists
  - [ ] 6.7 Implement API integration
    - Call apiClient.uploadCSV on file selection
    - Call apiClient.categorize on "Categorize Selected Months" click
    - Handle errors and dispatch appropriate actions
  - [ ] 6.8 Create root page redirect
    - Create `app/page.tsx` that redirects to `/import`
  - [ ] 6.9 Ensure integration tests pass
    - Run ONLY the 4 tests from 6.1

**Acceptance Criteria:**

- All 4 integration tests pass
- Full flow works: upload → preview → categorize → results
- Error states handled gracefully
- State transitions are predictable

---

### Testing Layer

#### Task Group 7: Test Review and Gap Analysis

**Dependencies:** Task Groups 2, 3, 4, 5, 6

- [ ] 7.0 Review and fill critical test gaps
  - [ ] 7.1 Review tests from Task Groups 2-6
    - Dropzone tests (3 from 2.1)
    - Table tests (3 from 3.1)
    - Options tests (2 from 4.1)
    - Results tests (3 from 5.1)
    - Integration tests (4 from 6.1)
    - Total existing: 15 tests
  - [ ] 7.2 Identify critical coverage gaps
    - Focus on end-to-end user workflows
    - Check API error handling scenarios
    - Verify edge cases in month selection
  - [ ] 7.3 Write up to 8 additional strategic tests
    - Test: Empty file shows appropriate error
    - Test: Network timeout shows error with retry
    - Test: Selecting zero months disables Categorize button
    - Test: Multiple file drops replace previous file
    - Test: Cancel during categorization refreshes page
    - Test: Results display correct totals from API response
    - Test: Currency formatting handles negative values
    - Test: Month key formatting produces correct YYYY-MM format
  - [ ] 7.4 Run all feature tests
    - Run all 23 tests (15 existing + 8 new)
    - Verify all pass
    - Do NOT run tests outside this feature

**Acceptance Criteria:**

- All 23 feature tests pass
- Critical user workflows covered
- No more than 8 additional tests added
- Testing focused on Import Page UI feature only

---

## Execution Order

1. **Task Group 1: Project Setup and Types** - Foundation for all other work
2. **Task Groups 2-5: UI Components** (can be done in parallel)
   - Task Group 2: File Dropzone
   - Task Group 3: Month Preview Table
   - Task Group 4: Import Options and Progress
   - Task Group 5: Results Summary
3. **Task Group 6: Main Page and State Management** - Integrates all components
4. **Task Group 7: Test Review and Gap Analysis** - Final quality assurance

## Notes

- Backend APIs (`/api/upload`, `/api/categorize`) are already implemented
- This is the first frontend page - no existing UI patterns to follow
- Use shadcn/ui components consistently for cohesive design
- All components should be client components (`'use client'`) due to interactivity
- Keep File object in state between upload and categorize (required by backend API)
