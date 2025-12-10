# PRD: Historical Data API

## 1. Overview

### 1.1 Feature Summary

Extend the existing months API to return aggregated historical data for the last N months, including score progression and percentage trends. This API enables the frontend to display evolution charts and trend analysis.

### 1.2 Problem Statement

Currently, the application can only retrieve data for a single month at a time. Users need to visualize their financial progress over time to:

- Track score evolution month-over-month
- Identify spending trends in Core/Choice/Compound categories
- Understand their financial trajectory

### 1.3 Success Criteria

- API returns historical data for configurable number of months (default: 12)
- Response includes all metrics needed for evolution charts
- Query performance < 100ms for 12 months of data
- Supports the Score Evolution Chart (item #11) and Spending Breakdown Chart (item #12)

## 2. Functional Requirements

### 2.1 API Endpoint

**Endpoint:** `GET /api/months/history`

**Query Parameters:**

| Parameter | Type | Default | Description                         |
| --------- | ---- | ------- | ----------------------------------- |
| `months`  | int  | 12      | Number of months to retrieve (1-24) |

### 2.2 Response Schema

```json
{
  "months": [
    {
      "year": 2025,
      "month": 10,
      "month_label": "Oct 2025",
      "total_income": 2823.29,
      "total_core": 1245.00,
      "total_choice": 678.50,
      "total_compound": 899.79,
      "core_percentage": 44.1,
      "choice_percentage": 24.0,
      "compound_percentage": 31.9,
      "score": 3,
      "score_label": "Great"
    }
  ],
  "summary": {
    "total_months": 10,
    "average_score": 2.3,
    "score_trend": "improving",
    "best_month": {"year": 2025, "month": 10, "score": 3},
    "worst_month": {"year": 2025, "month": 2, "score": 1}
  }
}
```

### 2.3 Business Rules

1. **Ordering**: Months are returned in chronological order (oldest first)
2. **Missing Months**: Months without data are excluded (not filled with zeros)
3. **Score Trend Calculation**:
   - `improving`: Average score of last 3 months > average of previous 3 months
   - `declining`: Average score of last 3 months < average of previous 3 months
   - `stable`: No significant change
4. **Limit**: Maximum 24 months of history can be requested

## 3. Technical Specifications

### 3.1 Database Query

Query the `months` table ordered by year and month descending, limited to N records:

```sql
SELECT
    year, month, total_income, total_core, total_choice, total_compound,
    core_percentage, choice_percentage, compound_percentage,
    score, score_label
FROM months
ORDER BY year DESC, month DESC
LIMIT :months
```

### 3.2 Implementation Location

| Component | File                                                          |
| --------- | ------------------------------------------------------------- |
| Router    | `backend/app/routers/months.py`                               |
| CRUD      | `backend/app/db/crud.py`                                      |
| Schemas   | `backend/app/schemas/months.py` (new file or extend existing) |

### 3.3 Response Models (Pydantic)

```python
class MonthHistory(BaseModel):
    year: int
    month: int
    month_label: str
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int
    score_label: str

class HistorySummary(BaseModel):
    total_months: int
    average_score: float
    score_trend: Literal["improving", "declining", "stable"]
    best_month: dict[str, int | str]
    worst_month: dict[str, int | str]

class HistoryResponse(BaseModel):
    months: list[MonthHistory]
    summary: HistorySummary
```

## 4. Dependencies

### 4.1 Prerequisites

- Items #1-6 must be completed (database models, monthly data API)
- At least 2+ months of data should exist for meaningful trends

### 4.2 Downstream Dependencies

This API enables:

- Item #11: Score Evolution Chart
- Item #12: Spending Breakdown Chart
- Item #13: History Page UI

## 5. Testing Requirements

### 5.1 Unit Tests

| Test Case                             | Description                                   |
| ------------------------------------- | --------------------------------------------- |
| `test_history_returns_correct_months` | Verify correct number of months returned      |
| `test_history_chronological_order`    | Verify oldest-first ordering                  |
| `test_history_default_limit`          | Verify default is 12 months                   |
| `test_history_max_limit`              | Verify 24 month maximum enforced              |
| `test_history_empty_database`         | Verify graceful handling with no data         |
| `test_score_trend_improving`          | Verify trend calculation for improving scores |
| `test_score_trend_declining`          | Verify trend calculation for declining scores |
| `test_score_trend_stable`             | Verify trend calculation for stable scores    |

### 5.2 Integration Tests

- Test with realistic data spanning 12+ months
- Verify response time < 100ms

## 6. Acceptance Criteria

- [ ] `GET /api/months/history` returns historical data
- [ ] `months` query parameter limits results (default: 12, max: 24)
- [ ] Response includes `months` array with all required fields
- [ ] Response includes `summary` with trend analysis
- [ ] Months are ordered chronologically (oldest first)
- [ ] Missing months are excluded from response
- [ ] Score trend is calculated correctly
- [ ] API documentation updated in FastAPI docs
- [ ] Unit tests achieve 80%+ coverage
- [ ] Response time < 100ms for 12 months

## 7. Out of Scope

- Filtering by date range (start/end dates)
- Category-level trends (e.g., trend per subcategory)
- Comparison between non-consecutive periods
- Data interpolation for missing months
