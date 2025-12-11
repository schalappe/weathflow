# Task Breakdown: Advice Generation Service

## Overview

Total Tasks: 18
Estimated Complexity: Medium
Primary Stack: Python (FastAPI + Pydantic + Anthropic SDK)

## Task List

### Foundation Layer

#### Task Group 1: DTOs and Exceptions

**Dependencies:** None

- [x] 1.0 Complete foundation layer (DTOs and exceptions)
  - [x] 1.1 Write 4 focused tests for DTOs and exceptions
    - Test `MonthData` validation with valid data
    - Test `ProblemArea` immutability (FrozenModel)
    - Test `AdviceResponse` field validation
    - Test `InsufficientDataError` attributes
  - [x] 1.2 Create advice DTOs in `backend/app/services/dto/advice.py`
    - `MonthData`: year, month, totals, percentages, score, score_label, category_breakdown
    - `ProblemArea`: category, amount, trend
    - `AdviceResponse`: analysis, problem_areas, recommendations, encouragement
    - Inherit from `FrozenModel` base class
    - Reuse pattern from: `backend/app/services/dto/categorization.py`
  - [x] 1.3 Add advice exceptions to `backend/app/services/exceptions.py`
    - `AdviceGenerationError` as base exception
    - `InsufficientDataError(min_months_required: int)`
    - `AdviceAPIError(retry_count: int)`
    - `AdviceParseError(raw_response: str)`
    - Follow pattern from existing `CategorizationError` hierarchy
  - [x] 1.4 Ensure foundation tests pass
    - Run ONLY tests from 1.1
    - Verify DTOs are immutable
    - Verify exceptions have correct attributes

**Acceptance Criteria:**

- All 4 tests from 1.1 pass
- DTOs inherit from `FrozenModel` and are immutable
- Exceptions follow existing hierarchy pattern
- All type annotations are complete

---

### Prompt Layer

#### Task Group 2: System Prompt

**Dependencies:** None (can run in parallel with Task Group 1)

- [x] 2.0 Complete prompt layer
  - [x] 2.1 Write 2 focused tests for prompt module
    - Test `ADVICE_SYSTEM_PROMPT` is non-empty string
    - Test prompt contains required keywords (Money Map, JSON, French)
  - [x] 2.2 Create prompts package `backend/app/services/prompts/__init__.py`
    - Empty `__init__.py` for package structure
  - [x] 2.3 Create `backend/app/services/prompts/advice_prompt.py`
    - Define `ADVICE_SYSTEM_PROMPT` constant in French
    - Include Money Map rules (50/30/20)
    - Specify exact JSON output format
    - Request: analysis, 3 problem_areas, 3 recommendations, encouragement
    - Reuse pattern from: `backend/app/services/categorization_prompt.py`
  - [x] 2.4 Ensure prompt tests pass
    - Run ONLY tests from 2.1

**Acceptance Criteria:**

- All 2 tests from 2.1 pass
- Prompt is written in French
- JSON output format is clearly specified
- Money Map rules are included

---

### Utility Layer

#### Task Group 3: Trend Calculation

**Dependencies:** Task Group 1

- [x] 3.0 Complete utility layer
  - [x] 3.1 Write 5 focused tests for trend calculation
    - Test positive trend returns "+15%" format
    - Test negative trend returns "-8%" format
    - Test zero change returns "+0%"
    - Test previous value of zero returns "N/A"
    - Test large percentage changes (> 100%)
  - [x] 3.2 Create `calculate_trend` function in `backend/app/services/advisor.py`
    - Module-level function (not class method) for testability
    - Parameters: `current: float`, `previous: float`
    - Return type: `str`
    - Handle division by zero edge case
    - Format: "+XX%" or "-XX%" or "N/A"
  - [x] 3.3 Ensure trend tests pass
    - Run ONLY tests from 3.1

**Acceptance Criteria:**

- All 5 tests from 3.1 pass
- Division by zero handled gracefully
- Output format is consistent

---

### Service Layer

#### Task Group 4: AdviceGenerator Class Structure

**Dependencies:** Task Groups 1, 2, 3

