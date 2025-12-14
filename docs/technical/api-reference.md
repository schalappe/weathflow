# API Reference

> **Last Updated:** December 2025
> **Base URL:** `http://localhost:8000`
> **API Prefix:** `/api/`

Complete reference for all Money Map Manager REST API endpoints.

---

## Table of Contents

- [Upload Endpoints](#upload-endpoints)
- [Month Endpoints](#month-endpoints)
- [Transaction Endpoints](#transaction-endpoints)
- [Advice Endpoints](#advice-endpoints)
- [Error Responses](#error-responses)

---

## Upload Endpoints

### Preview CSV Upload

Preview CSV file contents before categorizing.

```http
POST /api/upload
Content-Type: multipart/form-data
```

**Request:**

| Parameter | Type | Required | Description             |
| --------- | ---- | -------- | ----------------------- |
| `file`    | File | Yes      | Bankin' CSV export file |

**Response:** `200 OK`

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
      "preview_transactions": [
        {
          "date": "2025-01-15",
          "description": "Carrefour Market",
          "amount": -45.50
        }
      ]
    },
    "2025-02": { ... },
    "2025-03": { ... }
  }
}
```

**Errors:**

| Status | Description                           |
| ------ | ------------------------------------- |
| `400`  | Invalid CSV format or missing columns |
| `413`  | File too large (max 10MB)             |
| `422`  | Invalid file type (must be .csv)      |

**Example:**

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@transactions.csv"
```

---

### Categorize Transactions

Process CSV and categorize transactions with AI.

```http
POST /api/categorize
Content-Type: multipart/form-data
```

**Request:**

| Parameter           | Type   | Required | Description                                                 |
| ------------------- | ------ | -------- | ----------------------------------------------------------- |
| `file`              | File   | Yes      | Bankin' CSV export file                                     |
| `months_to_process` | String | No       | Comma-separated list (e.g., `"2025-01,2025-02"`) or `"all"` |
| `import_mode`       | String | No       | `"replace"` (default) or `"merge"`                          |

**Import Modes:**

- **replace**: Delete existing month data and import fresh (default)
- **merge**: Keep existing transactions, add only new ones (duplicate detection)

**Response:** `200 OK`

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

**Fields:**

- `transactions_categorized`: Successfully categorized transactions
- `transactions_skipped`: Duplicates (merge mode only)
- `low_confidence_count`: Transactions with confidence < 0.8
- `score`: Money Map score (0-3)
- `score_label`: "Poor" | "Need Improvement" | "Okay" | "Great"
- `total_api_calls`: Number of Claude API calls made

**Errors:**

| Status | Description                                    |
| ------ | ---------------------------------------------- |
| `400`  | Invalid CSV format or month format             |
| `502`  | Claude API unreachable or invalid response     |
| `503`  | Categorization service temporarily unavailable |

**Example:**

```bash
curl -X POST "http://localhost:8000/api/categorize?months_to_process=2025-01,2025-02&import_mode=replace" \
  -F "file=@transactions.csv"
```

---

## Month Endpoints

### List All Months

Get all imported months with summaries.

```http
GET /api/months
```

**Response:** `200 OK`

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
  },
  ...
]
```

**Sorting:** Most recent first (descending by year, month)

**Example:**

```bash
curl http://localhost:8000/api/months
```

---

### Get Historical Trends

Get historical data for trend charts.

```http
GET /api/months/history?months={count}
```

**Query Parameters:**

| Parameter | Type    | Required | Default | Description                         |
| --------- | ------- | -------- | ------- | ----------------------------------- |
| `months`  | Integer | No       | 12      | Number of months to retrieve (0-24) |

**Response:** `200 OK`

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
    },
    ...
  ],
  "summary": {
    "average_score": 2.5,
    "trend": "improving"
  }
}
```

**Trend Values:**

- `"improving"`: Average score trending upward
- `"declining"`: Average score trending downward
- `"stable"`: No significant change

**Errors:**

| Status | Description                             |
| ------ | --------------------------------------- |
| `400`  | Invalid months parameter (must be 0-24) |

**Example:**

```bash
curl "http://localhost:8000/api/months/history?months=12"
```

---

### Get Cash Flow Data

Get aggregated cash flow data for Sankey diagram.

```http
GET /api/months/cashflow?months={count}
```

**Query Parameters:**

