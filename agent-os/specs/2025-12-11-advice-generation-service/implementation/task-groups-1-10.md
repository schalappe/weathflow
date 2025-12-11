# Implementation: Advice Generation Service (Task Groups 1-10)

**Date:** 2025-12-11
**Task Groups:** 1-10 (Complete Service Implementation)
**Implementer:** implement-task command

## Summary

Implemented the complete `AdviceGenerator` service class that uses Claude API to analyze financial data and generate personalized recommendations in French. The implementation follows the existing `TransactionCategorizer` pattern for consistency.

## Architecture Approach

Selected **minimal changes approach** that mirrors existing codebase patterns:

- Synchronous API (matching `TransactionCategorizer`)
- `FrozenModel` DTOs for immutability
- Domain-specific exception hierarchy
- Module-level utility function (`calculate_trend`) for testability

## Files Created

- `backend/app/services/dto/advice.py` - DTOs: `MonthData`, `ProblemArea`, `AdviceResponse`
- `backend/app/services/prompts/__init__.py` - Package initialization
- `backend/app/services/prompts/advice_prompt.py` - French system prompt constant
- `backend/app/services/advisor.py` - Main `AdviceGenerator` service class
- `backend/tests/units/services/test_advisor.py` - 32 unit tests

## Files Modified

- `backend/app/services/exceptions.py` - Added `AdviceGenerationError`, `InsufficientDataError`, `AdviceAPIError`, `AdviceParseError`

## Key Implementation Details

### DTOs (Task Group 1)

```python
class MonthData(FrozenModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    total_income: float
    # ... financial totals and percentages
    category_breakdown: dict[str, float] | None = None

class ProblemArea(FrozenModel):
    category: str
    amount: float
    trend: str  # e.g., '+20%', '-5%', 'N/A'

class AdviceResponse(FrozenModel):
    analysis: str
    problem_areas: list[ProblemArea]
    recommendations: list[str]
    encouragement: str
```

### Exception Hierarchy (Task Group 1)

```text
AdviceGenerationError (base)
├── InsufficientDataError(min_months_required: int)
├── AdviceAPIError(retry_count: int)
└── AdviceParseError(raw_response: str)
```

### System Prompt (Task Group 2)

- Written entirely in French
- Defines Money Map rules (50/30/20)
- Specifies exact JSON output format
- Requests: analysis, 3 problem_areas, 3 recommendations, encouragement

### AdviceGenerator Service (Task Groups 3-9)

```python
class AdviceGenerator:
    MIN_MONTHS_REQUIRED: ClassVar[int] = 2
    MAX_TOKENS: ClassVar[int] = 1024
    MAX_RETRIES: ClassVar[int] = 3

    def generate_advice(self, current_month: MonthData, history: list[MonthData]) -> AdviceResponse:
        # 1. Validate data (min 2 months required)
        # 2. Build user prompt with JSON-serialized month data
        # 3. Call Claude API with system prompt
        # 4. Parse JSON response into AdviceResponse
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `calculate_trend()` | Module-level function for trend calculation ('+15%', '-8%', 'N/A') |
| `_validate_data()` | Ensures minimum 2 months of data |
| `_build_user_prompt()` | Formats months as JSON with `ensure_ascii=False` |
| `_call_claude_api()` | Handles API call with exception mapping |
| `_parse_response()` | Strips markdown, parses JSON, validates structure |

## Integration Points

- **Settings**: Uses `get_settings()` for API key and model configuration (lazy import)
- **Anthropic SDK**: Initialized with `max_retries=3` at client level
- **Exception Mapping**: All Anthropic exceptions mapped to domain exceptions

## Testing Notes

- 32 tests covering all task groups
- Tests organized by feature: DTOs, prompt, trend calculation, validation, API, parsing, integration
- Anthropic client mocked with `MagicMock()` for isolation
- All tests pass in 0.43s
