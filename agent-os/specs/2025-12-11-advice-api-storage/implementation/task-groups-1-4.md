# Implementation: Advice API and Storage (Task Groups 1-4)

**Date:** 2025-12-11
**Task Groups:** 1-4 (Exception and Service Layer, Response Models, Router, Integration Tests)
**Implementer:** implement-task command

## Summary

Implemented the Advice API and Storage feature, exposing the existing `AdviceGenerator` service via REST API. The implementation adds CRUD service functions, Pydantic response models, and two endpoints for generating and retrieving personalized financial advice.

## Architecture Approach

Selected the **Minimal approach** that maximizes code reuse:
- Pure service functions (no class) matching `months.py` pattern
- Factory methods on response models (`from_json()`, `from_service_response()`)
- Direct `AdviceGenerator` instantiation in router (simpler than dependency injection)
- Upsert pattern for one advice per month

## Files Modified

| File | Change |
|------|--------|
| `backend/app/services/exceptions.py` | Added `AdviceQueryError` exception class inheriting from `AdviceGenerationError` |
| `backend/app/main.py` | Imported and registered advice router |

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/services/advice.py` | CRUD functions: `get_advice_by_month_id()`, `create_or_update_advice()`, `month_to_month_data()`, `advice_response_to_json()` |
| `backend/app/responses/advice.py` | Response models: `ProblemAreaResponse`, `AdviceData`, `GenerateAdviceRequest`, `GenerateAdviceResponse`, `GetAdviceResponse` |
| `backend/app/routers/advice.py` | REST endpoints: `POST /api/advice/generate`, `GET /api/advice/{year}/{month}` |
| `backend/tests/units/services/test_advice_service.py` | 6 unit tests for service functions |
| `backend/tests/units/responses/test_advice_responses.py` | 5 unit tests for response model converters |
| `backend/tests/units/routers/test_advice_router.py` | 8 unit tests for router endpoints |
| `backend/tests/integration/test_advice_api.py` | 5 integration tests for end-to-end workflows |

## Key Implementation Details

### Service Layer (`advice.py`)
- Uses `model_dump_json()` for serialization (Pydantic's built-in method)
- Upsert pattern: query for existing, update if found, create if not
- `month_to_month_data()` converts Month model to MonthData DTO for AdviceGenerator
- All functions wrap SQLAlchemyError in `AdviceQueryError`

### Response Models (`responses/advice.py`)
- `AdviceData.from_json()` parses stored JSON from database
- `AdviceData.from_service_response()` converts fresh advice from Claude API
- Separate response models from service DTOs (clean architecture)

### Router (`routers/advice.py`)
- POST endpoint: checks cache first, generates if needed, stores result
- GET endpoint: returns existing advice or `exists=False`
- Error mapping: 404 (month not found), 400 (insufficient data), 503 (API/DB unavailable), 500 (unexpected)

### Data Flow
```bash
POST /api/advice/generate
  → Check month exists (404 if not)
  → Check cached advice (return if exists and not regenerating)
  → Fetch history (last 3 months)
  → Convert to MonthData DTOs
  → Call AdviceGenerator.generate_advice()
  → Serialize to JSON and store
  → Return GenerateAdviceResponse

GET /api/advice/{year}/{month}
  → Check month exists (404 if not)
  → Query stored advice
  → Return GetAdviceResponse with exists flag
```

## Integration Points

- **Months service**: Uses `get_month_by_year_month()` and `get_months_history()`
- **AdviceGenerator**: Creates instance with API key from settings
- **Database**: Uses existing `Advice` model with `advice_text` column (JSON storage)
- **Router registration**: Added to `app/main.py` with other routers

## Testing Notes

- **24 feature-specific tests** (6 service + 5 response + 8 router + 5 integration)
- **286 total tests pass** (no regressions)
- All tests mock Claude API to avoid real API calls
- Integration tests use pytest fixtures with test database
- Tests verify caching logic, error handling, and JSON persistence
