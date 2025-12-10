# Import Page UI — Feature PRD

## 1. Overview

### 1.1 Feature Summary

Build the frontend import page that allows users to upload Bankin' CSV files, preview detected months with transaction summaries, select which months to import, and monitor categorization progress.

### 1.2 Dependencies

- **Backend APIs (already implemented)**:
  - `POST /api/upload` — Parse CSV and return month summaries
  - `POST /api/categorize` — Trigger categorization for selected months

### 1.3 User Story

```sql
As a user,
I want to upload my Bankin' CSV export and see a preview of all detected months,
So that I can select which months to import and monitor the categorization progress.
```

---

## 2. Functional Requirements

### 2.1 File Upload Zone

| Requirement     | Description                                      |
| --------------- | ------------------------------------------------ |
| Drag-and-drop   | Users can drag CSV files onto the dropzone       |
| Click to browse | Clicking the zone opens file picker              |
| File validation | Accept only `.csv` files                         |
| Visual feedback | Show dragging state, uploaded state, error state |
| Single file     | One file at a time                               |

### 2.2 Multi-Month Preview Table

| Column       | Description                                    |
| ------------ | ---------------------------------------------- |
| Checkbox     | Select/deselect month for import               |
| Month        | Display as "MMM YYYY" (e.g., "Jan 2025")       |
| Transactions | Count of transactions in that month            |
| Income       | Total positive amounts (formatted as currency) |
| Expenses     | Total negative amounts (formatted as currency) |

**Additional Controls:**

- "Select All" / "Deselect All" buttons
- Months sorted chronologically (oldest first)

### 2.3 Import Mode Selection

| Option  | Description                                     |
| ------- | ----------------------------------------------- |
| Replace | Overwrite existing data for selected months     |
| Merge   | Add new transactions, skip duplicates (default) |

### 2.4 Categorization Progress

| Element                | Description                                |
| ---------------------- | ------------------------------------------ |
| Per-month progress bar | Shows percentage complete for each month   |
| Status indicator       | Pending / In Progress / Complete / Error   |
| API call counter       | "API calls: X/Y"                           |
| Cancel button          | Allow canceling in-progress categorization |

### 2.5 Results Summary

| Element              | Description                                     |
| -------------------- | ----------------------------------------------- |
| Score per month      | Display score (0-3) with label and emoji        |
| Percentages          | Core%, Choice%, Compound% per month             |
| Low confidence count | Number of transactions needing review           |
| Action buttons       | "View transactions to verify" / "Finish import" |

---

## 3. UI States

### 3.1 Page States Flow

```text
Empty → File Uploaded → Preview Shown → Categorizing → Results
```

| State             | Description                                         |
| ----------------- | --------------------------------------------------- |
| **Empty**         | Show dropzone with instructions                     |
| **File Uploaded** | Brief loading while parsing                         |
| **Preview Shown** | Display month table, import options, action buttons |
| **Categorizing**  | Show progress indicators, disable inputs            |
| **Results**       | Show summary with scores, enable navigation         |
| **Error**         | Display error message with retry option             |

### 3.2 Dropzone States

| State    | Visual                                                |
| -------- | ----------------------------------------------------- |
| Default  | Dashed border, folder icon, "Drag your CSV file here" |
| Dragging | Highlighted border, "Drop to upload"                  |
| Uploaded | Solid border, checkmark, filename displayed           |
| Error    | Red border, error message                             |

---

## 4. UI Wireframe Reference

```txt
┌───────────────────────────────────────────────────────────────┐
│  Money Map Manager                        [Import] [History]  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │         📁 Drag your CSV file here                      │  │
│  │              or click to select                         │  │
│  │                                                         │  │
│  │              Accepted format: .csv                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 📊 FILE ANALYSIS                                        │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ ✓ 1,355 transactions detected                           │  │
│  │ ✓ 10 months detected (Jan → Oct 2025)                   │  │
│  │                                                         │  │
│  │ ┌─────────────────────────────────────────────────────┐ │  │
│  │ │ [✓] │ Month     │ Trans. │ Income    │ Expenses     │ │  │
│  │ ├─────────────────────────────────────────────────────┤ │  │
│  │ │ [✓] │ Jan 2025  │   89   │  €1,429   │    €901      │ │  │
│  │ │ [✓] │ Feb 2025  │   76   │     €0    │    €456      │ │  │
│  │ │ ...                                                 │ │  │
│  │ └─────────────────────────────────────────────────────┘ │  │
│  │                                                         │  │
│  │ [Select All] [Deselect All]                             │  │
│  │                                                         │  │
│  │ Import mode:                                            │  │
│  │ ○ Replace existing data                                 │  │
│  │ ● Merge (skip duplicates)                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│         [Cancel]    [Categorize Selected Months]              │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. Component Structure

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

---

## 6. API Integration

### 6.1 Upload Flow

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

### 6.2 Expected API Response Types

```typescript
interface MonthSummary {
  year: number;
  month: number;
  transaction_count: number;
  total_income: number;
  total_expenses: number;
}

interface UploadResponse {
  success: boolean;
  total_transactions: number;
  months_detected: MonthSummary[];
}

interface MonthResult {
  year: number;
  month: number;
  transactions_categorized: number;
  low_confidence_count: number;
  score: number;
  score_label: string;
}

interface CategorizeResponse {
  success: boolean;
  months_processed: MonthResult[];
  total_api_calls: number;
}
```

---

## 7. Acceptance Criteria

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
- [ ] User can navigate to review low-confidence transactions
- [ ] Error states are handled gracefully with retry options

---

## 8. Design Specifications

### 8.1 Colors

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

### 8.2 shadcn/ui Components to Use

- `Card` — Container for sections
- `Table` — Month preview table
- `Checkbox` — Month selection
- `RadioGroup` — Import mode selection
- `Button` — Actions
- `Progress` — Categorization progress bars
- `Badge` — Score labels
- `Alert` — Error/success messages

---

## 9. Out of Scope

- Transaction editing/correction (separate feature #9)
- Viewing individual transactions (part of Dashboard #8)
- Historical data (feature #10+)