- [x] 4.0 Complete service class structure
  - [x] 4.1 Write 3 focused tests for class initialization
    - Test `__init__` accepts api_key, base_url, model parameters
    - Test default model is loaded from settings
    - Test `ClassVar` constants are set correctly
  - [x] 4.2 Create `AdviceGenerator` class in `backend/app/services/advisor.py`
    - `ClassVar` constants: `MIN_MONTHS_REQUIRED = 2`, `MAX_TOKENS = 1024`, `MAX_RETRIES = 3`
    - `__init__(api_key: str, base_url: str | None = None, model: str | None = None)`
    - Initialize `Anthropic` client with `max_retries=3`
    - Load model from settings if not provided
    - Reuse pattern from: `backend/app/services/categorizer.py`
  - [x] 4.3 Ensure class structure tests pass
    - Run ONLY tests from 4.1

**Acceptance Criteria:**

- All 3 tests from 4.1 pass
- Class follows `TransactionCategorizer` pattern
- Settings integration works correctly

---

#### Task Group 5: Input Validation

**Dependencies:** Task Group 4

- [x] 5.0 Complete input validation
  - [x] 5.1 Write 3 focused tests for validation
    - Test raises `InsufficientDataError` with 0 months
    - Test raises `InsufficientDataError` with 1 month
    - Test passes validation with 2+ months
  - [x] 5.2 Implement `_validate_data` method
    - Check `len(history) >= 1` (current + 1 history = 2 minimum)
    - Raise `InsufficientDataError(min_months_required=2)` if insufficient
    - Method signature: `_validate_data(self, current_month: MonthData, history: list[MonthData]) -> None`
  - [x] 5.3 Ensure validation tests pass
    - Run ONLY tests from 5.1

**Acceptance Criteria:**

- All 3 tests from 5.1 pass
- Correct error raised with helpful message
- Edge cases handled (empty list, single item)

---

#### Task Group 6: Prompt Building

**Dependencies:** Task Groups 4, 5

- [x] 6.0 Complete prompt building
  - [x] 6.1 Write 3 focused tests for prompt building
    - Test JSON output contains all month data
    - Test `ensure_ascii=False` preserves French characters
    - Test category breakdown is included when present
  - [x] 6.2 Implement `_build_user_prompt` method
    - Format months as list of dictionaries
    - Include: year, month, totals, percentages, score, score_label
    - Include category_breakdown when available
    - Use `json.dumps(data, ensure_ascii=False, indent=2)`
    - Add instruction to return ONLY JSON
    - Reuse pattern from: `categorizer._build_user_prompt()`
  - [x] 6.3 Ensure prompt building tests pass
    - Run ONLY tests from 6.1

**Acceptance Criteria:**

- All 3 tests from 6.1 pass
- French characters preserved in output
- All required data fields included

---

#### Task Group 7: Claude API Call

**Dependencies:** Task Group 6

- [x] 7.0 Complete Claude API integration
  - [x] 7.1 Write 4 focused tests for API call (mocked)
    - Test successful API call returns response text
    - Test `AuthenticationError` raises `AdviceGenerationError`
    - Test `APIConnectionError` raises `AdviceAPIError`
    - Test empty response raises `AdviceParseError`
  - [x] 7.2 Implement `_call_claude_api` method
    - Call `self._client.messages.create()`
    - Parameters: model, max_tokens=1024, system=ADVICE_SYSTEM_PROMPT, messages
    - Handle `anthropic.AuthenticationError` → `AdviceGenerationError`
    - Handle `anthropic.APIConnectionError`, `RateLimitError` → `AdviceAPIError`
    - Handle `anthropic.APIStatusError` → `AdviceAPIError`
    - Validate response has content
    - Return `response.content[0].text`
    - Reuse pattern from: `categorizer._call_claude_api()`
  - [x] 7.3 Ensure API call tests pass
    - Run ONLY tests from 7.1
    - Use mocked Anthropic client

**Acceptance Criteria:**

- All 4 tests from 7.1 pass
- All Anthropic exceptions mapped to domain exceptions
- Response validation before returning

---

#### Task Group 8: Response Parsing

**Dependencies:** Task Group 7

- [x] 8.0 Complete response parsing
  - [x] 8.1 Write 4 focused tests for response parsing
    - Test valid JSON creates `AdviceResponse`
    - Test markdown code blocks are stripped
    - Test invalid JSON raises `AdviceParseError`
    - Test missing fields raise `AdviceParseError`
  - [x] 8.2 Implement `_parse_response` method
    - Strip leading/trailing whitespace
    - Remove markdown code blocks if present (```json...```)
    - Parse JSON with `json.loads()`
    - Validate structure: analysis, problem_areas, recommendations, encouragement
    - Create `ProblemArea` objects from problem_areas list
    - Return `AdviceResponse` DTO
    - Raise `AdviceParseError(raw_response)` on failure
    - Reuse pattern from: `categorizer._parse_response()`
  - [x] 8.3 Ensure parsing tests pass
    - Run ONLY tests from 8.1

