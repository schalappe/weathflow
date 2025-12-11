# Spec Requirements: Advice API and Storage

## Initial Description

Create endpoints to generate and retrieve personalized financial advice, storing generated advice in the database for each month. This feature exposes the Advice Generation Service (Feature 14) via REST API and persists advice for future retrieval.

## Requirements Discussion

### Source Document

All requirements were derived from the existing feature specification document:
`docs/product-development/features/15-advice-api-storage.md`

### Key Decisions from Feature Document

**Q1:** Storage Format - Should we serialize full AdviceResponse as JSON or store raw text?
**Answer:** Store as JSON in `advice_text` column containing: analysis, problem_areas, recommendations, encouragement.

**Q2:** One Advice Per Month - Replace or append on regeneration?
**Answer:** Each month can only have one advice record. Regenerating advice replaces the existing record.

**Q3:** API Endpoints - What URL structure?
**Answer:**

- `POST /api/advice/generate` - Generate (or regenerate) advice for a month
- `GET /api/advice/{year}/{month}` - Retrieve stored advice for a month

**Q4:** Generate vs Retrieve Logic - Should GET auto-generate if missing?
**Answer:** No. POST returns cached advice if exists and `regenerate=False`. GET returns existing advice or indicates none exists (no auto-generation).

**Q5:** Error Handling - What error codes?
**Answer:**

- 404: Month not found
- 400: Insufficient historical data (< 2 months)
- 500: Claude API failure

**Q6:** Exclusions?
**Answer:** Rate limiting mentioned as "consider adding" but not required for this feature. No advice versioning/history.

### Existing Code to Reference

**Similar Features Identified:**

- Router Pattern: `backend/app/routers/months.py` - Similar GET endpoint with year/month path params, error handling pattern
- Advice Model: `backend/app/db/models/advice.py` - Already exists with id, month_id, advice_text, generated_at
- Advice Service: `backend/app/services/advisor.py` - AdviceGenerator class already implemented
- DTOs: `backend/app/services/dto/advice.py` - AdviceResponse, ProblemArea, MonthData already defined

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

N/A - This is a backend-only feature (API endpoints).

## Requirements Summary

### Functional Requirements

- POST `/api/advice/generate` endpoint accepts `{year, month, regenerate}` and generates advice
- GET `/api/advice/{year}/{month}` endpoint retrieves stored advice
- Advice is persisted in the `advice` table as JSON
- Endpoint returns existing advice if already generated and `regenerate=False`
- Endpoint supports `regenerate=True` flag to force new advice generation
- Response includes `was_cached` flag to indicate if advice was freshly generated

### API Response Models

**GenerateAdviceResponse:**

```python
{
    "success": bool,
    "advice": AdviceData,
    "generated_at": datetime,
    "was_cached": bool
}
```

**GetAdviceResponse:**

```python
{
    "success": bool,
    "advice": AdviceData | None,
    "generated_at": datetime | None,
    "exists": bool
}
```

### Reusability Opportunities

- Existing `Advice` model in `backend/app/db/models/advice.py`
- Existing `AdviceGenerator` service in `backend/app/services/advisor.py`
- Existing DTOs in `backend/app/services/dto/advice.py`
- Router pattern from `backend/app/routers/months.py`
- Service layer pattern from `backend/app/services/months.py`

### Scope Boundaries

**In Scope:**

- POST `/api/advice/generate` endpoint
- GET `/api/advice/{year}/{month}` endpoint
- CRUD operations for advice (create_or_update, get_by_month)
- JSON serialization/deserialization of advice data
- Error handling (404, 400, 500)
- Unit and integration tests

**Out of Scope:**

- Rate limiting for Claude API calls
- Advice versioning/history (multiple advice per month)
- Advice Panel UI (Feature 16)

### Technical Considerations

- Store advice as JSON text for flexibility in schema changes
- Use existing `AdviceGenerator` service from Feature 14
- Follow existing router patterns in `months.py`
- Use `Depends(get_db)` for database session injection
- Handle `InsufficientDataError` from advisor service
