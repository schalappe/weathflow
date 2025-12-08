# Implementation: Task Groups 4-5 (Categorizer Service & Integration Tests)

**Date:** 2025-12-08
**Task Groups:** 4 (Transaction Categorizer Service) and 5 (Integration Testing)
**Implementer:** implement-task command

## Summary

Implemented the core `TransactionCategorizer` service that categorizes bank transactions into Money Map types using a three-tier pipeline (cache → deterministic rules → Claude API) and comprehensive integration tests.

## Architecture Approach

Selected **Minimal Changes** approach:
- Single class following `BankinCSVParser` pattern
- Used SDK's built-in retry (`Anthropic(max_retries=3)`) instead of tenacity
- Synchronous processing as per user preference
- Fail-fast on batch errors

## Files Created

### `backend/app/services/categorizer.py`
Main categorizer service (~370 lines) with:
- `TransactionCategorizer` class with ClassVar constants (MODEL, BATCH_SIZE, MAX_TOKENS, MAX_RETRIES)
- Constructor accepting `api_key` and optional `cache` for dependency injection
- Main `categorize()` method orchestrating the three-tier pipeline
- Private helpers:
  - `_check_cache()` - Cache lookup for recurring patterns
  - `_apply_deterministic_rules()` - Internal transfer detection + Bankin' mapping
  - `_categorize_with_api()` - Batch processing (50 per call)
  - `_call_claude_api()` - SDK call with exception handling
  - `_build_user_prompt()` - Format transactions as JSON for Claude
  - `_parse_response()` - JSON parsing with markdown stripping
  - `_update_cache()` - Cache high-confidence results

### `backend/tests/units/services/test_categorizer.py`
Comprehensive test suite (16 tests) organized by scenario:
- `TestTransactionCategorizerCache` - Cache lookup tests
- `TestTransactionCategorizerDeterministicRules` - Rule-based categorization
- `TestTransactionCategorizerAPI` - API integration with mocked client
- `TestTransactionCategorizerRetry` - Error handling and retry behavior
- `TestTransactionCategorizerResponseParsing` - JSON parsing edge cases
- `TestTransactionCategorizerMixedPipeline` - Full pipeline scenarios
- `TestTransactionCategorizerEmptyInput` - Edge cases
- `TestTransactionCategorizerCachePersistence` - Cache update behavior

## Key Implementation Details

### Pipeline Flow
```bash
Input: list[TransactionInput]
    ↓
[1] Cache Lookup
    └─ Hits returned immediately
    ↓
[2] Deterministic Rules
    ├─ Internal transfers → EXCLUDED
    └─ Known Bankin' mappings → Money Map type
    ↓
[3] Claude API (batched, 50/call)
    ├─ Build JSON prompt
    ├─ Call API with built-in retry
    └─ Parse JSON response
    ↓
[4] Merge & Return
    └─ Results in original order
```

### Deviation from Spec
- **Spec said**: Use `tenacity` with `@retry` decorator
- **Implemented**: Used SDK's built-in `max_retries=3`
- **Reason**: Simpler, SDK already provides exponential backoff

### Error Handling
- `APIConnectionError` - After SDK exhausts 3 retries
- `InvalidResponseError` - Malformed JSON from Claude
- `BatchCategorizationError` - Missing transactions in response

## Integration Points

- **Input**: `TransactionInput` schema from `schemas.py`
- **Output**: `CategorizationResult` schema matching input order by ID
- **Cache**: Uses `CategorizationCache` for persistence
- **Mapping**: Uses `CategoryMapping` for deterministic rules
- **Prompt**: Uses `CATEGORIZATION_SYSTEM_PROMPT` constant

## Testing Notes

All tests use mocked Anthropic client to avoid real API calls:
```python
self.categorizer._client = MagicMock()
mock_response = MagicMock()
mock_response.content = [MagicMock(text='[...]')]
self.mock_client.messages.create.return_value = mock_response
```

Coverage includes:
- Cache hit/miss scenarios
- Deterministic rule matching
- API response parsing (valid JSON, markdown-wrapped, malformed)
- Error propagation (connection errors, rate limits)
- Mixed pipeline with all three paths
- Result ordering preservation
