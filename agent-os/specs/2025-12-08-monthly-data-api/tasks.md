# Task Breakdown: Monthly Data API

## Overview

| Metric               | Value                        |
| -------------------- | ---------------------------- |
| Total Tasks          | 14                           |
| Estimated Complexity | Low                          |
| Primary Stack        | FastAPI + SQLAlchemy         |
| New Files            | 3 (router, service, schemas) |
| Modified Files       | 1 (main.py)                  |

## Task List

### Schema Layer

#### Task Group 1: Pydantic Response Schemas

**Dependencies:** None

- [ ] 1.0 Complete schema layer
  - [ ] 1.1 Create `backend/app/schemas/months.py` with response models
    - `MonthSummary`: id, year, month, totals, percentages, score, score_label, transaction_count, timestamps
    - `TransactionResponse`: id, date, description, account, amount, categories, is_manually_corrected
    - `PaginationInfo`: page, page_size, total_items, total_pages
    - `MonthsListResponse`: months array + total count
    - `MonthDetailResponse`: month + transactions + pagination
    - Follow pattern from: `backend/app/schemas/upload.py`
    - Use `Field(ge=, le=)` for validation constraints
  - [ ] 1.2 Add `ScoreLabelLiteral` type alias
    - Define as `Literal["Poor", "Need Improvement", "Okay", "Great"]`
    - Reuse pattern from upload.py line 8

**Acceptance Criteria:**

- All 5 response models defined with correct field types
- Field validations match spec (month 1-12, page_size 1-100, etc.)
- Models can serialize from SQLAlchemy objects

---

### Service Layer

#### Task Group 2: Query Service

**Dependencies:** Task Group 1

- [ ] 2.0 Complete service layer
  - [ ] 2.1 Write 4 focused tests for service methods
    - Test `get_all_months()` returns months ordered by date desc
    - Test `get_month_by_year_month()` returns None when not found
    - Test `get_transactions_filtered()` applies category filter correctly
    - Test `get_transactions_filtered()` returns correct pagination tuple
  - [ ] 2.2 Create `backend/app/services/months.py` with `MonthsService` class
    - Stateless service receiving `db: Session` per method call
    - Follow pattern from: `backend/app/services/upload.py`
  - [ ] 2.3 Implement `get_all_months(db: Session) -> list[Month]`
    - Query: `db.query(Month).order_by(Month.year.desc(), Month.month.desc()).all()`
  - [ ] 2.4 Implement `get_month_by_year_month(db, year, month) -> Month | None`
    - Query: `db.query(Month).filter(Month.year == year, Month.month == month).first()`
  - [ ] 2.5 Implement `get_transactions_filtered()` with filtering and pagination
    - Parameters: db, month_id, category_type, search, start_date, end_date, page, page_size
    - Build query with chained `.filter()` calls (AND logic)
    - Use `.ilike(f"%{search}%")` for case-insensitive search
    - Return tuple: `(list[Transaction], total_count)`
    - Apply `.offset((page - 1) * page_size).limit(page_size)`
    - Order by `Transaction.date.desc()`
  - [ ] 2.6 Ensure service tests pass
    - Run: `cd backend && uv run pytest tests/services/test_months.py -v`

**Acceptance Criteria:**

- All 4 service tests pass
- `get_all_months()` returns months in correct order
- `get_month_by_year_month()` returns Month or None
- `get_transactions_filtered()` applies all filters correctly
- Pagination returns correct slice with total count

---

### Router Layer

#### Task Group 3: API Endpoints

**Dependencies:** Task Group 2

