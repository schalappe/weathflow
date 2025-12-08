# Task Breakdown: Transaction Categorization Service

## Overview

| Metric               | Value            |
| -------------------- | ---------------- |
| Total Tasks          | 24               |
| Task Groups          | 5                |
| Estimated Complexity | Medium           |
| Primary Stack        | Python + FastAPI |

## Task List

### Dependencies & Schema Layer

#### Task Group 1: Project Dependencies and Pydantic Models

**Dependencies:** None

- [x] 1.0 Complete dependencies and schema layer
  - [x] 1.1 Add external dependencies to pyproject.toml
    - Add `anthropic>=0.40.0` for Claude API
    - Add `tenacity>=9.0.0` for retry logic
    - Run `uv sync` to install
  - [x] 1.2 Add categorization exception hierarchy to `exceptions.py`
    - `CategorizationError`: Base exception
    - `APIConnectionError`: Stores retry_count
    - `InvalidResponseError`: Stores raw_response
    - `BatchCategorizationError`: Stores failed_ids, partial_results
    - Follow pattern from `CSVParseError` hierarchy
  - [x] 1.3 Add categorization Pydantic models to `schemas.py`
    - `TransactionInput`: id, date, description, amount, bankin_category, bankin_subcategory
    - `CategorizationResult`: id, money_map_type, money_map_subcategory, confidence
    - `CachedCategorization`: money_map_type, money_map_subcategory, confidence, hit_count
    - Extend `FrozenModel` base class
    - Import `MoneyMapType` from `db/enums.py`
  - [x] 1.4 Write 4 focused tests for schema validation
    - Test `TransactionInput` validation with valid data
    - Test `CategorizationResult` confidence bounds (0.0-1.0)
    - Test `CachedCategorization` immutability (frozen)
    - Test exception message formatting
  - [x] 1.5 Ensure schema tests pass
    - Run ONLY the 4 tests from 1.4
    - Verify imports work correctly

**Acceptance Criteria:**

- Dependencies installed and importable
- All 4 exception classes defined with proper attributes
- All 3 Pydantic models validate correctly
- Tests from 1.4 pass

---

### Supporting Modules Layer

#### Task Group 2: System Prompt and Category Mapping

**Dependencies:** Task Group 1

- [x] 2.0 Complete supporting modules
  - [x] 2.1 Create `categorization_prompt.py` with system prompt constant
    - Define `CATEGORIZATION_SYSTEM_PROMPT` as module-level constant
    - Copy French prompt from `docs/product-development/features/03-transaction-categorization-service.md`
    - Include Money Map categories and categorization rules
  - [x] 2.2 Create `category_mapping.py` with `CategoryMapping` class
    - `BANKIN_TO_MONEYMAP`: ClassVar dict mapping (category, subcategory) → (type, subcategory)
    - `INTERNAL_TRANSFER_KEYWORDS`: ClassVar list of keywords
    - `get_deterministic_category()`: Returns mapping or None
    - `is_internal_transfer()`: Checks description for keywords
    - Follow NumPy docstring style
  - [x] 2.3 Write 4 focused tests for category mapping
    - Test `get_deterministic_category()` returns correct mapping for known pair
    - Test `get_deterministic_category()` returns None for unknown pair
    - Test `is_internal_transfer()` detects "virement interne"
    - Test `is_internal_transfer()` returns False for regular transactions
  - [x] 2.4 Ensure mapping tests pass
    - Run ONLY the 4 tests from 2.3
    - Verify prompt constant is non-empty string

**Acceptance Criteria:**

- System prompt matches spec exactly
- Mapping covers all Bankin' categories from spec
- Internal transfer detection works
- Tests from 2.3 pass

---

#### Task Group 3: Categorization Cache

**Dependencies:** Task Group 1

- [x] 3.0 Complete caching module
  - [x] 3.1 Create `categorization_cache.py` with `CategorizationCache` class
    - `DEFAULT_CACHE_PATH`: ClassVar Path to `data/categorization_cache.json`
    - `CONFIDENCE_THRESHOLD`: ClassVar float = 0.95
    - Constructor accepts optional cache_path
    - Internal `_cache` dict for in-memory storage
  - [x] 3.2 Implement cache key normalization
    - `_normalize_key()`: lowercase, strip whitespace, normalize spaces
    - Remove variable suffixes (dates like `12/05`, refs like `REF:ABC123`)
    - Use regex for pattern removal
  - [x] 3.3 Implement cache operations
    - `get()`: Return `CachedCategorization` or None, increment hit_count
    - `put()`: Cache only if confidence >= threshold
    - `save()`: Persist to JSON, remove stale entries (180 days)
    - `clear()`: Empty cache (for testing)
    - `_load_cache()`: Load from JSON file if exists
  - [x] 3.4 Write 6 focused tests for cache operations
    - Test `_normalize_key()` handles "NETFLIX.COM 12/05" → "netflix.com"
    - Test `get()` returns None for cache miss
    - Test `put()` stores high-confidence result
    - Test `put()` rejects low-confidence result (< 0.95)
    - Test `save()` and `_load_cache()` roundtrip
    - Test `clear()` empties cache
  - [x] 3.5 Ensure cache tests pass
    - Run ONLY the 6 tests from 3.4
    - Use temp directory for cache file in tests

**Acceptance Criteria:**

- Cache key normalization handles merchant name variations
- Only high-confidence results are cached
- JSON persistence works correctly
- Tests from 3.4 pass

---

### Core Service Layer

#### Task Group 4: Transaction Categorizer Service

