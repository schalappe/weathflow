# Spec Requirements: Advice Generation Service

## Initial Description

Implement Claude API integration that analyzes the last 3 months and generates personalized recommendations with trend analysis.

## Requirements Discussion

### First Round Questions

**Q1:** Analysis Window - Fixed at 3 months or configurable?
**Answer:** Fixed at 3 months (per feature doc)

**Q2:** Advice Structure - What sections should be included?
**Answer:** Per feature doc: analysis (2-3 sentences), problem_areas (top 3), recommendations (3), encouragement

**Q3:** Trend Detection Logic - Simple percentage change or more sophisticated?
**Answer:** Simple percentage change calculation between current and previous values (per feature doc)

**Q4:** Minimum Data Requirement - What if user has fewer than 3 months?
**Answer:** Minimum 2 months required. Raises `InsufficientDataError` if less (per feature doc)

**Q5:** Regeneration Behavior - Any constraints?
**Answer:** Out of scope for this feature (covered in Feature 15: Advice API and Storage)

**Q6:** Advice Storage - One per month or keep history?
**Answer:** Out of scope for this feature (covered in Feature 15: Advice API and Storage)

**Q7:** Exclusions - What to exclude?
**Answer:** API endpoints, database storage, UI components (all covered in Features 15-16)

### Follow-up Questions

**Follow-up 1:** Should we include transaction-level category breakdowns in the prompt to Claude?
**Answer:** Yes, include transaction-level category breakdowns (e.g., "Subscriptions: 85EUR", "Dining: 120EUR")

**Follow-up 2:** Should this spec focus only on the AdviceGenerator service class?
**Answer:** Yes, focus only on the AdviceGenerator service class

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Transaction Categorization Service - Path: `backend/app/services/categorizer.py` (likely)
- Components to potentially reuse: Claude API integration patterns, response parsing, error handling
- Backend logic to reference: Service layer patterns from other services

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Insights

N/A - This is a backend service with no UI component.

## Feature Documentation Reference

Complete technical specification exists at: `docs/product-development/features/14-advice-generation-service.md`

Key specifications from document:

- **Service Location**: `backend/app/services/advisor.py`
- **Class Name**: `AdviceGenerator`
- **Method**: `async def generate_advice(current_month: MonthData, history: list[MonthData]) -> AdviceResponse`
- **Model**: `claude-sonnet-4-20250514`
- **Max Tokens**: 1024
- **Language**: French

### Data Models (from doc)

```python
class ProblemArea(BaseModel):
    category: str
    amount: float
    trend: str  # e.g., "+20%", "-5%"

class AdviceResponse(BaseModel):
    analysis: str  # 2-3 sentence trend analysis
    problem_areas: list[ProblemArea]  # Top 3 spending concerns
    recommendations: list[str]  # 3 actionable suggestions
    encouragement: str  # Personalized encouragement message
```

### Error Handling (from doc)

```python
class AdviceGenerationError(Exception):
    """Raised when advice generation fails."""
    pass

class InsufficientDataError(AdviceGenerationError):
    """Raised when there is not enough historical data."""
    pass
```

### Configuration (from doc)

```python
MIN_MONTHS_FOR_ADVICE = 2
ADVICE_MODEL = "claude-sonnet-4-20250514"
ADVICE_MAX_TOKENS = 1024
```

## Requirements Summary

### Functional Requirements

- Analyze last 3 months of financial data
- Calculate month-over-month trends for each category
- Include transaction-level category breakdowns in Claude prompt
- Identify top 3 spending categories that are increasing (problem areas)
- Generate 3 concrete, actionable improvement suggestions
- Provide personalized encouragement message
- Return structured JSON response via Claude API
- Handle edge cases: zero income (division by zero), insufficient data

### Non-Functional Requirements

- All advice generated in French
- Use `claude-sonnet-4-20250514` model
- Max 1024 tokens for response
- Graceful error handling with custom exceptions

### Reusability Opportunities

- Claude API client patterns from Transaction Categorization Service
- Error handling patterns from existing services
- Service layer architecture patterns

### Scope Boundaries

**In Scope:**

- `AdviceGenerator` service class
- `generate_advice()` method
- Pydantic models: `ProblemArea`, `AdviceResponse`, `MonthData` (input)
- Trend calculation utility function
- Custom exceptions: `AdviceGenerationError`, `InsufficientDataError`
- Claude API prompt construction
- Response parsing and validation
- Unit tests for service

**Out of Scope:**

- API endpoints (Feature 15)
- Database storage/caching (Feature 15)
- Advice retrieval endpoints (Feature 15)
- UI components (Feature 16)
- Regeneration logic (Feature 15)
- Any frontend code

### Technical Considerations

- Must integrate with existing `MonthData` structure from historical data API
- Follow existing service layer patterns in codebase
- Use async/await for Claude API calls
- Handle JSON parsing errors from Claude response
- Validate Claude returns expected structure before returning