- [ ] 3.0 Complete router layer
  - [ ] 3.1 Write 4 focused tests for API endpoints
    - Test `GET /api/months` returns list with correct structure
    - Test `GET /api/months/{year}/{month}` returns 404 when not found
    - Test `GET /api/months/{year}/{month}` returns paginated transactions
    - Test `GET /api/months/{year}/{month}?category_type=CORE` filters correctly
  - [ ] 3.2 Create `backend/app/routers/months.py` with router setup
    - `APIRouter(prefix="/api", tags=["months"])`
    - Add `# ruff: noqa: B008` for Depends() false positive
    - Create `_get_months_service()` dependency factory
    - Import `get_db` from `app.db.database`
  - [ ] 3.3 Implement `GET /api/months` endpoint
    - Response model: `MonthsListResponse`
    - Call `service.get_all_months(db)`
    - Transform to `MonthSummary` with `transaction_count = len(month.transactions)`
    - NumPy docstring with Returns section
  - [ ] 3.4 Implement `GET /api/months/{year}/{month}` endpoint
    - Path parameters: `year: int`, `month: int = Path(ge=1, le=12)`
    - Query parameters: `category_type`, `search`, `start_date`, `end_date`, `page`, `page_size`
    - Use `Query(default=...)` with descriptions for Swagger docs
    - Return 404 with `HTTPException(status_code=404, detail="Month not found")`
    - Build `PaginationInfo` with `total_pages = ceil(total_items / page_size)`
    - NumPy docstring with Parameters, Returns, Raises sections
  - [ ] 3.5 Ensure router tests pass
    - Run: `cd backend && uv run pytest tests/routers/test_months.py -v`

**Acceptance Criteria:**

- All 4 router tests pass
- `GET /api/months` returns correct response structure
- `GET /api/months/{year}/{month}` returns month detail with transactions
- 404 returned when month doesn't exist
- All query parameters work correctly

---

### Integration Layer

#### Task Group 4: Router Registration & Final Verification

**Dependencies:** Task Group 3

- [ ] 4.0 Complete integration
  - [ ] 4.1 Register router in `backend/app/main.py`
    - Add import: `from app.routers import months`
    - Add registration: `app.include_router(months.router)`
  - [ ] 4.2 Run all Monthly Data API tests
    - Run: `cd backend && uv run pytest tests/services/test_months.py tests/routers/test_months.py -v`
    - Verify all 8 tests pass
  - [ ] 4.3 Manual API verification
    - Start server: `make dev-backend`
    - Test `GET http://localhost:8000/api/months`
    - Test `GET http://localhost:8000/api/months/2025/10`
    - Test filtering: `?category_type=CORE&search=salaire`
    - Verify Swagger docs at `/docs` show both endpoints

**Acceptance Criteria:**

- Router registered and accessible
- All 8 feature tests pass
- Both endpoints return correct responses
- Swagger documentation displays correctly
- Filtering and pagination work as expected

---

## Execution Order

| Order | Task Group              | Reason                           |
| ----- | ----------------------- | -------------------------------- |
| 1     | Schema Layer (Group 1)  | Response models needed by router |
| 2     | Service Layer (Group 2) | Query logic needed by router     |
| 3     | Router Layer (Group 3)  | Depends on schemas and service   |
| 4     | Integration (Group 4)   | Final wiring and verification    |

## Files Summary

### New Files (3)

| File                             | Purpose                               |
| -------------------------------- | ------------------------------------- |
| `backend/app/schemas/months.py`  | Pydantic response models              |
| `backend/app/services/months.py` | Query logic with filtering/pagination |
| `backend/app/routers/months.py`  | API endpoints                         |

### Modified Files (1)

| File                  | Change                             |
| --------------------- | ---------------------------------- |
| `backend/app/main.py` | Add router import and registration |

### Test Files (2)

| File                                    | Tests           |
| --------------------------------------- | --------------- |
| `backend/tests/services/test_months.py` | 4 service tests |
| `backend/tests/routers/test_months.py`  | 4 router tests  |

## Test Summary

| Phase         | Tests | Scope                                       |
| ------------- | ----- | ------------------------------------------- |
| Service Layer | 4     | Query methods, filtering, pagination        |
| Router Layer  | 4     | Endpoints, 404 handling, response structure |
| **Total**     | **8** | Full feature coverage                       |
