# Feature 18: Data Export

## Overview

Implement JSON and CSV export functionality for monthly financial data. This enables users to backup their data and use it in external tools like spreadsheets. The feature adds export buttons to the dashboard that download the current month's data.

**Size:** XS (Extra Small)
**Dependencies:** Feature #6 (Monthly Data API), Feature #8 (Monthly Dashboard UI)

## User Story

```txt
En tant qu'utilisateur,
Je veux exporter mes donnees mensuelles en JSON et CSV,
Afin de sauvegarder mes donnees et les utiliser dans d'autres outils.
```

### Acceptance Criteria

- [ ] Export monthly data as JSON file with all transactions and summary
- [ ] Export monthly data as CSV file with transaction list
- [ ] Download files with descriptive filenames (e.g., `moneymap-2025-10.json`)
- [ ] Export buttons accessible from the dashboard
- [ ] Show loading state during export generation
- [ ] Handle errors gracefully with user feedback

## Technical Specifications

### Backend API

Add new export endpoints in `backend/app/routers/months.py`:

```txt
GET /api/months/{year}/{month}/export/json
GET /api/months/{year}/{month}/export/csv
```

### JSON Export Format

```json
{
  "exported_at": "2025-10-29T14:30:00Z",
  "month": {
    "year": 2025,
    "month": 10,
    "total_income": 2823.29,
    "total_core": 1245.00,
    "total_choice": 678.50,
    "total_compound": 899.79,
    "core_percentage": 44.1,
    "choice_percentage": 24.0,
    "compound_percentage": 31.9,
    "score": 3,
    "score_label": "Great"
  },
  "transactions": [
    {
      "date": "2025-10-29",
      "description": "CB Domoro",
      "amount": -2.50,
      "account": "Compte De Depots",
      "bankin_category": "Alimentation & Restau.",
      "bankin_subcategory": "Fast foods",
      "money_map_type": "CHOICE",
      "money_map_subcategory": "Dining out",
      "is_manually_corrected": false
    }
  ],
  "transaction_count": 156
}
```

### CSV Export Format

Standard CSV with headers, semicolon-separated (matches Bankin' format):

```csv
Date;Description;Account;Amount;Bankin Category;Bankin Subcategory;Money Map Type;Money Map Subcategory;Manually Corrected
2025-10-29;CB Domoro;Compte De Depots;-2.50;Alimentation & Restau.;Fast foods;CHOICE;Dining out;false
2025-10-29;Virement Salaire;Compte De Depots;2823.29;Entrees d'argent;Salaires;INCOME;Job;false
```

### Backend Implementation

#### Router Endpoints

```python
# backend/app/routers/months.py

from fastapi.responses import StreamingResponse
import csv
import io
import json
from datetime import UTC, datetime

@router.get("/{year}/{month}/export/json")
async def export_month_json(
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    Export month data as JSON file.

    Returns
    -------
    StreamingResponse
        JSON file download with month summary and transactions.
    """
    month_record = crud.get_month_by_year_month(db, year, month)
    if not month_record:
        raise HTTPException(status_code=404, detail="Month not found")

    transactions = crud.get_transactions_by_month(db, month_record.id)

    export_data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "month": {
            "year": month_record.year,
            "month": month_record.month,
            "total_income": month_record.total_income,
            "total_core": month_record.total_core,
            "total_choice": month_record.total_choice,
            "total_compound": month_record.total_compound,
            "core_percentage": month_record.core_percentage,
            "choice_percentage": month_record.choice_percentage,
            "compound_percentage": month_record.compound_percentage,
            "score": month_record.score,
            "score_label": month_record.score_label,
        },
        "transactions": [
            {
                "date": t.date.isoformat(),
                "description": t.description,
                "amount": t.amount,
                "account": t.account,
                "bankin_category": t.bankin_category,
                "bankin_subcategory": t.bankin_subcategory,
                "money_map_type": t.money_map_type,
                "money_map_subcategory": t.money_map_subcategory,
                "is_manually_corrected": t.is_manually_corrected,
            }
            for t in transactions
        ],
        "transaction_count": len(transactions),
    }

    json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"moneymap-{year}-{month:02d}.json"

    return StreamingResponse(
        io.BytesIO(json_content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.get("/{year}/{month}/export/csv")
async def export_month_csv(
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    Export month transactions as CSV file.

    Returns
    -------
    StreamingResponse
        CSV file download with transaction list.
    """
    month_record = crud.get_month_by_year_month(db, year, month)
    if not month_record:
        raise HTTPException(status_code=404, detail="Month not found")

    transactions = crud.get_transactions_by_month(db, month_record.id)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # ##>: Headers match the JSON export fields for consistency.
    writer.writerow([
        "Date",
        "Description",
        "Account",
        "Amount",
        "Bankin Category",
        "Bankin Subcategory",
        "Money Map Type",
        "Money Map Subcategory",
        "Manually Corrected",
    ])

    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            t.description,
            t.account,
            t.amount,
            t.bankin_category,
            t.bankin_subcategory,
            t.money_map_type,
            t.money_map_subcategory,
            str(t.is_manually_corrected).lower(),
        ])

    filename = f"moneymap-{year}-{month:02d}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

### Frontend Implementation

#### Component Location

```txt
frontend/
  components/
    dashboard/
      export-buttons.tsx     # New - export action buttons
```

#### Export Buttons Component

```typescript
// components/dashboard/export-buttons.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface ExportButtonsProps {
  year: number;
  month: number;
}

