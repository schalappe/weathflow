# Spec Requirements: Upload and Categorize API

## Initial Description

Build FastAPI endpoints for CSV upload, parsing preview, and triggering categorization with support for replace/merge import modes.

**Size**: M (Medium)
**Dependencies**: Items 1-4 (Database Models, CSV Parser, Categorization Service, Score Calculation)

## Requirements Discussion

### First Round Questions

**Q1:** CSV Upload Endpoint Design - Single endpoint or separate upload/parsing?
**Answer:** Single `POST /api/upload` endpoint that accepts multipart/form-data and returns a preview of detected months and transactions. (From spec document)

**Q2:** Parsing Preview Response - Full transactions or just summaries?
**Answer:** Both. Response includes month summaries AND full transaction previews per month via `preview_by_month` dict. (From spec document)

**Q3:** Categorization Trigger - Two-step flow or single atomic operation?
**Answer:** Two-step flow. `POST /api/categorize` is called after user reviews preview and selects months/import mode. (From spec document)

**Q4:** Replace vs Merge Import Modes definitions?
**Answer:** Replace overwrites existing data for the month. Merge adds new transactions, skipping duplicates based on key: `{date}_{description}_{amount}_{account}`. (From spec document)

**Q5:** State Management Between Preview and Categorization?
**Answer:** **Re-upload approach**. User re-sends the CSV file with the categorize request. Chosen for simplicity since this is a local-first, single-user app. Stateless API = no session management, no cleanup, no complexity.

**Q6:** Error Handling Scope?
**Answer:** Detailed error handling defined in spec:

- Invalid CSV format → 400
- No transactions found → 400
- Claude API failure → 502
- Invalid month format → 400

**Q7:** What should be excluded?
**Answer:** Backend API only. Excludes frontend UI (roadmap item #7), progress indicators, database schema changes (models exist from item #1).

### Existing Code to Reference

**Similar Features Identified:**

| Service         | Path                                  | Purpose                                   |
| --------------- | ------------------------------------- | ----------------------------------------- |
| CSV Parser      | `backend/app/services/csv_parser.py`  | Parses Bankin' CSV, groups by month       |
| Categorizer     | `backend/app/services/categorizer.py` | Claude API integration for categorization |
| Calculator      | `backend/app/services/calculator.py`  | Score calculation (0-3)                   |
| Service Schemas | `backend/app/services/schemas/`       | Input/output types for services           |

Supporting files:

- `backend/app/services/categorization_prompt.py` - Claude prompt
- `backend/app/services/category_mapping.py` - Category mappings
- `backend/app/services/categorization_cache.py` - Caching logic
- `backend/app/services/exceptions.py` - Service exceptions

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

N/A

## Detailed Specification Reference

Full specification exists at: `docs/product-development/features/05-upload-categorize-api.md`

This document contains:

- Complete API endpoint definitions with request/response schemas
- Workflow diagrams
- Data flow diagrams
- Error handling table
- Testing requirements
- File structure
- API cost considerations

## Requirements Summary

### Functional Requirements

1. **Upload Endpoint** (`POST /api/upload`)
   - Accept CSV file via multipart/form-data
   - Validate Bankin' CSV format
   - Parse and group transactions by month
   - Return preview with month summaries and transaction lists

2. **Categorize Endpoint** (`POST /api/categorize`)
   - Accept CSV file (re-upload), selected months, and import mode
   - Categorize transactions via Claude API (batch of 50)
   - Calculate Money Map score per month
   - Store results in database
   - Return results with scores and API call count

3. **Import Modes**
   - Replace: Delete existing month data before import
   - Merge: Add new transactions, skip duplicates

### Response Schemas

```python
# Upload Response
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

# Categorize Response
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

### Scope Boundaries

**In Scope:**

- `POST /api/upload` endpoint
- `POST /api/categorize` endpoint
- Request/response Pydantic schemas
- Integration with existing services (parser, categorizer, calculator)
- Database persistence (months + transactions tables)
- Error handling with appropriate HTTP status codes

**Out of Scope:**

- Frontend upload UI (roadmap item #7)
- Progress indicators / WebSocket updates
- Database schema changes (models exist)
- New service logic (services exist)

### Technical Considerations

- Re-upload approach for state management (stateless API)
- Batch 50 transactions per Claude API call
- Pre-filter internal transfers before API call
- Track `total_api_calls` in response for cost monitoring
- Use existing repository pattern for database operations
- Use FastAPI `Depends()` for dependency injection

### File Structure

```text
backend/app/
├── routers/
│   └── upload.py          # NEW: POST /api/upload, POST /api/categorize
├── schemas/
│   └── upload.py          # NEW: Request/Response models
├── services/
│   ├── csv_parser.py      # EXISTS
│   ├── categorizer.py     # EXISTS
│   └── calculator.py      # EXISTS
└── db/
    └── crud.py            # EXISTS: Repository operations
```

### Testing Requirements

**Unit Tests:**

1. Upload endpoint - valid CSV returns correct month summaries
2. Upload endpoint - invalid format returns 400
3. Upload endpoint - empty file returns error
4. Categorize endpoint - replace mode clears existing data
5. Categorize endpoint - merge mode skips duplicates
6. Categorize endpoint - invalid month format returns 400

**Integration Tests:**

1. Full upload → categorize → verify database flow
2. Multi-month file processing
3. Claude API error handling (mock failures)
