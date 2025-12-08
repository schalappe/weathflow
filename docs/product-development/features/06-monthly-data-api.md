# Monthly Data API Specification

## Overview

Create FastAPI endpoints to retrieve month data including totals, percentages, score, and transaction list with filtering capabilities.

**Size**: Small (S)
**Dependencies**: Items 1-5 (Database Models, CSV Parser, Categorization, Score Calculation, Upload API)

---

## Functional Requirements

### FR1: Get Single Month Data

Retrieve complete data for a specific month including:

- Month metadata (year, month, created_at, updated_at)
- Financial totals (income, core, choice, compound)
- Percentages vs income
- Score (0-3) and score label (Great/Okay/Need Improvement/Poor)
- List of transactions for that month

### FR2: List All Months

Retrieve a summary list of all months with data in the system, ordered by date (most recent first).

### FR3: Transaction Filtering

Filter transactions within a month by:

- Category type (`INCOME`, `CORE`, `CHOICE`, `COMPOUND`, `EXCLUDED`)
- Date range (start_date, end_date)
- Search by description (partial match, case-insensitive)

### FR4: Pagination

Support pagination for transaction lists:

- Default page size: 50
- Maximum page size: 100
- Return total count for pagination UI

---

## API Endpoints

### GET /api/months

List all months with summary data.

**Response:**

```json
{
  "months": [
    {
      "id": 1,
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
      "score_label": "Great",
      "transaction_count": 156,
      "created_at": "2025-10-01T10:00:00Z",
      "updated_at": "2025-10-31T18:30:00Z"
    }
  ],
  "total": 10
}
```

### GET /api/months/{year}/{month}

Get detailed data for a specific month.

**Path Parameters:**

- `year`: int (e.g., 2025)
- `month`: int (1-12)

**Query Parameters:**

- `category_type`: str | None - Filter transactions by Money Map type
- `search`: str | None - Search in transaction descriptions
- `start_date`: date | None - Filter transactions from this date
- `end_date`: date | None - Filter transactions until this date
- `page`: int = 1 - Page number
- `page_size`: int = 50 - Items per page (max 100)

**Response (200 OK):**

```json
{
  "month": {
    "id": 1,
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
    "score_label": "Great",
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-31T18:30:00Z"
  },
  "transactions": [
    {
      "id": 1,
      "date": "2025-10-29",
      "description": "Virement Salaire",
      "account": "Compte De Dépôts",
      "amount": 2823.29,
      "bankin_category": "Entrées d'argent",
      "bankin_subcategory": "Salaires",
      "money_map_type": "INCOME",
      "money_map_subcategory": "Job",
      "is_manually_corrected": false
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 156,
    "total_pages": 4
  }
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Month not found"
}
```

---

## Data Models

### MonthSummary (Response Schema)

```python
class MonthSummary(BaseModel):
    id: int
    year: int
    month: int
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int
    score_label: str
    transaction_count: int
    created_at: datetime
    updated_at: datetime
```

### TransactionResponse (Response Schema)

```python
class TransactionResponse(BaseModel):
    id: int
    date: date
    description: str
    account: str | None
    amount: float
    bankin_category: str | None
    bankin_subcategory: str | None
    money_map_type: str
    money_map_subcategory: str | None
    is_manually_corrected: bool
```

### PaginationInfo (Response Schema)

```python
class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
```

---

## Business Rules

1. **Score Calculation**: Score is pre-calculated and stored in the months table (not computed on each request)
2. **Percentages**: All percentages are relative to total_income
3. **Compound Calculation**: `total_compound = total_income - total_core - total_choice`
4. **Empty Month**: Return 404 if no month exists for the given year/month
5. **Filtering**: Filters are applied with AND logic (all conditions must match)
6. **Search**: Case-insensitive partial match on transaction description

---

## Score Labels Reference

| Score | Label            | Condition                                      |
| ----- | ---------------- | ---------------------------------------------- |
| 3     | Great            | Core ≤ 50% AND Choice ≤ 30% AND Compound ≥ 20% |
| 2     | Okay             | 2 of 3 conditions met                          |
| 1     | Need Improvement | 1 of 3 conditions met                          |
| 0     | Poor             | No conditions met                              |

---

## Acceptance Criteria

- [ ] `GET /api/months` returns list of all months with summary data
- [ ] `GET /api/months/{year}/{month}` returns month details with transactions
- [ ] Returns 404 when month does not exist
- [ ] Transactions can be filtered by `category_type`
- [ ] Transactions can be filtered by date range (`start_date`, `end_date`)
- [ ] Transactions can be searched by description (case-insensitive)
- [ ] Pagination works correctly with `page` and `page_size` parameters
- [ ] Response includes correct pagination metadata
- [ ] All response schemas are properly validated with Pydantic