**Acceptance Criteria:**

- All 4 tests from 8.1 pass
- Markdown stripping works correctly
- All field validations in place

---

#### Task Group 9: Main Method Integration

**Dependencies:** Task Groups 5, 6, 7, 8

- [x] 9.0 Complete main method integration
  - [x] 9.1 Write 2 focused tests for `generate_advice`
    - Test full flow with valid data returns `AdviceResponse`
    - Test insufficient data raises `InsufficientDataError`
  - [x] 9.2 Implement `generate_advice` public method
    - Method signature: `def generate_advice(self, current_month: MonthData, history: list[MonthData]) -> AdviceResponse`
    - Step 1: `_validate_data(current_month, history)`
    - Step 2: `prompt = _build_user_prompt(current_month, history)`
    - Step 3: `response_text = _call_claude_api(prompt)`
    - Step 4: `return _parse_response(response_text)`
    - Add logging at each step
  - [x] 9.3 Ensure integration tests pass
    - Run ONLY tests from 9.1
    - Use mocked Anthropic client

**Acceptance Criteria:**

- All 2 tests from 9.1 pass
- All methods called in correct order
- Logging provides visibility into flow

---

### Testing Layer

#### Task Group 10: Test Review and Gap Analysis

**Dependencies:** Task Groups 1-9

- [x] 10.0 Review tests and fill critical gaps
  - [x] 10.1 Review all tests from Task Groups 1-9
    - Foundation: 4 tests (DTOs, exceptions)
    - Prompt: 2 tests
    - Utility: 5 tests (trend calculation)
    - Service: 3 + 3 + 3 + 4 + 4 + 2 = 19 tests
    - Total existing: ~30 tests
  - [x] 10.2 Identify critical gaps (if any)
    - Check edge case: zero income handling
    - Check edge case: very large trend percentages
    - Check integration between components
  - [x] 10.3 Add up to 4 additional strategic tests if needed
    - Focus on integration points not covered
    - Skip exhaustive edge case coverage
  - [x] 10.4 Run all feature tests
    - Run complete test suite for advisor module
    - Expected total: ~30-34 tests
    - Verify all pass

**Acceptance Criteria:**

- All feature tests pass (~30-34 total)
- Critical integration points covered
- No more than 4 additional tests added

---

## Execution Order

Recommended implementation sequence:

| Order | Task Group    | Description              | Duration |
| ----- | ------------- | ------------------------ | -------- |
| 1     | Task Group 1  | DTOs and Exceptions      | 45 min   |
| 1     | Task Group 2  | System Prompt (parallel) | 30 min   |
| 2     | Task Group 3  | Trend Calculation        | 30 min   |
| 3     | Task Group 4  | Class Structure          | 45 min   |
| 4     | Task Group 5  | Input Validation         | 30 min   |
| 5     | Task Group 6  | Prompt Building          | 45 min   |
| 6     | Task Group 7  | Claude API Call          | 60 min   |
| 7     | Task Group 8  | Response Parsing         | 45 min   |
| 8     | Task Group 9  | Main Method              | 30 min   |
| 9     | Task Group 10 | Test Review              | 30 min   |

**Total Estimated Time:** ~6.5 hours

## Files to Create/Modify

| File                                            | Action | Task Group          |
| ----------------------------------------------- | ------ | ------------------- |
| `backend/app/services/dto/advice.py`            | Create | 1                   |
| `backend/app/services/exceptions.py`            | Modify | 1                   |
| `backend/app/services/prompts/__init__.py`      | Create | 2                   |
| `backend/app/services/prompts/advice_prompt.py` | Create | 2                   |
| `backend/app/services/advisor.py`               | Create | 3, 4, 5, 6, 7, 8, 9 |
| `backend/tests/units/services/test_advisor.py`  | Create | 1-10                |

## Reference Files

Existing code to follow as patterns:

- `backend/app/services/categorizer.py` - Class structure, API call, response parsing
- `backend/app/services/categorization_prompt.py` - System prompt pattern
- `backend/app/services/dto/categorization.py` - DTO pattern with FrozenModel
- `backend/app/services/exceptions.py` - Exception hierarchy pattern
