# Specification: Advice Generation Service

## Goal

Implement an `AdviceGenerator` service class that uses Claude API to analyze the last 3 months of financial data and generate personalized recommendations with trend analysis in French.

## User Stories

- As a user, I want to receive AI-generated advice based on my spending history so that I can improve my Money Map score.
- As a user, I want to see which spending categories are trending upward so that I can identify problem areas.

## Specific Requirements

**Service Class Structure:**

- Create `AdviceGenerator` class in `backend/app/services/advisor.py`
- Use `ClassVar` for constants: `MIN_MONTHS_REQUIRED = 2`, `MAX_TOKENS = 1024`, `MAX_RETRIES = 3`
- Accept `api_key`, optional `base_url`, optional `model` in `__init__`
- Initialize `Anthropic` client with `max_retries=3`
- Load model from settings if not provided

**Input Validation:**

- Require minimum 2 months of data (current + at least 1 history month)
- Raise `InsufficientDataError` if data requirement not met
- Handle zero income edge case (return 0.0 percentages)

**Trend Calculation:**

- Create module-level `calculate_trend(current: float, previous: float) -> str` function
- Return formatted string like "+15%" or "-8%"
- Return "N/A" when previous value is zero

**Prompt Construction:**

- Create system prompt in separate file `backend/app/services/prompts/advice_prompt.py`
- Format month data as JSON with `ensure_ascii=False` for French characters
- Include category breakdowns when available for detailed problem area identification
- Request exactly 3 problem areas, 3 recommendations, analysis, and encouragement

**Claude API Call:**

- Use `claude-sonnet-4-20250514` model
- Set `max_tokens=1024`
- Handle `AuthenticationError`, `APIConnectionError`, `RateLimitError`, `APIStatusError`
- Wrap errors in domain-specific exceptions

**Response Parsing:**

- Strip markdown code blocks if Claude wraps response
- Parse JSON and validate against `AdviceResponse` model
- Raise `AdviceParseError` on invalid JSON or missing fields

**Data Transfer Objects:**

- Create `MonthData`, `ProblemArea`, `AdviceResponse` in `backend/app/services/dto/advice.py`
- Use `FrozenModel` base class for immutability
- Include all fields from feature doc specification

**Exception Hierarchy:**

- Add to existing `backend/app/services/exceptions.py`
- `AdviceGenerationError` as base exception
- `InsufficientDataError(min_months_required: int)`
- `AdviceAPIError(retry_count: int)`
- `AdviceParseError(raw_response: str)`

## Visual Design

No visual assets provided - this is a backend service with no UI component.

## Existing Code to Leverage

**TransactionCategorizer - `backend/app/services/categorizer.py`**

- What it does: Claude API integration for transaction categorization with batching, caching, and error handling
- How to reuse: Replicate the class structure, `__init__` pattern, API call handling, and response parsing logic
- Key methods: `_build_user_prompt()`, `_call_claude_api()`, `_parse_response()`
- Found by: code-explorer analysis of categorization service

**System Prompt Pattern - `backend/app/services/categorization_prompt.py`**

- What it does: Defines French system prompt as module constant
- How to reuse: Create similar `advice_prompt.py` with `ADVICE_SYSTEM_PROMPT` constant
- Key exports: `CATEGORIZATION_SYSTEM_PROMPT`
- Found by: code-explorer analysis of prompt patterns

**Exception Hierarchy - `backend/app/services/exceptions.py`**

- What it does: Domain exceptions with programmatic attributes (retry_count, raw_response)
- How to reuse: Add new advice exceptions following same pattern
- Key classes: `CategorizationError`, `APIConnectionError`, `InvalidResponseError`
- Found by: code-explorer analysis of service patterns

**FrozenModel Base - `backend/app/services/dto/_base.py`**

- What it does: Pydantic base model with `frozen=True` for immutable DTOs
- How to reuse: Inherit from `FrozenModel` for all advice DTOs
- Key exports: `FrozenModel`
- Found by: code-explorer analysis of DTO patterns

**MonthHistory Model - `backend/app/responses/history.py`**

- What it does: Response model with all monthly financial data fields
- How to reuse: Reference field structure for `MonthData` input DTO
- Key fields: year, month, totals, percentages, score, score_label
- Found by: code-explorer analysis of month data structures

## Architecture Approach

**Component Design:**

- `AdviceGenerator` class: orchestrates validation, prompt building, API call, response parsing
- DTOs in `services/dto/advice.py`: `MonthData`, `ProblemArea`, `AdviceResponse`
- Prompt in `services/prompts/advice_prompt.py`: `ADVICE_SYSTEM_PROMPT` constant
- Exceptions added to existing `services/exceptions.py`

**Data Flow:**

- Input: `current_month (MonthData)` + `history (list[MonthData])`
- Validate: Check minimum months, raise `InsufficientDataError` if needed
- Calculate: Compute trends between current and previous month
- Build: Format data as JSON prompt with category breakdowns
- Call: Send to Claude API with system prompt
- Parse: Strip markdown, validate JSON, create `AdviceResponse`
- Output: Immutable `AdviceResponse` with analysis, problem_areas, recommendations, encouragement

**Integration Points:**

- Settings: Use `get_settings()` for API key and model configuration
- Exceptions: Follows existing exception patterns in `services/exceptions.py`
- DTOs: Uses `FrozenModel` base class from `services/dto/_base.py`
- Router (Feature 15): Service will be injected via `Depends(_get_advice_generator)`

## Out of Scope

- API endpoints (covered in Feature 15: Advice API and Storage)
- Database storage of generated advice (covered in Feature 15)
- Advice retrieval endpoints (covered in Feature 15)
- Caching or regeneration logic (covered in Feature 15)
- UI components for displaying advice (covered in Feature 16)
- Any frontend code
- Batch processing of multiple months' advice
- Multi-language support (French only)
- Comparison with external benchmarks or other users
- Integration with external financial APIs