| Parameter | Type    | Required | Default | Description                          |
| --------- | ------- | -------- | ------- | ------------------------------------ |
| `months`  | Integer | No       | 12      | Number of months to aggregate (1-24) |

**Response:** `200 OK`

```json
{
  "income_total": 42000.00,
  "core_total": 20500.00,
  "choice_total": 12000.00,
  "compound_total": 9500.00,
  "deficit": 0.00,
  "core_breakdown": [
    { "subcategory": "Housing", "amount": 12000.00 },
    { "subcategory": "Groceries", "amount": 4800.00 },
    { "subcategory": "Utilities", "amount": 2400.00 },
    { "subcategory": "Transport", "amount": 1300.00 }
  ],
  "choice_breakdown": [
    { "subcategory": "Eating Out", "amount": 5400.00 },
    { "subcategory": "Entertainment", "amount": 3600.00 },
    { "subcategory": "Shopping", "amount": 3000.00 }
  ],
  "compound_breakdown": [
    { "subcategory": "Savings", "amount": 6000.00 },
    { "subcategory": "Investments", "amount": 3500.00 }
  ]
}
```

**Fields:**

- `deficit`: Amount spent beyond income (if any)
- `*_breakdown`: Subcategory breakdowns sorted by amount descending

**Example:**

```bash
curl "http://localhost:8000/api/months/cashflow?months=12"
```

---

### Get Month Detail

Get detailed month data with filtered transactions.

```http
GET /api/months/{year}/{month}?page={page}&page_size={size}&category={type}&search={query}&start_date={date}&end_date={date}
```

**Path Parameters:**

| Parameter | Type    | Description               |
| --------- | ------- | ------------------------- |
| `year`    | Integer | 4-digit year (e.g., 2025) |
| `month`   | Integer | 1-2 digit month (1-12)    |

**Query Parameters:**

| Parameter    | Type    | Required | Default | Description                                                       |
| ------------ | ------- | -------- | ------- | ----------------------------------------------------------------- |
| `page`       | Integer | No       | 1       | Page number                                                       |
| `page_size`  | Integer | No       | 25      | Items per page (1-100)                                            |
| `category`   | String  | No       | -       | Filter by MoneyMapType (CORE, CHOICE, COMPOUND, INCOME, EXCLUDED) |
| `search`     | String  | No       | -       | Search in description (case-insensitive)                          |
| `start_date` | String  | No       | -       | Filter by date range (ISO format: YYYY-MM-DD)                     |
| `end_date`   | String  | No       | -       | Filter by date range (ISO format: YYYY-MM-DD)                     |

**Response:** `200 OK`

```json
{
  "month": {
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
  },
  "transactions": [
    {
      "id": 1234,
      "date": "2025-01-15",
      "description": "Carrefour Market",
      "account": "Compte Courant",
      "amount": -45.50,
      "bankin_category": "Food",
      "bankin_subcategory": "Groceries",
      "money_map_type": "CORE",
      "money_map_subcategory": "Groceries",
      "is_manually_corrected": false
    },
    ...
  ],
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

**Errors:**

| Status | Description                       |
| ------ | --------------------------------- |
| `404`  | Month not found                   |
| `400`  | Invalid date format or parameters |

**Example:**

```bash
# Get first page with CORE transactions only
curl "http://localhost:8000/api/months/2025/1?category=CORE&page=1&page_size=25"

# Search for "Carrefour" transactions
curl "http://localhost:8000/api/months/2025/1?search=Carrefour"

# Filter by date range
curl "http://localhost:8000/api/months/2025/1?start_date=2025-01-01&end_date=2025-01-15"
```

---

### Export Month Data

Export month data as JSON or CSV.

```http
GET /api/months/{year}/{month}/export/{format}
```

**Path Parameters:**

| Parameter | Type    | Description     |
| --------- | ------- | --------------- |
| `year`    | Integer | 4-digit year    |
| `month`   | Integer | 1-2 digit month |
| `format`  | String  | `json` or `csv` |

**Response (JSON):** `200 OK`

```json
{
  "month": {
    "year": 2025,
    "month": 1,
    "total_income": 3500.00,
    "score": 3,
    ...
  },
  "transactions": [...]
}
```

**Response (CSV):** `200 OK`

```csv
Date,Description,Account,Amount,Category,Subcategory,Manually Corrected
2025-01-15,Carrefour Market,Compte Courant,-45.50,CORE,Groceries,No
2025-01-14,Netflix,Compte Courant,-12.99,CHOICE,Subscriptions,No
...
```

**Headers:**

- JSON: `Content-Type: application/json`
- CSV: `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="month-2025-01.csv"`

**Errors:**

| Status | Description                          |
| ------ | ------------------------------------ |
| `404`  | Month not found                      |
| `400`  | Invalid format (must be json or csv) |

**Example:**

```bash
# Export as JSON
curl "http://localhost:8000/api/months/2025/1/export/json" -o month-2025-01.json

