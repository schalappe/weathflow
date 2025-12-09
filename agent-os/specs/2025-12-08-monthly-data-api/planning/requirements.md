# Spec Requirements: Monthly Data API

## Initial Description

Create endpoints to retrieve month data including totals, percentages, score, and transaction list with filtering capabilities.

## Requirements Discussion

### Source Document

All requirements were pre-documented in: `docs/product-development/features/06-monthly-data-api.md`

This comprehensive specification already defines:

- API endpoints and their contracts
- Request/response schemas
- Business rules
- Acceptance criteria

### Key Decisions from Spec

**Q1:** Endpoint structure?
**Answer:** Two endpoints:

- `GET /api/months` - List all months with summary data
- `GET /api/months/{year}/{month}` - Single month details with transactions (uses year/month path params, not month_id)

**Q2:** Transaction filtering capabilities?
**Answer:** Three filter types:

- `category_type`: Filter by Money Map type (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED)
- `start_date` / `end_date`: Date range filtering within the month
- `search`: Case-insensitive partial match on transaction description

**Q3:** Pagination approach?
**Answer:** Offset-based pagination:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- Response includes `total_items` and `total_pages`

**Q4:** All months listing format?
**Answer:** Summary list with score, totals, percentages, and transaction_count (no full transaction details)

**Q5:** Percentage/variance display?
**Answer:** Percentages included (core_percentage, choice_percentage, compound_percentage). No variance from 50/30/20 targets included.

**Q6:** Exclusions?
**Answer:**

- Advice: Excluded (handled by Advice API - roadmap item #15)
- Historical trends: Excluded (handled by Historical Data API - roadmap item #10)

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Upload and Categorize API - Path: `backend/app/routers/upload.py`
- Database Models: `backend/app/db/models.py`
- CRUD Operations: `backend/app/db/crud.py`
- Score Calculation Service: `backend/app/services/score.py`

**Patterns to Follow:**

- FastAPI router structure from existing routers
- Pydantic schemas for request/response validation
- Repository pattern for database access
- Service layer for business logic

### Follow-up Questions

No follow-up questions needed - spec is comprehensive.

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

N/A - API endpoint specification does not require visual mockups.

## Requirements Summary

### Functional Requirements

1. **FR1: Get Single Month Data** - Retrieve complete data for a specific month including metadata, totals, percentages, score, and transactions
2. **FR2: List All Months** - Retrieve summary list of all months ordered by date (most recent first)
3. **FR3: Transaction Filtering** - Filter by category_type, date range, and search description
4. **FR4: Pagination** - Support paginated transaction lists with configurable page size

### Response Schemas Required

- `MonthSummary`: Month metadata with totals, percentages, score, score_label
- `TransactionResponse`: Individual transaction data with Money Map categorization
- `PaginationInfo`: Page metadata (page, page_size, total_items, total_pages)
- `MonthListResponse`: Wrapper for list of months
- `MonthDetailResponse`: Wrapper for single month with transactions and pagination

### Reusability Opportunities

- Existing SQLAlchemy models for Month and Transaction
- Existing score calculation logic in `services/score.py`
- Existing CRUD patterns in `db/crud.py`
- Router patterns from `routers/upload.py`

### Scope Boundaries

**In Scope:**

- `GET /api/months` endpoint
- `GET /api/months/{year}/{month}` endpoint
- Transaction filtering (category, date range, search)
- Pagination for transaction lists
- Proper 404 handling for non-existent months

**Out of Scope:**

- Advice generation/retrieval (separate API)
- Historical trend aggregation (separate API)
- Transaction editing/correction (roadmap item #9)
- Data export functionality (roadmap item #18)

### Technical Considerations

- Score is pre-calculated and stored (not computed per request)
- Percentages are relative to total_income
- Compound = total_income - total_core - total_choice
- Filters use AND logic (all conditions must match)
- Search is case-insensitive partial match

### Business Rules

| Score | Label            | Condition                                      |
| ----- | ---------------- | ---------------------------------------------- |
| 3     | Great            | Core ≤ 50% AND Choice ≤ 30% AND Compound ≥ 20% |
| 2     | Okay             | 2 of 3 conditions met                          |
| 1     | Need Improvement | 1 of 3 conditions met                          |
| 0     | Poor             | No conditions met                              |

### Acceptance Criteria

- [ ] `GET /api/months` returns list of all months with summary data
- [ ] `GET /api/months/{year}/{month}` returns month details with transactions
- [ ] Returns 404 when month does not exist
- [ ] Transactions can be filtered by `category_type`
- [ ] Transactions can be filtered by date range (`start_date`, `end_date`)
- [ ] Transactions can be searched by description (case-insensitive)
- [ ] Pagination works correctly with `page` and `page_size` parameters
- [ ] Response includes correct pagination metadata
- [ ] All response schemas are properly validated with Pydantic