export function ExportButtons({ year, month }: ExportButtonsProps) {
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [isExportingCsv, setIsExportingCsv] = useState(false);

  const handleExport = async (format: 'json' | 'csv') => {
    const setLoading = format === 'json' ? setIsExportingJson : setIsExportingCsv;
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/months/${year}/${month}/export/${format}`
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // [>]: Create blob and trigger download via hidden anchor element.
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `moneymap-${year}-${String(month).padStart(2, '0')}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export error:', error);
      // [?]: Consider adding toast notification for error feedback.
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('json')}
        disabled={isExportingJson}
      >
        <Download className="mr-2 h-4 w-4" />
        {isExportingJson ? 'Exporting...' : 'JSON'}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('csv')}
        disabled={isExportingCsv}
      >
        <Download className="mr-2 h-4 w-4" />
        {isExportingCsv ? 'Exporting...' : 'CSV'}
      </Button>
    </div>
  );
}
```

#### Integration in Dashboard

Add export buttons to the dashboard header:

```typescript
// In app/page.tsx or dashboard component

<div className="flex items-center justify-between">
  <h1>October 2025</h1>
  <ExportButtons year={2025} month={10} />
</div>
```

## UI Specifications

### Visual Design

Export buttons appear in the dashboard header, aligned right:

```txt
+---------------------------------------------------------------+
|  Money Map Manager                        [Import] [History]   |
+---------------------------------------------------------------+
|                                                                |
|  OCTOBER 2025 - SCORE: 2/3 (Okay)         [JSON] [CSV]        |
|                                                                |
```

### Button States

| State    | Appearance                        |
| -------- | --------------------------------- |
| Default  | Outline button with download icon |
| Loading  | Disabled, text shows "Exporting..." |
| Disabled | Grayed out (when no data exists)  |

### Responsive Behavior

- **Desktop**: Buttons side by side in header
- **Mobile**: Buttons stack vertically or move to dropdown menu

## Testing Requirements

### Backend Tests

```python
# tests/test_months_export.py

def test_export_json_returns_valid_json():
    """Export endpoint returns valid JSON structure."""

def test_export_json_includes_all_transactions():
    """JSON export contains all month transactions."""

def test_export_json_includes_month_summary():
    """JSON export contains month statistics."""

def test_export_json_404_for_missing_month():
    """Returns 404 when month doesn't exist."""

def test_export_csv_returns_valid_csv():
    """Export endpoint returns valid CSV format."""

def test_export_csv_has_correct_headers():
    """CSV has all expected column headers."""

def test_export_csv_semicolon_delimiter():
    """CSV uses semicolon as delimiter."""

def test_export_csv_404_for_missing_month():
    """Returns 404 when month doesn't exist."""

def test_export_filename_format():
    """Downloaded file has correct naming pattern."""
```

### Frontend Tests

```typescript
// tests/components/dashboard/export-buttons.test.tsx

describe('ExportButtons', () => {
  it('renders JSON and CSV export buttons', () => {});
  it('shows loading state when exporting JSON', () => {});
  it('shows loading state when exporting CSV', () => {});
  it('triggers download on successful export', () => {});
  it('handles export errors gracefully', () => {});
});
```

## Implementation Steps

1. **Backend: Add JSON export endpoint** in `months.py` router
2. **Backend: Add CSV export endpoint** in `months.py` router
3. **Backend: Add tests** for export endpoints
4. **Frontend: Create ExportButtons component**
5. **Frontend: Integrate buttons into dashboard**
6. **Frontend: Add component tests**

## Out of Scope

- Export all months at once (bulk export)
- Export to Excel (.xlsx) format
- Export filtered transactions only
- Scheduled automatic backups
- Cloud backup integration
- Import from exported files (restore functionality)
