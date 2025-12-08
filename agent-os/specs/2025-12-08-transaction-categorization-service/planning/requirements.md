# Spec Requirements: Transaction Categorization Service

## Initial Description

Implement Claude API integration that categorizes transactions into Money Map categories (Core/Choice/Compound/Excluded) with batch processing for cost efficiency.

## Existing Specification Document

Primary specification exists at: `docs/product-development/features/03-transaction-categorization-service.md`

This document defines:

- Money Map categories (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED) with subcategories
- Bankin' to Money Map category mapping table
- French categorization prompt for Claude
- Input/output Pydantic models
- Batch processing configuration (50 tx/call, claude-sonnet-4-20250514)
- Error handling strategies
- File structure: `categorizer.py`, `categorization_prompt.py`, `category_mapping.py`
- Success metrics (90%+ accuracy, <30s for 100 tx, <$0.001/tx)

## Requirements Discussion

### First Round Questions

**Q1:** Retry mechanism configuration?
**Answer:** Use `tenacity` package. 3 retries with exponential backoff (1s, 2s, 4s).

**Q2:** Synchronous or asynchronous processing?
**Answer:** Synchronous. Caller waits for all batches to complete.

**Q3:** Implement caching for recurring patterns?
**Answer:** Yes, implement caching. Be meticulous about it (careful, thorough implementation).

**Q4:** Anything explicitly out of scope?
**Answer:** Follow the existing specification document. Anything not in it is out of scope.

### Existing Code to Reference

**Similar Service Identified:**

- `backend/app/services/csv_parser.py` - `BankinCSVParser` class
- `backend/app/services/exceptions.py` - Exception hierarchy pattern
- `backend/app/services/schemas.py` - Pydantic models with `FrozenModel` base

**Patterns to Replicate:**

1. **Service class pattern**: Main service as a class with methods
2. **Exception hierarchy**: Base exception (e.g., `CategorizationError`) with specific subclasses
3. **Pydantic models**: `FrozenModel` base with `frozen=True` for immutable data
4. **NumPy-style docstrings**: Detailed with Parameters, Returns, Raises sections
5. **Type annotations**: Full type hints on all public and private methods

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

Not applicable - this is a backend-only service.

## Requirements Summary

### Functional Requirements

1. **Claude API Integration**
   - Use `anthropic` SDK with `claude-sonnet-4-20250514` model
   - French categorization prompt as defined in spec
   - Return structured JSON with `money_map_type`, `money_map_subcategory`, `confidence`

2. **Batch Processing**
   - Batch 50 transactions per API call
   - Process batches sequentially (synchronous)
   - Use `tenacity` for retry logic (3 retries, exponential backoff)

3. **Caching**
   - Cache recurring transaction patterns
   - Example: "Netflix" → always CHOICE/Subscription services
   - Meticulous implementation (cache invalidation, lookup efficiency)

4. **Error Handling**
   - API rate limit: Exponential backoff with retry
   - Invalid JSON: Log error, mark batch for manual review
   - Missing confidence: Default to 1.0
   - Unknown category: Log warning, mark for review

### Reusability Opportunities

| Component             | Source                   | Reuse Strategy                                  |
| --------------------- | ------------------------ | ----------------------------------------------- |
| Exception hierarchy   | `services/exceptions.py` | Create parallel `CategorizationError` hierarchy |
| FrozenModel base      | `services/schemas.py`    | Import and extend for categorization models     |
| Pydantic patterns     | `services/schemas.py`    | Follow same structure for input/output models   |
| Service class pattern | `csv_parser.py`          | Class with `categorize()` method                |

### Scope Boundaries

**In Scope:**

- Claude API integration with batch processing
- Transaction categorization into Money Map categories
- Confidence scores for each categorization
- Caching for recurring patterns
- Error handling with retry logic
- Pydantic models for input/output

**Out of Scope:**

- Learning from user corrections (deferred)
- Multi-language prompts
- Custom category definitions
- Database persistence (handled by caller)
- Pre-filtering of internal transfers (mentioned but not core)
- Progress callbacks or async patterns

### Technical Considerations

| Area            | Decision                   |
| --------------- | -------------------------- |
| Package manager | `uv`                       |
| Retry library   | `tenacity`                 |
| Model           | `claude-sonnet-4-20250514` |
| Batch size      | 50 transactions            |
| Max tokens      | 4096                       |
| Processing      | Synchronous                |

### File Structure (from spec)

```text
backend/app/services/
├── categorizer.py           # Main categorization service
├── categorization_prompt.py # System prompt constant
└── category_mapping.py      # Bankin' to Money Map mapping
```

### Dependencies

- **Internal**: CSV Parser Service (provides `ParsedTransaction`)
- **External**: `anthropic` SDK, `tenacity`
