# Upload and Categorize API — Feature Specification

## Overview

Build FastAPI endpoints for CSV upload, parsing preview, and triggering categorization with support for replace/merge import modes.

**Size**: M (Medium)
**Dependencies**: Items 1-4 (Database Models, CSV Parser, Categorization Service, Score Calculation)

---

## Functional Requirements

### Use Case: Import et catégorisation (mono ou multi-mois)

```txt
En tant qu'utilisateur,
Je veux importer mon export Bankin' (qui peut contenir plusieurs mois),
Afin que mes transactions soient automatiquement catégorisées et regroupées par mois.
```

### Acceptance Criteria

- [ ] L'utilisateur peut uploader un fichier CSV
- [ ] Le système détecte automatiquement le format Bankin'
- [ ] Le système détecte automatiquement tous les mois présents dans le fichier
- [ ] Les transactions sont groupées par mois (année + mois)
- [ ] Les transactions sont catégorisées via l'API Claude (par batch)
- [ ] Les virements internes sont automatiquement exclus
- [ ] Un résumé par mois est affiché avant validation
- [ ] Les données existantes d'un mois peuvent être écrasées ou fusionnées

---

## API Endpoints

### 1. Upload CSV — `POST /api/upload`

Uploads and parses a Bankin' CSV file. Detects all months present and returns a preview.

#### Request

- **Content-Type**: `multipart/form-data`
- **Body**: `file` (CSV file)

#### Response Schema

```python
class MonthSummary(BaseModel):
    year: int
    month: int
    transaction_count: int
    total_income: float
    total_expenses: float

class UploadResponse(BaseModel):
    success: bool
    total_transactions: int
    months_detected: list[MonthSummary]
    preview_by_month: dict[str, list[dict]]  # "2025-10": [transactions...]
```

#### Example Response

```json
{
  "success": true,
  "total_transactions": 1355,
  "months_detected": [
    {"year": 2025, "month": 1, "transaction_count": 89, "total_income": 1429.12, "total_expenses": 901.25},
    {"year": 2025, "month": 10, "transaction_count": 156, "total_income": 2823.29, "total_expenses": 1245.50}
  ],
  "preview_by_month": {
    "2025-01": [
      {"date": "2025-01-30", "description": "Virement Salaire", "amount": 1100.0}
    ],
    "2025-10": [...]
  }
}
```

### 2. Categorize Transactions — `POST /api/categorize`

Triggers categorization via Claude API for selected months. Stores results in database.

#### Request Schema

```python
class CategorizeRequest(BaseModel):
    months_to_process: list[str]  # ["2025-01", "2025-02", ...] or ["all"]
    import_mode: str  # "replace" | "merge"
```

- **months_to_process**: List of month keys to process, or `["all"]` to process all detected months
- **import_mode**:
  - `replace`: Overwrites existing data for the month
  - `merge`: Adds to existing data, avoiding duplicates

#### Response Schema

```python
class MonthResult(BaseModel):
    year: int
    month: int
    transactions_categorized: int
    low_confidence_count: int
    score: int
    score_label: str

class CategorizeResponse(BaseModel):
    success: bool
    months_processed: list[MonthResult]
    total_api_calls: int
```

#### Example Response

```json
{
  "success": true,
  "months_processed": [
    {
      "year": 2025,
      "month": 1,
      "transactions_categorized": 89,
      "low_confidence_count": 5,
      "score": 2,
      "score_label": "Okay"
    },
    {
      "year": 2025,
      "month": 10,
      "transactions_categorized": 156,
      "low_confidence_count": 8,
      "score": 3,
      "score_label": "Great"
    }
  ],
  "total_api_calls": 3
}
```

---

## Implementation Details

### Workflow

```txt
1. User uploads CSV file
   └─> POST /api/upload
       └─> CSVParser.parse() groups transactions by month
       └─> Returns preview with month summaries

2. User selects months and import mode
   └─> POST /api/categorize
       └─> For each selected month:
           ├─> TransactionCategorizer.categorize_month()
           ├─> ScoreCalculator.calculate_month_stats()
           └─> Save to database (replace or merge)
       └─> Returns results with scores
```

### State Management

The upload endpoint must store parsed transactions temporarily for the categorize endpoint to access. Options:

1. **Session-based storage** (recommended): Store in server memory with session ID
2. **Re-upload**: Require file in categorize request (simpler but redundant)
3. **Temp file storage**: Write to temp file, reference by ID

### Duplicate Detection (Merge Mode)

When `import_mode: "merge"`:

```python
def _transaction_key(t: dict) -> str:
    """Generate unique key for a transaction."""
    return f"{t['Date']}_{t['Description']}_{t['Montant']}_{t['Compte']}"
```

- Compare new transactions against existing ones in database
- Skip transactions with matching keys
- Return count of skipped duplicates in response

### Error Handling

| Error Case | HTTP Status | Response |
|------------|-------------|----------|
| Invalid CSV format | 400 | `{"detail": "Invalid CSV format: missing columns"}` |
| No transactions found | 400 | `{"detail": "No transactions found in file"}` |
| Claude API failure | 502 | `{"detail": "Categorization service unavailable"}` |
| Invalid month format | 400 | `{"detail": "Invalid month format: expected YYYY-MM"}` |

---

## Data Flow

### CSV to Database

```txt
CSV File
    │
    ▼
┌─────────────────────────┐
│   CSVParser.parse()     │
│   - Validate columns    │
│   - Parse dates         │
│   - Group by month      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   TransactionCategorizer│
│   - Batch by 50         │
│   - Call Claude API     │
│   - Assign categories   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   ScoreCalculator       │
│   - Sum by category     │
│   - Calculate %         │
│   - Determine score     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Database              │
│   - months table        │
│   - transactions table  │
└─────────────────────────┘
```

---

## File Structure

```txt
backend/app/
├── routers/
│   └── upload.py          # POST /api/upload, POST /api/categorize
├── services/
│   ├── csv_parser.py      # Already exists (item 2)
│   ├── categorizer.py     # Already exists (item 3)
│   └── calculator.py      # Already exists (item 4)
└── schemas/
    └── upload.py          # Request/Response models for upload endpoints
```

---

## Testing Requirements

### Unit Tests

1. **Upload endpoint**
   - Valid CSV file returns correct month summaries
   - Invalid format returns 400 error
   - Empty file returns appropriate error

2. **Categorize endpoint**
   - Replace mode clears existing data
   - Merge mode skips duplicates
   - Invalid month format returns 400 error

### Integration Tests

1. Full upload → categorize → verify database flow
2. Multi-month file processing
3. Claude API error handling (mock failures)

---

## API Cost Considerations

- Batch 50 transactions per Claude API call
- Pre-filter obvious internal transfers before API call
- Track `total_api_calls` in response for cost monitoring
- Estimated cost: ~$0.50-$1.00 per 1,350 transactions (10 months)
