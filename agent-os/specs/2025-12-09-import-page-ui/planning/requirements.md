# Spec Requirements: Import Page UI

## Initial Description

Build the file upload interface with drag-and-drop, multi-month preview table, month selection checkboxes, and categorization progress indicator.

## Requirements Discussion

### Source Document

Requirements are primarily derived from the existing PRD: `docs/product-development/features/07-import-page-ui.md`

### Clarifying Questions

**Q1:** Is the Import Page the entry point for the app?
**Answer:** Yes, based on PRD wireframe showing navigation with [Import] [History] tabs, Import is a primary page.

**Q2:** Should we support multiple file uploads at once?
**Answer:** No, single file at a time per PRD section 2.1.

**Q3:** What columns should the multi-month preview table show?
**Answer:** Per PRD section 2.2: Checkbox, Month (MMM YYYY), Transactions count, Income, Expenses.

**Q4:** Should months auto-select by default?
**Answer:** Yes, all months selected by default with Select All/Deselect All controls.

**Q5:** What granularity for progress indicator?
**Answer:** Per PRD section 2.4: Per-month progress bar with percentage, status indicator (Pending/In Progress/Complete/Error), API call counter, and Cancel button.

**Q6:** What happens after categorization completes?
**Answer:** Per PRD section 2.5: Show results summary with score per month, percentages, low-confidence count, and action buttons.

**Q7:** What is excluded from scope?
**Answer:** Per PRD section 9: Transaction editing/correction, viewing individual transactions, historical data.

### Follow-up Questions

**Follow-up 1:** The PRD mentions "View transactions to verify" button for low-confidence transactions. Since the Monthly Dashboard isn't built yet, where should this button navigate to?
**Answer:** Disabled state — Show the button but disable it with a tooltip "Coming soon in Dashboard"

## Existing Code to Reference

### Backend APIs (already implemented)

- `POST /api/upload` — Parse CSV and return month summaries
- `POST /api/categorize` — Trigger categorization for selected months

### Frontend Structure

- Components organized by feature: `components/{feature}/`
- API calls via centralized `lib/api-client.ts`
- Types defined in `types/index.ts`
- Use App Router (`app/` directory)

## Visual Assets

### Files Provided

- `wireframe-import-page-ui.md`: ASCII wireframe showing the complete page layout with dropzone, file analysis card, month preview table, import mode selection, and action buttons.

### Visual Insights