# Export as CSV
curl "http://localhost:8000/api/months/2025/1/export/csv" -o month-2025-01.csv
```

---

## Transaction Endpoints

### Update Transaction

Update transaction category (manual correction).

```http
PATCH /api/transactions/{id}
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type    | Description    |
| --------- | ------- | -------------- |
| `id`      | Integer | Transaction ID |

**Request Body:**

```json
{
  "money_map_type": "CORE",
  "money_map_subcategory": "Groceries"
}
```

**Fields:**

| Field                   | Type   | Required | Description                                 |
| ----------------------- | ------ | -------- | ------------------------------------------- |
| `money_map_type`        | String | Yes      | INCOME, CORE, CHOICE, COMPOUND, or EXCLUDED |
| `money_map_subcategory` | String | Yes      | Subcategory name (e.g., "Groceries")        |

**Response:** `200 OK`

```json
{
  "id": 1234,
  "date": "2025-01-15",
  "description": "Carrefour Market",
  "account": "Compte Courant",
  "amount": -45.50,
  "bankin_category": "Food",
  "bankin_subcategory": "Groceries",
  "money_map_type": "CORE",
  "money_map_subcategory": "Groceries",
  "is_manually_corrected": true
}
```

**Side Effects:**

- Sets `is_manually_corrected = true`
- Triggers month score recalculation
- Updates month totals and percentages

**Errors:**

| Status | Description                          |
| ------ | ------------------------------------ |
| `404`  | Transaction not found                |
| `400`  | Invalid category type or subcategory |
| `422`  | Invalid request body                 |

**Example:**

```bash
curl -X PATCH http://localhost:8000/api/transactions/1234 \
  -H "Content-Type: application/json" \
  -d '{"money_map_type": "CORE", "money_map_subcategory": "Groceries"}'
```

---

## Advice Endpoints

### Generate Advice

Generate or retrieve cached AI advice.

```http
POST /api/advice/generate
Content-Type: application/json
```

**Request Body:**

```json
{
  "year": 2025,
  "month": 1,
  "regenerate": false
}
```

**Fields:**

| Field        | Type    | Required | Default | Description                         |
| ------------ | ------- | -------- | ------- | ----------------------------------- |
| `year`       | Integer | Yes      | -       | 4-digit year                        |
| `month`      | Integer | Yes      | -       | 1-2 digit month                     |
| `regenerate` | Boolean | No       | false   | Force new generation (ignore cache) |

**Response (Cached):** `200 OK`

```json
{
  "success": true,
  "exists": true,
  "advice": {
    "analysis": "Your spending this month shows strong adherence to the Money Map framework. You've kept your Core expenses at 47%, well within the 50% target.",
    "problem_areas": [
      {
        "category": "CHOICE",
        "amount": 1200.00,
        "trend": "increasing"
      }
    ],
    "recommendations": [
      "Review your Eating Out expenses (€450). Consider meal prepping twice a week to reduce restaurant visits.",
      "Cancel unused subscriptions (Netflix €12.99, Spotify €10.99) if not actively using them.",
      "Set up automatic transfer of €100/month to savings account on payday."
    ],
    "encouragement": "You're making great progress! Your savings rate of 25% is above the 20% target. Keep up the excellent work!"
  },
  "generated_at": "2025-01-15T10:30:00"
}
```

**Response (No Advice):** `200 OK`

```json
{
  "success": true,
  "exists": false,
  "advice": null,
  "generated_at": null
}
```

**Advice Data Schema:**

| Field             | Type   | Description                               |
| ----------------- | ------ | ----------------------------------------- |
| `analysis`        | String | 2-3 sentence summary of spending patterns |
| `problem_areas`   | Array  | Categories with issues (amount, trend)    |
| `recommendations` | Array  | 3-5 concrete, actionable steps            |
| `encouragement`   | String | Personalized motivational message         |