**Dependencies:** Task Groups 1, 2, 3

- [ ] 4.0 Complete main categorizer service
  - [ ] 4.1 Create `categorizer.py` with `TransactionCategorizer` class skeleton
    - `MODEL`: ClassVar = "claude-sonnet-4-20250514"
    - `BATCH_SIZE`: ClassVar = 50
    - `MAX_TOKENS`: ClassVar = 4096
    - Constructor accepts `api_key` and optional `cache`
    - Initialize Anthropic client
    - NumPy docstrings with usage example
  - [ ] 4.2 Implement cache lookup helper
    - `_check_cache()`: Takes transactions, returns (cached_results, pending)
    - Lookup by normalized description
    - Create `CategorizationResult` from cache hit
  - [ ] 4.3 Implement deterministic rules helper
    - `_apply_deterministic_rules()`: Takes transactions, returns (rule_results, remaining)
    - Use `CategoryMapping.get_deterministic_category()`
    - Use `CategoryMapping.is_internal_transfer()`
    - Set confidence=1.0 for deterministic results
  - [ ] 4.4 Implement user prompt builder
    - `_build_user_prompt()`: Format transactions as JSON for Claude
    - Include transaction id, date, description, amount, bankin_category, bankin_subcategory
    - Request JSON array response format
  - [ ] 4.5 Implement Claude API call with tenacity retry
    - `_call_claude_api()`: Call Anthropic API with system and user prompts
    - Decorate with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))`
    - Retry on `RateLimitError` and `anthropic.APIConnectionError`
    - Return raw response text
  - [ ] 4.6 Implement response parser
    - `_parse_response()`: Parse JSON response into `CategorizationResult` list
    - Strip markdown code blocks if present
    - Default confidence to 1.0 if missing
    - Raise `InvalidResponseError` on parse failure
  - [ ] 4.7 Implement cache update helper
    - `_update_cache()`: Cache high-confidence results
    - Map transaction description to result
  - [ ] 4.8 Implement main `categorize()` method
    - Public entry point taking `list[TransactionInput]`
    - Pipeline: cache → deterministic rules → batch API → merge
    - Chunk remaining transactions by `BATCH_SIZE`
    - Collect partial results on batch failure
    - Raise `BatchCategorizationError` if any batch fails
    - Sort final results by transaction ID
    - Call `cache.save()` at end

**Acceptance Criteria:**

- Service follows class pattern from `BankinCSVParser`
- Pipeline processes cache → rules → API in order
- Batching works correctly for 50+ transactions
- Error handling preserves partial results

---

#### Task Group 5: Integration Testing

**Dependencies:** Task Group 4

- [ ] 5.0 Complete integration testing
  - [ ] 5.1 Write 2 unit tests for cache + rules pipeline (no API)
    - Test transactions fully resolved by cache return without API call
    - Test transactions resolved by deterministic rules return without API call
  - [ ] 5.2 Write 3 unit tests with mocked Claude API
    - Test successful batch categorization with mocked response
    - Test retry on simulated rate limit (verify 3 attempts)
    - Test `InvalidResponseError` on malformed JSON response
  - [ ] 5.3 Write 2 integration tests for full pipeline
    - Test mixed scenario: some cached, some rules, some API
    - Test `BatchCategorizationError` contains partial_results on failure
  - [ ] 5.4 Run all feature tests
    - Run tests from Task Groups 1-5
    - Expected total: ~25 tests
    - Verify all pass
  - [ ] 5.5 Run linting and type checking
    - Run `uv run ruff check backend/app/services/`
    - Run `uv run mypy backend/app/services/`
    - Fix any issues

**Acceptance Criteria:**

- All ~25 feature tests pass
- No ruff linting errors
- No mypy type errors
- Pipeline handles all scenarios correctly

---

## Execution Order

| Order | Task Group   | Reason                                                          |
| ----- | ------------ | --------------------------------------------------------------- |
| 1     | Task Group 1 | Foundation: dependencies and schemas needed by all other groups |
| 2     | Task Group 2 | Supporting: prompt and mapping used by categorizer              |
| 3     | Task Group 3 | Supporting: cache used by categorizer (can parallel with 2)     |
| 4     | Task Group 4 | Core: main service requires groups 1-3                          |
| 5     | Task Group 5 | Verification: integration tests require complete service        |

---

## Files to Create/Modify

| File                                                    | Action | Task Group |
| ------------------------------------------------------- | ------ | ---------- |
| `backend/pyproject.toml`                                | Modify | 1          |
| `backend/app/services/exceptions.py`                    | Modify | 1          |
| `backend/app/services/schemas.py`                       | Modify | 1          |
| `backend/app/services/categorization_prompt.py`         | Create | 2          |
| `backend/app/services/category_mapping.py`              | Create | 2          |
| `backend/app/services/categorization_cache.py`          | Create | 3          |
| `backend/app/services/categorizer.py`                   | Create | 4          |
| `backend/tests/units/services/test_categorization_*.py` | Create | 1-5        |

---

## Testing Summary

| Phase        | Tests   | Focus                                   |
| ------------ | ------- | --------------------------------------- |
| Task Group 1 | 4       | Schema validation, exception formatting |
| Task Group 2 | 4       | Category mapping, transfer detection    |
| Task Group 3 | 6       | Cache operations, persistence           |
| Task Group 4 | 0       | (Tested via integration)                |
| Task Group 5 | 7       | Pipeline integration, error handling    |
| **Total**    | **~21** | Focused, critical-path coverage         |