- Navigation bar with [Import] [History] tabs
- Large dropzone area with folder icon and instructions
- File Analysis card containing summary stats and month table
- Table with checkbox, month, transactions, income, expenses columns
- Select All / Deselect All buttons below table
- Import mode radio buttons (Replace/Merge with Merge as default)
- Cancel and "Categorize Selected Months" action buttons
- Fidelity level: Low-fidelity ASCII wireframe (use app's existing styling)

## Requirements Summary

### Functional Requirements

#### File Upload Zone (PRD 2.1)

- Drag-and-drop CSV files onto dropzone
- Click to browse fallback
- Accept only `.csv` files
- Visual feedback for dragging, uploaded, and error states
- Single file at a time

#### Multi-Month Preview Table (PRD 2.2)

- Columns: Checkbox, Month (MMM YYYY), Transactions, Income, Expenses
- Select All / Deselect All buttons
- Months sorted chronologically (oldest first)

#### Import Mode Selection (PRD 2.3)

- Replace: Overwrite existing data for selected months
- Merge: Add new transactions, skip duplicates (default)

#### Categorization Progress (PRD 2.4)

- Per-month progress bar with percentage
- Status indicator: Pending / In Progress / Complete / Error
- API call counter: "API calls: X/Y"
- Cancel button to abort in-progress categorization

#### Results Summary (PRD 2.5)

- Score per month (0-3) with label and emoji
- Percentages: Core%, Choice%, Compound% per month
- Low confidence count per month
- Action buttons:
  - "View transactions to verify" (disabled with tooltip "Coming soon in Dashboard")
  - "Finish import"

### Page States (PRD 3.1)

```text
Empty → File Uploaded → Preview Shown → Categorizing → Results
```

- **Empty**: Dropzone with instructions
- **File Uploaded**: Brief loading while parsing
- **Preview Shown**: Month table, import options, action buttons
- **Categorizing**: Progress indicators, inputs disabled
- **Results**: Summary with scores, navigation enabled
- **Error**: Error message with retry option

### Dropzone States (PRD 3.2)

- Default: Dashed border, folder icon, "Drag your CSV file here"
- Dragging: Highlighted border, "Drop to upload"
- Uploaded: Solid border, checkmark, filename displayed
- Error: Red border, error message

### Component Structure (PRD 5)

```text
frontend/
└── app/
    └── import/
        └── page.tsx              # Import page (server component wrapper)
└── components/
    └── import/
        ├── file-dropzone.tsx     # Drag-and-drop upload zone
        ├── month-preview-table.tsx # Multi-month selection table
        ├── import-options.tsx    # Import mode radio buttons
        ├── progress-panel.tsx    # Categorization progress display
        └── results-summary.tsx   # Post-categorization results
```

### API Integration (PRD 6)

```typescript
// 1. Upload CSV file
const response = await apiClient.uploadCSV(file);
// Returns: { total_transactions, months_detected, preview_by_month }

// 2. User selects months and import mode

// 3. Trigger categorization
const result = await apiClient.categorize({
  months_to_process: selectedMonths, // ["2025-01", "2025-02"] or ["all"]
  import_mode: "merge" // or "replace"
});
// Returns: { months_processed, total_api_calls }
```

### Design Specifications (PRD 8)

#### Colors

| Element                | Color               |
| ---------------------- | ------------------- |
| Score Great            | `#22c55e` (Green)   |
| Score Okay             | `#eab308` (Yellow)  |
| Score Need Improvement | `#f97316` (Orange)  |
| Score Poor             | `#ef4444` (Red)     |
| Income                 | `#3b82f6` (Blue)    |
| Core                   | `#8b5cf6` (Purple)  |
| Choice                 | `#f59e0b` (Amber)   |
| Compound               | `#10b981` (Emerald) |

#### shadcn/ui Components

- `Card` — Container for sections
- `Table` — Month preview table
- `Checkbox` — Month selection
- `RadioGroup` — Import mode selection
- `Button` — Actions
- `Progress` — Categorization progress bars
- `Badge` — Score labels
- `Alert` — Error/success messages

### Scope Boundaries

**In Scope:**

- File dropzone with drag-and-drop and click-to-browse
- CSV file validation
- Multi-month preview table with selection
- Import mode selection (Replace/Merge)
- Categorization progress display
- Results summary with scores
- Error handling with retry options

**Out of Scope:**

- Transaction editing/correction (feature #9)
- Viewing individual transactions (feature #8 Dashboard)
- Historical data (feature #10+)
- Non-Bankin' CSV formats

### Technical Considerations

- Backend APIs already implemented and ready to use
- Use centralized `lib/api-client.ts` for all API calls
- Client components required for interactivity (`'use client'`)
- shadcn/ui for consistent component styling
- Currency formatting for Euro (€)

### Acceptance Criteria (PRD 7)

- [ ] User can drag-and-drop a CSV file onto the dropzone
- [ ] User can click the dropzone to open file picker
- [ ] Invalid file types show error message
- [ ] Uploaded file shows all detected months in a table
- [ ] User can select/deselect individual months via checkboxes
- [ ] "Select All" and "Deselect All" buttons work correctly
- [ ] User can choose between "Replace" and "Merge" import modes
- [ ] Clicking "Categorize" triggers the categorization API
- [ ] Progress is displayed per month during categorization
- [ ] Results show score, percentages, and low-confidence count per month
- [ ] "View transactions to verify" button is disabled with tooltip
- [ ] Error states are handled gracefully with retry options
