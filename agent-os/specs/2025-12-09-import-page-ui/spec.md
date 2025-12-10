# Specification: Import Page UI

## Goal

Build the frontend import page that allows users to upload Bankin' CSV files, preview detected months, select which months to import, and monitor categorization progress with results.

## User Stories

- As a user, I want to upload my Bankin' CSV export and see a preview of all detected months, so that I can select which months to import and monitor the categorization progress.
- As a user, I want to choose between "Replace" or "Merge" import modes, so that I can control how new data integrates with existing months.

## Specific Requirements

**File Upload Zone:**

- Drag-and-drop CSV files onto a prominent dropzone area
- Click-to-browse fallback with hidden file input
- Accept only `.csv` files; reject others with error message
- Visual states: Default (dashed border), Dragging (highlighted), Uploaded (solid, checkmark), Error (red border)
- Single file at a time; new file replaces previous

**Multi-Month Preview Table:**

- Display table with columns: Checkbox, Month (MMM YYYY), Transactions, Income (€), Expenses (€)
- All months selected by default after upload
- "Select All" and "Deselect All" buttons below table
- Months sorted chronologically (oldest first)
- Income displayed in blue (#3b82f6), expenses as negative values

**Import Mode Selection:**

- Radio group with two options: "Replace" and "Merge"
- "Merge" selected by default (skip duplicates)
- "Replace" overwrites existing data for selected months
- Disabled during categorization

**Categorization Progress Display:**

- Show indeterminate progress bar during processing (backend doesn't stream progress)
- Display "Processing X months..." message
- Cancel button to abort (refreshes page)
- Disable all inputs during categorization

**Results Summary:**

- Display each processed month with: score (0-3), score label, emoji, Core/Choice/Compound percentages
- Score colors: Great=#22c55e, Okay=#eab308, Need Improvement=#f97316, Poor=#ef4444
- Show low confidence transaction count per month
- "View transactions to verify" button (disabled with tooltip "Coming soon in Dashboard")
- "Finish import" button (resets to empty state)

**Page State Machine:**

- States: `empty` → `uploading` → `preview` → `categorizing` → `results` → `error`
- Error state shows Alert with message and "Try Again" button
- Keep file and selections on categorization error (allow retry)
- Clear file on upload error

**Error Handling:**

- Invalid file type: "Only CSV files are accepted"
- Network error: "Unable to connect to server"
- Backend errors: Display `detail` message from API response
- All errors use shadcn/ui Alert with `variant="destructive"`

## Visual Design

**`planning/visuals/wireframe-import-page-ui.md`**

- Navigation bar with [Import] [History] tabs at top
- Large centered dropzone with folder icon and "Drag your CSV file here or click to select"
- "Accepted format: .csv" hint text below dropzone
- File Analysis card with header showing total transactions and months detected
- Month preview table nested inside File Analysis card
- Select All / Deselect All buttons below table
- Import mode radio buttons below selection buttons
- Cancel and "Categorize Selected Months" primary buttons at bottom

## Existing Code to Leverage

**POST /api/upload endpoint - `backend/app/routers/upload.py:30`**

- What it does: Parses CSV file and returns month summaries without persisting
- How to reuse: Call via FormData with file, returns UploadResponse
- Key fields: `success`, `total_transactions`, `months_detected[]`, `preview_by_month`

**POST /api/categorize endpoint - `backend/app/routers/upload.py:61`**

- What it does: Categorizes transactions, persists to database, calculates scores
- How to reuse: Call via FormData with file + query params `months_to_process` and `import_mode`
- Key fields: `success`, `months_processed[]` (with score, score_label, low_confidence_count), `total_api_calls`

**Response schemas - `backend/app/responses/upload.py`**

- What it does: Defines Pydantic models for API responses
- How to reuse: Mirror types in `frontend/types/index.ts`
- Key types: MonthSummaryResponse, UploadResponse, MonthResult, CategorizeResponse

**Score labels and colors - `backend/app/db/enums.py`**

- What it does: Defines ScoreLabel enum (Poor, Need Improvement, Okay, Great)
- How to reuse: Map score (0-3) to label and color in frontend
- Key mapping: 0=Poor/Red, 1=Need Improvement/Orange, 2=Okay/Yellow, 3=Great/Green

## Architecture Approach

**Component Design:**

- `app/import/page.tsx` - Server component wrapper (imports client component)
- `components/import/import-page-client.tsx` - Client component with `useReducer` for all state
- `components/import/file-dropzone.tsx` - Drag-and-drop with visual states
- `components/import/month-preview-table.tsx` - Table with checkboxes, select all/none
- `components/import/import-options.tsx` - RadioGroup for import mode
- `components/import/progress-panel.tsx` - Indeterminate progress during categorization
- `components/import/results-summary.tsx` - Score display with action buttons

**Data Flow:**

- User drops file → dispatch FILE_SELECTED → call apiClient.uploadCSV → dispatch UPLOAD_SUCCESS
- User clicks Categorize → dispatch CATEGORIZE_START → call apiClient.categorize → dispatch CATEGORIZE_SUCCESS
- All state lifted to `import-page-client.tsx`; children receive props and callbacks

**Integration Points:**

- `lib/api-client.ts` - Centralized fetch wrapper for /api/upload and /api/categorize
- `types/index.ts` - TypeScript types mirroring backend response schemas
- `lib/utils.ts` - Helpers: formatCurrency (€), formatMonthDisplay (MMM YYYY), formatMonthKey (YYYY-MM)
- File kept in React state between upload and categorize (required by backend API)

**shadcn/ui Components:**

- Card (sections), Table (months), Checkbox (selection), RadioGroup (import mode)
- Button (actions), Progress (indeterminate), Badge (score labels), Alert (errors)

## Out of Scope

- Transaction editing/correction (feature #9)
- Viewing individual transactions (feature #8 Dashboard)
- Historical data and charts (feature #10+)
- Non-Bankin' CSV formats
- Real-time progress streaming (backend doesn't support it)
- WebSocket or SSE for progress updates
- Multiple file uploads
- Drag-and-drop reordering of months
- Persisting user preferences (import mode selection)
- Navigation to other pages (History tab is placeholder)
