# Implementation: Task Groups 1-3 (Foundation Layer)

**Date:** 2025-12-08
**Task Groups:** 1, 2, 3
**Implementer:** implement-task command

## Summary

Implemented the foundation layer for the Transaction Categorization Service, including:
- External dependencies (anthropic, tenacity)
- Custom exception hierarchy for categorization errors
- Pydantic schemas for categorization input/output
- French system prompt for Claude API
- Deterministic category mapping from Bankin' to Money Map
- In-memory cache with JSON persistence for recurring transactions

## Architecture Approach

Followed existing codebase patterns from `csv_parser.py` and `schemas.py`:
- Service classes with ClassVar constants and private helper methods
- Exception hierarchy with contextual attributes
- Frozen Pydantic models for immutable data
- NumPy-style docstrings throughout

## Files Modified

- `backend/pyproject.toml` - Added anthropic>=0.40.0 and tenacity>=9.0.0 dependencies
- `backend/app/services/exceptions.py` - Added 4 categorization exception classes
- `backend/app/services/schemas.py` - Added 3 Pydantic models (TransactionInput, CategorizationResult, CachedCategorization)

## Files Created

- `backend/app/services/categorization_prompt.py` - French system prompt constant for Claude API
- `backend/app/services/category_mapping.py` - CategoryMapping class with deterministic mappings and internal transfer detection
- `backend/app/services/categorization_cache.py` - CategorizationCache class with JSON persistence
- `backend/tests/units/services/test_category_mapping.py` - 10 tests for mapping and prompt
- `backend/tests/units/services/test_categorization_cache.py` - 10 tests for cache operations

## Key Implementation Details

### Exception Hierarchy
```bash
CategorizationError (base)
├── APIConnectionError (stores retry_count)
├── InvalidResponseError (stores raw_response, truncates in message)
└── BatchCategorizationError (stores failed_ids, partial_results)
```

### Category Mapping
- 40+ deterministic mappings from Bankin' categories to Money Map
- Extended beyond spec to include common French banking categories
- Internal transfer detection using "virement interne" variations only

### Cache Design
- Key normalization removes dates (DD/MM) and references (REF:XXX)
- Only caches results with confidence >= 0.95
- Stale entry cleanup (180 days) on save()
- Timezone-aware datetime comparison for stale detection

## Integration Points

- `TransactionInput` can be created from `ParsedTransaction` (from CSV parser)
- `CategorizationResult` maps directly to Transaction model fields
- Cache integrates with categorizer service (Task Group 4)

## Testing Notes

- 31 new tests added (11 schemas/exceptions, 10 mapping, 10 cache)
- All 93 project tests pass
- Ruff linting and mypy type checking pass
- Fixed timezone comparison bug during quality review
