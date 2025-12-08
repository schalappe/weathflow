# Specification: Transaction Categorization Service

## Goal

Implement a Claude API integration that automatically categorizes bank transactions into Money Map categories (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED) with batch processing for cost efficiency and caching for recurring patterns.

## User Stories

- As a budget-conscious user, I want my transactions automatically categorized so that I save 25+ minutes of manual work each month.
- As a Money Map follower, I want accurate categorization aligned with the 50/30/20 framework so that my budget score reflects reality.

## Specific Requirements

**Claude API Integration:**

- Use `anthropic` SDK with `claude-sonnet-4-20250514` model
- French system prompt with Money Map category definitions and rules
- Return structured JSON with `money_map_type`, `money_map_subcategory`, `confidence`
- Max tokens: 4096 per API call

**Batch Processing:**

- Batch 50 transactions per API call to optimize costs
- Process batches sequentially (synchronous)
- Estimated cost: ~$0.50-1.00 per 1,350 transactions (10 months)

**Retry Logic with Tenacity:**

- Use `tenacity` library (add as dependency)
- 3 retries with exponential backoff: 1s, 2s, 4s
- Retry on `RateLimitError` and `APIConnectionError`
- Reraise after all retries exhausted

**Transaction Pattern Caching:**

- In-memory cache with JSON file persistence at `data/categorization_cache.json`
- Cache key: normalized description (lowercase, stripped, variable parts removed)
- Only cache results with confidence >= 0.95
- Track hit_count for analytics
- Remove stale entries (no hits in 180 days) on save

**Deterministic Pre-filtering:**

- Apply Bankin' to Money Map mapping for obvious categories before API call
- Detect internal transfers by keywords and mark as EXCLUDED
- Reduces API calls by ~20%

**Error Handling:**

- Base exception: `CategorizationError`
- `APIConnectionError`: Claude API unreachable after retries (stores retry_count)
- `InvalidResponseError`: Unparseable JSON response (stores raw_response)
- `BatchCategorizationError`: Partial failure (stores failed_ids, partial_results)
- Chain exceptions with `from e` to preserve tracebacks

**Input/Output Models:**

- `TransactionInput`: id, date, description, amount, bankin_category, bankin_subcategory
- `CategorizationResult`: id, money_map_type, money_map_subcategory, confidence
- `CachedCategorization`: money_map_type, money_map_subcategory, confidence, hit_count
- All models extend `FrozenModel` for immutability

## Existing Code to Leverage

**FrozenModel Base - `backend/app/services/schemas.py`**

- What it does: Provides immutable Pydantic model base with `frozen=True`
- How to reuse: Import and extend for `TransactionInput`, `CategorizationResult`, `CachedCategorization`
- Key exports: `FrozenModel`

**Exception Hierarchy - `backend/app/services/exceptions.py`**

- What it does: Establishes base exception with context-aware subclasses
- How to reuse: Add `CategorizationError` hierarchy following same pattern
- Key pattern: Store context attributes, call `super().__init__()` with formatted message

**MoneyMapType Enum - `backend/app/db/enums.py`**

- What it does: Defines valid category types (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED)
- How to reuse: Import directly for validation in `CategorizationResult`
- Key exports: `MoneyMapType`

**Service Class Pattern - `backend/app/services/csv_parser.py`**

- What it does: Demonstrates class-based service with public API and private helpers
- How to reuse: Follow same structure with single `categorize()` public method
- Key pattern: ClassVar for constants, NumPy docstrings, full type annotations

**ParsedTransaction - `backend/app/services/schemas.py`**

- What it does: Represents parsed CSV transaction with all fields
- How to reuse: Convert to `TransactionInput` for categorization
- Key fields: date, description, amount, bankin_category, bankin_subcategory

## Architecture Approach

**Component Design:**

- `TransactionCategorizer`: Main service class with single `categorize()` public method
- `CategorizationCache`: Manages in-memory cache with JSON persistence
- `CategoryMapping`: Static deterministic rules for pre-filtering
- `CATEGORIZATION_SYSTEM_PROMPT`: French prompt constant

**Data Flow:**

1. `_check_cache()` - Lookup cached results by normalized description
2. `_apply_deterministic_rules()` - Apply Bankin' to Money Map mapping
3. `_categorize_batch()` - Send remaining to Claude API in batches of 50
4. `_update_cache()` - Cache high-confidence results
5. Merge all results, sort by transaction ID, persist cache

**File Structure:**

```text
backend/app/services/
├── categorizer.py           # TransactionCategorizer class
├── categorization_cache.py  # CategorizationCache class
├── categorization_prompt.py # CATEGORIZATION_SYSTEM_PROMPT constant
└── category_mapping.py      # CategoryMapping class
```

**Integration Points:**

- Input: Convert `ParsedTransaction` from CSV parser to `TransactionInput`
- Output: `CategorizationResult` maps to `Transaction` model fields
- Dependencies: Add `anthropic>=0.40.0` and `tenacity>=9.0.0` to pyproject.toml

## Out of Scope

- Learning from user corrections (deferred to future iteration)
- Multi-language prompts (French only)
- Custom category definitions (fixed Money Map categories)
- Database persistence (caller's responsibility)
- Async/background processing (synchronous only)
- Progress callbacks or status updates
- Pre-filtering of internal transfers by amount patterns
- Cache invalidation on manual corrections (deferred)
- Rate limiting beyond tenacity retry (API handles this)
- Cost tracking or usage metrics
