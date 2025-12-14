# Backend Architecture

> **Last Updated:** December 2025
> **Framework:** FastAPI 0.115+ | Python 3.12+ | SQLite + SQLAlchemy 2.0+

This document provides a comprehensive guide to the Money Map Manager backend architecture, explaining the layers, patterns, and data flow that power the application.

---

## Table of Contents

- [Overview](#overview)
- [Clean Architecture Layers](#clean-architecture-layers)
- [API Endpoints Reference](#api-endpoints-reference)
- [Database Schema](#database-schema)
- [Service Layer](#service-layer)
- [Repository Pattern](#repository-pattern)
- [Transaction Processing Flow](#transaction-processing-flow)
- [AI Integration](#ai-integration)
- [Error Handling](#error-handling)
- [Testing Strategy](#testing-strategy)

---

## Overview

The backend follows **Clean Architecture** principles with strict separation of concerns across four layers:

```text
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER (FastAPI Routers)                       │
│  - Thin controllers that delegate to services               │
│  - Input validation via Pydantic                            │
│  - HTTP response handling                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓ Depends on
┌─────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER (Services)                               │
│  - Business logic orchestration                             │
│  - Multi-step workflows                                     │
│  - External API calls                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓ Depends on
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN LAYER (Models, Enums, Business Rules)               │
│  - Core business entities                                   │
│  - Business rule validation                                 │
│  - Money Map framework logic                                │
└─────────────────────────────────────────────────────────────┘
                           ↓ Depends on
┌─────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER                                       │
│  - Database access via repositories                         │
│  - External API clients (Claude)                            │
│  - Configuration management                                 │
└─────────────────────────────────────────────────────────────┘
```

**Key Principles:**

- Dependencies point inward (outer layers depend on inner layers)
- Core business logic has no dependencies on frameworks
- Easy to test and swap implementations

---

## Clean Architecture Layers

### 1. Presentation Layer (`backend/app/api/`)

Thin FastAPI route handlers that:

- Validate incoming requests via Pydantic models
- Delegate work to service layer
- Map service responses to HTTP responses
- Handle API-specific concerns (status codes, headers)

**Example:**

```python
# backend/app/api/upload.py
@router.post("/categorize")
async def categorize_transactions(
    file: UploadFile,
    upload_service: UploadSvc,  # Injected via Depends()
) -> CategorizeResponse:
    result = await upload_service.process_categorization(file, months, mode)
    return result  # Service returns Pydantic response model
```

### 2. Application Layer (`backend/app/services/`)

Contains business logic and orchestration:

| Service                  | Purpose                         | Key Methods                           |
| ------------------------ | ------------------------------- | ------------------------------------- |
| `UploadService`          | Orchestrate CSV import workflow | `process_categorization()`            |
| `TransactionCategorizer` | AI-powered categorization       | `categorize()`                        |
| `ScoreCalculator`        | Money Map score calculation     | `calculate_and_update_month()`        |
| `AdviceGenerator`        | Personalized budget advice      | `generate_advice()`                   |
| `MonthService`           | Month data queries              | `get_month_detail()`, `get_history()` |

**Service Pattern:**

```python
class UploadService:
    def __init__(self, month_repo: MonthRepository, tx_repo: TransactionRepository):
        self.month_repo = month_repo
        self.tx_repo = tx_repo

    async def process_categorization(self, file, months, mode) -> CategorizeResponse:
        # 1. Parse CSV
        # 2. Group by month
        # 3. Categorize with AI
        # 4. Persist to database
        # 5. Calculate scores
        # 6. Return summary
```

### 3. Domain Layer (`backend/app/db/models/`, `backend/app/db/enums.py`)

Core business entities with relationships:

```python
# backend/app/db/models/month.py
class Month(Base):
    id: Mapped[int]
    year: Mapped[int]
    month: Mapped[int]
    total_income: Mapped[Decimal]
    total_core: Mapped[Decimal]
    total_choice: Mapped[Decimal]
    total_compound: Mapped[Decimal]
    core_percentage: Mapped[Decimal]
    choice_percentage: Mapped[Decimal]
    compound_percentage: Mapped[Decimal]
    score: Mapped[int]  # 0-3

    # Relationships
    transactions: Mapped[list["Transaction"]]
    advice_records: Mapped[list["Advice"]]
```

**Money Map Enums:**

```python
class MoneyMapType(str, Enum):
    INCOME = "INCOME"        # Revenue
    CORE = "CORE"            # Necessities (target ≤50%)
    CHOICE = "CHOICE"        # Wants (target ≤30%)
    COMPOUND = "COMPOUND"    # Savings (target ≥20%)
    EXCLUDED = "EXCLUDED"    # Internal transfers
```

### 4. Infrastructure Layer (`backend/app/repositories/`, `backend/app/db/database.py`)

Implements data access and external integrations:

```python
# backend/app/repositories/month.py
class MonthRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_by_year_month(self, year: int, month: int) -> Month | None:
        result = await self.db.execute(
            select(Month).where(Month.year == year, Month.month == month)
        )
        return result.scalar_one_or_none()
```

---

## API Endpoints Reference

All endpoints are mounted at `/api/` prefix.

### Upload & Categorization

#### `POST /api/upload`

Preview CSV file contents before import.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (CSV file from Bankin')

**Response:**

```json
{
  "success": true,
  "total_transactions": 342,
  "months_detected": 3,
  "preview_by_month": {
    "2025-01": {
      "year": 2025,
      "month": 1,
      "transaction_count": 120,
      "total_income": 3500.00,
      "total_expenses": 2800.50,
      "preview_transactions": [...]
    }
  }
}
```

**Location:** `backend/app/api/upload.py:25`

---

#### `POST /api/categorize`

Process CSV and categorize transactions with Claude AI.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (CSV file)
- Query Parameters:
  - `months_to_process` (optional): Comma-separated list (e.g., `"2025-01,2025-02"`) or `"all"`
  - `import_mode` (optional): `"replace"` (default) or `"merge"`

**Response:**

```json
{
  "success": true,
  "months_processed": [
    {
      "year": 2025,
      "month": 1,
      "transactions_categorized": 118,
      "transactions_skipped": 2,
      "low_confidence_count": 5,
      "score": 2,
      "score_label": "Okay"
    }
  ],
  "months_not_found": [],
  "total_api_calls": 3
}
```

**Location:** `backend/app/api/upload.py:61`

**Import Modes:**

- **replace**: Delete existing month data and import fresh (default)
- **merge**: Keep existing transactions, add only new ones

---

### Month Data

#### `GET /api/months`

List all imported months with summaries.

**Response:**

```json
[
  {
    "id": 15,
    "year": 2025,
    "month": 1,
    "total_income": 3500.00,
    "total_core": 1650.00,
    "total_choice": 980.00,
    "total_compound": 870.00,
    "core_percentage": 47.14,
    "choice_percentage": 28.00,
    "compound_percentage": 24.86,
    "score": 3,
    "score_label": "Great",
    "transaction_count": 120,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

**Location:** `backend/app/api/months.py:52`

---

#### `GET /api/months/history`

Historical trend data for charts.

**Query Parameters:**

- `months` (optional): Number of months to retrieve (0-24, default 12)

**Response:**

```json
{
  "months": [
    {
      "year": 2024,
      "month": 2,
      "total_income": 3500.00,
      "total_core": 1750.00,
      "total_choice": 1050.00,
      "total_compound": 700.00,
      "core_percentage": 50.00,
      "choice_percentage": 30.00,
      "compound_percentage": 20.00,
      "score": 3,
      "score_label": "Great",
      "month_label": "février 2024"
    }
  ],
  "summary": {
    "average_score": 2.5,
    "trend": "improving"
  }
}
```

**Location:** `backend/app/api/months.py:83`

---

#### `GET /api/months/cashflow`

Aggregated cash flow data for Sankey diagram.

**Query Parameters:**

- `months` (optional): Number of months to aggregate (default 12)

**Response:**

```json
{
  "income_total": 42000.00,
  "core_total": 20500.00,
  "choice_total": 12000.00,
  "compound_total": 9500.00,
  "deficit": 0.00,
  "core_breakdown": [
    {"subcategory": "Housing", "amount": 12000.00},
    {"subcategory": "Groceries", "amount": 4800.00},
    {"subcategory": "Utilities", "amount": 2400.00}
  ],
  "choice_breakdown": [...],
  "compound_breakdown": [...]
}
```

**Location:** `backend/app/api/months.py:144`

---

#### `GET /api/months/{year}/{month}`

Detailed month data with filtered transactions.

**Path Parameters:**

- `year`: 4-digit year (e.g., 2025)
- `month`: 1-2 digit month (e.g., 1 or 01)

**Query Parameters:**

- `page` (optional): Page number (default 1)
- `page_size` (optional): Items per page (default 25)
- `category` (optional): Filter by MoneyMapType
- `search` (optional): Search in description
- `start_date` (optional): Filter by date range (ISO format)
- `end_date` (optional): Filter by date range (ISO format)

**Response:**

```json
{
  "month": {
    "id": 15,
    "year": 2025,
    "month": 1,
    "total_income": 3500.00,
    "score": 3,
    "score_label": "Great",
    ...
  },
  "transactions": [...],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 120,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

**Location:** `backend/app/api/months.py:182`

---

#### `GET /api/months/{year}/{month}/export/{format}`

Export month data as JSON or CSV.

**Path Parameters:**

- `year`: 4-digit year
- `month`: 1-2 digit month
- `format`: `json` or `csv`

**Response:**

- JSON: Returns structured data
- CSV: Returns CSV file with headers

**Locations:**

- JSON: `backend/app/api/months.py:300`
- CSV: `backend/app/api/months.py:353`

---

### Transactions

#### `PATCH /api/transactions/{transaction_id}`

Update transaction category (manual correction).

**Path Parameters:**

- `transaction_id`: Transaction ID

**Request Body:**

```json
{
  "money_map_type": "CORE",
  "money_map_subcategory": "Groceries"
}
```

**Response:**

```json
{
  "id": 1234,
  "date": "2025-01-15",
  "description": "Carrefour Market",
  "amount": -45.50,
  "money_map_type": "CORE",
  "money_map_subcategory": "Groceries",
  "is_manually_corrected": true
}
```

**Side Effects:**

- Sets `is_manually_corrected = true`
- Triggers month score recalculation

**Location:** `backend/app/api/transactions.py:22`

---

### Advice

#### `POST /api/advice/generate`

Generate or retrieve cached AI advice.

**Request Body:**

```json
{
  "year": 2025,
  "month": 1,
  "regenerate": false
}
```

**Response (cached):**

```json
{
  "success": true,
  "exists": true,
  "advice": {
    "analysis": "Your spending this month shows...",
    "problem_areas": [
      {
        "category": "CHOICE",
        "amount": 1200.00,
        "trend": "increasing"
      }
    ],
    "recommendations": [
      "Review your Eating Out expenses (€450)...",
      "Consider canceling unused subscriptions..."
    ],
    "encouragement": "You're making great progress!"
  },
  "generated_at": "2025-01-15T10:30:00"
}
```

**Location:** `backend/app/api/advice.py:50`

**Parameters:**

- `regenerate: false`: Returns cached advice if exists
- `regenerate: true`: Forces new AI generation

---

#### `GET /api/advice/{year}/{month}`

Retrieve stored advice for a month.

**Response:**

```json
{
  "success": true,
  "exists": true,
  "advice": {...},
  "generated_at": "2025-01-15T10:30:00"
}
```

**Location:** `backend/app/api/advice.py:170`

---

## Database Schema

### Entity-Relationship Diagram

```text
┌──────────────────────────────┐
│         Month                │
├──────────────────────────────┤
│ id (PK)                      │
│ year                         │
│ month                        │
│ total_income                 │
│ total_core                   │
│ total_choice                 │
│ total_compound               │
│ core_percentage              │
│ choice_percentage            │
│ compound_percentage          │
│ score (0-3)                  │
│ created_at                   │
│ updated_at                   │
└──────────────────────────────┘
         │ 1
         │
         │ Many
         ▼
┌──────────────────────────────┐
│      Transaction             │
├──────────────────────────────┤
│ id (PK)                      │
│ month_id (FK) → Month.id     │
│ date                         │
│ description                  │
│ account                      │
│ amount                       │
│ bankin_category              │
│ bankin_subcategory           │
│ money_map_type               │
│ money_map_subcategory        │
│ is_manually_corrected        │
└──────────────────────────────┘

         ┌──────────────────────────────┐
         │         Advice               │
         ├──────────────────────────────┤
         │ id (PK)                      │
         │ month_id (FK) → Month.id     │
         │ advice_text (JSON)           │
         │ generated_at                 │
         └──────────────────────────────┘
```

### Constraints & Indexes

**Month:**

- `UNIQUE(year, month)` - One record per calendar month
- `CHECK(score >= 0 AND score <= 3)` - Valid score range

**Transaction:**

- `CHECK(money_map_type IN (...))` - Valid enum values
- Index on `month_id` (foreign key)
- Index on `date` (for date range queries)

---

## Service Layer

### Upload Service

**File:** `backend/app/services/upload/service.py`

**Workflow:**

```python
async def process_categorization(
    file: UploadFile,
    months_to_process: list[str],
    import_mode: str
) -> CategorizeResponse:
    # 1. Parse CSV (French locale: DD/MM/YYYY, comma decimals)
    transactions = await BankinCSVParser.parse(file)

    # 2. Group by month
    months = group_by_month(transactions)

    # 3. For each month:
    for month_data in months:
        # Handle import mode
        if import_mode == "replace":
            await month_repo.delete(month_id)
        elif import_mode == "merge":
            existing_keys = await tx_repo.get_keys_for_month(month_id)
            month_data.transactions = filter_duplicates(month_data.transactions, existing_keys)

        # 4. Categorize transactions (AI + rules)
        categorized = await categorizer.categorize(month_data.transactions)

        # 5. Persist transactions (batch insert)
        await tx_repo.add_bulk(categorized)
        await tx_repo.flush()

        # 6. Calculate and update score
        await calculate_and_update_month(month_id)
        await month_repo.commit()

    # 7. Return summary
    return CategorizeResponse(...)
```

**Key Implementation Details:**

- **Duplicate Detection:** Transaction key = `date_description_amount_account`
- **Low-Confidence Tracking:** Tracks categorizations with confidence < 0.8
- **Batch Processing:** Categorizes up to 50 transactions per Claude API call
- **Transactional Consistency:** Uses `flush()` before score calculation, final `commit()` after

---

### Transaction Categorization Service

**File:** `backend/app/services/categorization/service.py`

**Three-Tier Pipeline:**

```python
async def categorize(transactions: list[Transaction]) -> list[Transaction]:
    # Tier 1: Cache lookup
    cache_hits, cache_misses = cache.lookup(transactions)

    # Tier 2: Deterministic rules
    rule_hits, rule_misses = apply_rules(cache_misses)

    # Tier 3: Claude API (batched)
    ai_results = await batch_categorize_with_claude(rule_misses)

    # Combine results
    return cache_hits + rule_hits + ai_results
```

**Deterministic Rules:**

1. **Internal Transfer Detection:**
   - Keywords: `"Virement"`, `"Transfer"`, `"Transfert"`
   - Category: `EXCLUDED`
   - Confidence: 1.0

2. **Bankin' Category Mapping:**
   - Hardcoded mapping: Bankin' category → Money Map type
   - Example: `"Groceries" → CORE`
   - Confidence: 1.0

**Claude API Configuration:**

- Model: `claude-sonnet-4-20250514`
- Batch size: 50 transactions
- Max tokens: 8192
- Max retries: 3
- System prompt: French with Money Map definitions

**Response Format:**

```json
[
  {
    "id": 1,
    "money_map_type": "CORE",
    "money_map_subcategory": "Groceries",
    "confidence": 0.95
  }
]
```

---

### Score Calculation Service

**File:** `backend/app/services/calculation/service.py`

**Algorithm:**

```python
async def calculate_and_update_month(month_id: int) -> Month:
    # 1. Aggregate transactions by category (single SQL query)
    totals = await tx_repo.aggregate_totals(month_id)

    # 2. Calculate percentages
    income = totals["income"]
    core_pct = (totals["core"] / income * 100) if income > 0 else 0
    choice_pct = (totals["choice"] / income * 100) if income > 0 else 0
    compound = income - totals["core"] - totals["choice"]
    compound_pct = (compound / income * 100) if income > 0 else 0

    # 3. Calculate score (0-3 points)
    score = 0
    if core_pct <= 50:
        score += 1
    if choice_pct <= 30:
        score += 1
    if compound_pct >= 20:
        score += 1

    # 4. Update month record
    month.total_income = income
    month.total_core = totals["core"]
    month.total_choice = totals["choice"]
    month.total_compound = compound
    month.core_percentage = core_pct
    month.choice_percentage = choice_pct
    month.compound_percentage = compound_pct
    month.score = score

    await month_repo.update(month)
    await month_repo.refresh(month)

    return month
```

**Money Map Thresholds:**

| Category | Target          | Scoring Rule    |
| -------- | --------------- | --------------- |
| CORE     | ≤ 50% of income | +1 point if met |
| CHOICE   | ≤ 30% of income | +1 point if met |
| COMPOUND | ≥ 20% of income | +1 point if met |

**Score Labels:**

- `0` → "Poor"
- `1` → "Need Improvement"
- `2` → "Okay"
- `3` → "Great"

---

### Advice Generation Service

**File:** `backend/app/services/advice/generator.py`

**Workflow:**

```python
async def generate_advice(
    year: int,
    month: int,
    regenerate: bool = False
) -> AdviceData:
    # 1. Check cache
    if not regenerate:
        cached = await advice_repo.get_by_month_id(month_id)
        if cached:
            return cached.advice_text

    # 2. Fetch historical data (last 3 months)
    months = await month_repo.get_recent_with_transactions(limit=3)

    if len(months) < 2:
        raise InsufficientDataError("Need at least 2 months of data")

    # 3. Extract all transactions per category
    all_transactions_by_category = extract_transactions(months)

    # 4. Build prompt
    prompt = build_advice_prompt(
        months=months,
        transactions_by_category=all_transactions_by_category,
        previous_advice=cached.advice_text if cached else None
    )

    # 5. Call Claude
    response = await claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": prompt}]
    )

    # 6. Parse response
    advice_data = parse_advice_response(response.content)

    # 7. Cache result
    await advice_repo.upsert(month_id, advice_data)

    return advice_data
```

**Prompt Structure:**

- **Context:** Last 3 months of totals, percentages, scores
- **Transactions:** ALL transactions sorted by amount (descending)
- **Previous Advice:** If regenerating, includes previous recommendations
- **Instructions:** Ultra-personalized, specific amounts, recurring patterns

**Response Schema:**

```json
{
  "analysis": "2-3 sentence summary",
  "problem_areas": [
    {
      "category": "CHOICE",
      "amount": 1200.00,
      "trend": "increasing"
    }
  ],
  "recommendations": [
    "Specific actionable step 1",
    "Specific actionable step 2"
  ],
  "encouragement": "Personalized motivation"
}
```

---

## Repository Pattern

All database operations go through repositories to:

- Decouple business logic from database implementation
- Enable easy testing with mocks
- Provide consistent query interface

### MonthRepository

**File:** `backend/app/repositories/month.py`

**Key Methods:**

```python
class MonthRepository:
    async def get_by_id(id: int) -> Month | None
    async def get_by_year_month(year: int, month: int) -> Month | None
    async def get_by_year_month_with_transactions(year: int, month: int) -> Month | None
    async def get_all_with_transaction_counts() -> list[Month]
    async def get_recent(limit: int) -> list[Month]
    async def get_recent_with_transactions(limit: int) -> list[Month]
    async def create(month: Month) -> Month
    async def update(month: Month) -> Month
    async def delete(month_id: int) -> None
    async def commit() -> None
    async def rollback() -> None
    async def flush() -> None
    async def refresh(month: Month) -> None
```

**Query Optimization:**

- `get_by_year_month_with_transactions()`: Uses `selectinload()` to eager-load transactions (avoids N+1)
- `get_all_with_transaction_counts()`: Uses LEFT JOIN to count transactions in single query

---

### TransactionRepository

**File:** `backend/app/repositories/transaction.py`

**Key Methods:**

```python
class TransactionRepository:
    async def get_filtered(
        month_id: int,
        page: int,
        page_size: int,
        category: str | None,
        search: str | None,
        start_date: date | None,
        end_date: date | None
    ) -> tuple[list[Transaction], int]

    async def get_all_for_month(month_id: int) -> list[Transaction]
    async def aggregate_totals(month_id: int) -> dict[str, Decimal]
    async def aggregate_by_subcategory(month_ids: list[int]) -> dict[str, list[dict]]
    async def add_bulk(transactions: list[Transaction]) -> None
    async def delete_for_month(month_id: int) -> None
    async def get_keys_for_month(month_id: int) -> set[str]
```

**Query Example:**

```python
# aggregate_totals() - Single SQL query with conditional aggregation
SELECT
    COALESCE(SUM(CASE WHEN money_map_type = 'INCOME' THEN amount ELSE 0 END), 0) as income,
    COALESCE(SUM(CASE WHEN money_map_type = 'CORE' AND amount < 0 THEN ABS(amount) ELSE 0 END), 0) as core,
    COALESCE(SUM(CASE WHEN money_map_type = 'CHOICE' AND amount < 0 THEN ABS(amount) ELSE 0 END), 0) as choice
FROM transactions
WHERE month_id = ?
```

---

## Transaction Processing Flow

End-to-end flow when user uploads a CSV file:

```text
User uploads CSV via /api/categorize
    ↓
POST /api/categorize (router)
    ↓
UploadService.process_categorization()
    ├─ Step 1: BankinCSVParser.parse()
    │  └─ Parse French locale CSV (DD/MM/YYYY, comma decimals)
    │
    ├─ Step 2: Group transactions by month
    │  └─ Creates MonthData objects with transaction summaries
    │
    ├─ Step 3: For each month:
    │  ├─ Handle import mode
    │  │  ├─ "replace": Delete existing month data
    │  │  └─ "merge": Filter out duplicates via transaction keys
    │  │
    │  ├─ TransactionCategorizer.categorize()
    │  │  ├─ Check in-memory cache
    │  │  ├─ Apply deterministic rules
    │  │  └─ Call Claude API (batched, 50 per call)
    │  │
    │  ├─ TransactionRepository.add_bulk()
    │  │  └─ Batch insert transactions
    │  │
    │  ├─ Session.flush()
    │  │  └─ Persist to DB (get transaction IDs)
    │  │
    │  ├─ calculate_and_update_month()
    │  │  ├─ aggregate_totals() (single SQL query)
    │  │  ├─ calculate_month_stats() (business logic)
    │  │  └─ Update Month record
    │  │
    │  └─ Session.commit()
    │     └─ Finalize database transaction
    │
    └─ Step 4: Return CategorizeResponse
       ├─ months_processed: list[MonthResult]
       ├─ months_not_found: list[str]
       └─ total_api_calls: int

Database State: Month + Transactions + Scores persisted
```

---

## AI Integration

### Claude API Configuration

**Model:** `claude-sonnet-4-20250514`

**Why Sonnet 4:**

- Best cost/quality ratio for this use case
- Fast inference (< 2s per batch)
- Excellent JSON adherence
- Strong multilingual support (French)

**Batch Processing:**

```python
# Categorize up to 50 transactions per API call
BATCH_SIZE = 50

batches = chunk_list(transactions, BATCH_SIZE)
results = []

for batch in batches:
    response = await claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": build_categorization_prompt(batch)
        }]
    )
    results.extend(parse_response(response))
```

**Cost Estimation:**

- Input: ~500 tokens per 50 transactions
- Output: ~300 tokens per 50 transactions
- Total: ~800 tokens per batch
- For 200 transactions: 4 API calls × $0.003 = $0.012

---

### Prompt Engineering

**Categorization Prompt Structure:**

```text
You are a financial categorization expert using the Money Map framework.

Categories:
- CORE: Necessities (housing, groceries, utilities, transport)
- CHOICE: Wants (entertainment, dining out, subscriptions)
- COMPOUND: Savings and investments
- EXCLUDED: Internal transfers
- INCOME: Revenue sources

Rules:
1. Categorize based on description and amount
2. Mark internal transfers as EXCLUDED
3. Provide confidence score (0-1)
4. Use French subcategory names

Transactions:
[
  {"id": 1, "date": "15/01/2025", "description": "Carrefour Market", "amount": -45.50},
  ...
]

Return JSON array:
[
  {"id": 1, "money_map_type": "CORE", "money_map_subcategory": "Groceries", "confidence": 0.95}
]
```

**Advice Prompt Structure:**

```text
You are a personal finance advisor specializing in the Money Map (50/30/20) framework.

Historical Data:
Month: January 2025
- Income: €3,500
- CORE: €1,650 (47%) ✓ Target ≤50%
- CHOICE: €980 (28%) ✓ Target ≤30%
- COMPOUND: €870 (25%) ✓ Target ≥20%
- Score: 3/3 (Great)

Transactions by Category:
CHOICE:
- Eating Out: €450 (McDonald's €15, Restaurant Le Bistro €85, ...)
- Subscriptions: €120 (Netflix €12, Spotify €10, ...)

Previous Advice:
[If regenerating, include previous recommendations to track follow-through]

Instructions:
1. Provide ultra-personalized analysis with specific transaction amounts
2. Identify recurring expenses and subscriptions
3. Compare with previous advice
4. Give 3-5 concrete, actionable recommendations
5. End with encouraging message

Return JSON:
{
  "analysis": "...",
  "problem_areas": [...],
  "recommendations": [...],
  "encouragement": "..."
}
```

---

## Error Handling

### Exception Hierarchy

```python
# Base exception
class BaseError(Exception):
    """Base for all custom exceptions."""

# CSV parsing errors
class CSVParseError(BaseError):
    pass

class InvalidFormatError(CSVParseError):
    pass

class MissingColumnsError(CSVParseError):
    pass

# Categorization errors
class CategorizationError(BaseError):
    pass

class APIConnectionError(CategorizationError):
    pass

class InvalidResponseError(CategorizationError):
    pass

# Calculation errors
class ScoreCalculationError(BaseError):
    pass

class MonthNotFoundError(ScoreCalculationError):
    pass

# Advice errors
class AdviceGenerationError(BaseError):
    pass

class InsufficientDataError(AdviceGenerationError):
    pass

class AdviceAPIError(AdviceGenerationError):
    pass

# Transaction errors
class TransactionError(BaseError):
    pass

class TransactionNotFoundError(TransactionError):
    pass
```

### Error Handling Pattern

```python
# In API layer
@router.post("/categorize")
async def categorize_transactions(...):
    try:
        result = await upload_service.process_categorization(...)
        return result
    except CSVParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIConnectionError as e:
        raise HTTPException(status_code=502, detail="Claude API unreachable")
    except Exception as e:
        logger.exception("Unexpected error in categorize endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### HTTP Status Code Mapping

| Exception Type               | HTTP Status | Description                           |
| ---------------------------- | ----------- | ------------------------------------- |
| `CSVParseError`              | 400         | Invalid CSV format or data            |
| `ValidationError` (Pydantic) | 422         | Invalid request body                  |
| `MonthNotFoundError`         | 404         | Requested month doesn't exist         |
| `InsufficientDataError`      | 400         | Not enough data for operation         |
| `APIConnectionError`         | 502         | Claude API unreachable                |
| `InvalidResponseError`       | 502         | Claude API returned invalid data      |
| `AdviceAPIError`             | 503         | Advice generation service unavailable |
| Generic exceptions           | 500         | Unexpected internal error             |

---

## Testing Strategy

### Test Structure

```text
backend/tests/
├── unit/              # Pure logic tests, no database
│   ├── test_parser.py
│   ├── test_rules.py
│   └── test_calculator.py
└── integration/       # Tests with database/external services
    ├── test_upload.py
    ├── test_months.py
    └── test_advice.py
```

### Testing Principles

1. **AAA Pattern:** Arrange-Act-Assert
2. **Independent:** No test depends on another
3. **Deterministic:** Same result every run
4. **Fast:** Unit tests < 100ms each

### Example Tests

**Unit Test (Parser):**

```python
def test_parse_french_decimal():
    """Test parsing French decimal format (comma separator)."""
    # Arrange
    csv_content = "Date;Description;Amount\n01/01/2025;Test;1.234,56"

    # Act
    result = BankinCSVParser.parse(csv_content)

    # Assert
    assert result[0].amount == Decimal("1234.56")
```

**Integration Test (Upload):**

```python
@pytest.mark.asyncio
async def test_upload_and_categorize(db_session):
    """Test full upload workflow with database."""
    # Arrange
    csv_file = create_test_csv()
    upload_service = UploadService(db_session)

    # Act
    result = await upload_service.process_categorization(
        csv_file,
        months_to_process=["2025-01"],
        import_mode="replace"
    )

    # Assert
    assert result.success is True
    assert len(result.months_processed) == 1
    assert result.months_processed[0].score >= 0

    # Verify database state
    month = await month_repo.get_by_year_month(2025, 1)
    assert month is not None
    assert month.transaction_count > 0
```

---

## Next Steps

- **[Frontend Architecture](./frontend-architecture.md)**: Understand the Next.js frontend
- **[API Reference](./api-reference.md)**: Complete API endpoint documentation

---

**Questions?** Check the [Product Mission](../product/mission.md) or [Tech Stack](../product/tech-stack.md) for context.