**Problem Area Schema:**

| Field      | Type   | Description                             |
| ---------- | ------ | --------------------------------------- |
| `category` | String | CORE, CHOICE, or COMPOUND               |
| `amount`   | Number | Total amount spent in category          |
| `trend`    | String | "increasing", "decreasing", or "stable" |

**Errors:**

| Status | Description                                |
| ------ | ------------------------------------------ |
| `400`  | Insufficient data (need at least 2 months) |
| `404`  | Month not found                            |
| `503`  | Claude API temporarily unavailable         |

**Example:**

```bash
# Get cached advice
curl -X POST http://localhost:8000/api/advice/generate \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "month": 1, "regenerate": false}'

# Force regeneration
curl -X POST http://localhost:8000/api/advice/generate \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "month": 1, "regenerate": true}'
```

---

### Get Advice

Retrieve stored advice for a month.

```http
GET /api/advice/{year}/{month}
```

**Path Parameters:**

| Parameter | Type    | Description     |
| --------- | ------- | --------------- |
| `year`    | Integer | 4-digit year    |
| `month`   | Integer | 1-2 digit month |

**Response:** `200 OK`

Same response schema as Generate Advice endpoint.

**Errors:**

| Status | Description     |
| ------ | --------------- |
| `404`  | Month not found |

**Example:**

```bash
curl http://localhost:8000/api/advice/2025/1
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code  | Meaning               | Common Causes                                          |
| ----- | --------------------- | ------------------------------------------------------ |
| `400` | Bad Request           | Invalid parameters, malformed CSV, invalid date format |
| `404` | Not Found             | Month or transaction doesn't exist                     |
| `413` | Payload Too Large     | File exceeds 10MB                                      |
| `422` | Unprocessable Entity  | Invalid request body (Pydantic validation error)       |
| `500` | Internal Server Error | Unexpected error (check server logs)                   |
| `502` | Bad Gateway           | Claude API unreachable or invalid response             |
| `503` | Service Unavailable   | Temporary service failure (retry recommended)          |

### Example Error Response

```json
{
  "detail": "Invalid month format. Expected YYYY-MM, got 2025-1"
}
```

---

## Pagination

Endpoints that support pagination use this standard format:

**Request:**

```http
GET /api/months/2025/1?page=2&page_size=50
```

**Response:**

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "page_size": 50,
    "total_items": 120,
    "total_pages": 3,
    "has_next": true,
    "has_previous": true
  }
}
```

**Pagination Fields:**

| Field          | Type    | Description                            |
| -------------- | ------- | -------------------------------------- |
| `page`         | Integer | Current page number (1-indexed)        |
| `page_size`    | Integer | Items per page                         |
| `total_items`  | Integer | Total number of items across all pages |
| `total_pages`  | Integer | Total number of pages                  |
| `has_next`     | Boolean | True if there's a next page            |
| `has_previous` | Boolean | True if there's a previous page        |

---

## CORS Configuration

**Current:** CORS enabled for `http://localhost:3000` (frontend development)

**Headers:**

```text
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Production:** Update CORS origins to match deployment domain.

---

## Testing Endpoints

Use the provided examples with `curl` or import into Postman/Insomnia.

### Quick Test Script

```bash
#!/bin/bash

API_URL="http://localhost:8000"

# 1. Upload and categorize
echo "1. Uploading CSV..."
curl -X POST "$API_URL/api/categorize?import_mode=replace" \
  -F "file=@test-transactions.csv"

# 2. Get months list
echo -e "\n2. Getting months list..."
curl "$API_URL/api/months"

# 3. Get month detail
echo -e "\n3. Getting month detail..."
curl "$API_URL/api/months/2025/1?page=1&page_size=10"

# 4. Generate advice
echo -e "\n4. Generating advice..."
curl -X POST "$API_URL/api/advice/generate" \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "month": 1, "regenerate": false}'

echo -e "\nDone!"
```

---

## Next Steps

- **[Backend Architecture](./backend-architecture.md)**: Understand the implementation
- **[Frontend Architecture](./frontend-architecture.md)**: Learn about the UI layer

---

**Questions?** Check the [Product Mission](../product/mission.md) for context.
