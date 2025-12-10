# Spec Requirements: Historical Data API

## Initial Description

Extend the months API to return aggregated history for the last N months with score and percentage trends. This is roadmap item #10, sized as `S` (small).

## Requirements Source

Requirements are derived from the existing PRD: `docs/product-development/features/10-historical-data-api.md`

## Requirements Discussion

### PRD Analysis

The PRD provides comprehensive requirements. Key decisions documented:

**Q1:** Default number of months?
**Answer:** 12 months default, maximum 24 months allowed.

**Q2:** How are trends calculated?
**Answer:** Score trend compares average of last 3 months vs average of previous 3 months:

- `improving`: last 3 avg > previous 3 avg
- `declining`: last 3 avg < previous 3 avg
- `stable`: no significant change

**Q3:** New endpoint or extend existing?
**Answer:** New endpoint: `GET /api/months/history`

**Q4:** Include aggregated totals?
**Answer:** Yes, per-month data plus a `summary` object with:

- `total_months`: count of months returned
- `average_score`: average across all months
- `score_trend`: improving/declining/stable
- `best_month`: year/month/score of highest score
- `worst_month`: year/month/score of lowest score

**Q5:** Handle missing months (gaps)?
**Answer:** Exclude them (not filled with zeros or null values).

**Q6:** What's explicitly out of scope?
**Answer:**

- Filtering by date range (start/end dates)
- Category-level trends (e.g., trend per subcategory)
- Comparison between non-consecutive periods
- Data interpolation for missing months

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Monthly Data API - Path: `backend/app/routers/months.py`
- Components to potentially reuse: `MonthSummary` response model pattern
- Backend logic to reference: `months_service.get_all_months_with_counts()`

**Implementation Locations (from PRD):**

- Router: `backend/app/routers/months.py`
- CRUD: `backend/app/db/crud.py`
- Schemas: `backend/app/responses/months.py` (extend existing)

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

N/A - This is a backend-only API feature. Frontend charts (items #11, #12) are separate roadmap items.

## Requirements Summary

### Functional Requirements

1. **New API Endpoint**: `GET /api/months/history`
2. **Query Parameter**: `months` (int, default: 12, range: 1-24)
3. **Response Structure**:
   - `months` array with per-month data (year, month, month_label, totals, percentages, score, score_label)
   - `summary` object with aggregated insights (total_months, average_score, score_trend, best_month, worst_month)
4. **Ordering**: Chronological (oldest first)
5. **Missing Months**: Excluded from response
6. **Score Trend Logic**: Compare last 3 months avg vs previous 3 months avg

### Non-Functional Requirements

- Query performance < 100ms for 12 months of data
- Support downstream features: Score Evolution Chart (#11), Spending Breakdown Chart (#12), History Page UI (#13)

### Reusability Opportunities

- Extend existing `MonthSummary` model or create similar `MonthHistory` model
- Reuse database query patterns from `get_all_months_with_counts()`
- Follow existing error handling pattern (`MonthDataError`, HTTP 503 for DB errors)

### Scope Boundaries

**In Scope:**

- New `/api/months/history` endpoint
- Configurable month limit (1-24)
- Per-month financial data (totals, percentages, score)
- Summary with trend analysis
- Unit tests for all business rules

**Out of Scope:**

- Date range filtering (start/end dates)
- Category-level trends
- Comparison between non-consecutive periods
- Data interpolation for missing months
- Frontend components (separate roadmap items #11-13)

### Technical Considerations

- Database query: Simple SELECT with ORDER BY and LIMIT
- Response models: Pydantic models following existing patterns
- Score trend calculation: Service-layer logic comparing 3-month averages
- Integration: Fits naturally in existing months router

### Testing Requirements (from PRD)

Unit Tests:

- `test_history_returns_correct_months`
- `test_history_chronological_order`
- `test_history_default_limit`
- `test_history_max_limit`
- `test_history_empty_database`
- `test_score_trend_improving`
- `test_score_trend_declining`
- `test_score_trend_stable`

Integration Tests:

- Test with realistic data spanning 12+ months
- Verify response time < 100ms
