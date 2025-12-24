# Specification: Advice Date Eligibility Improvement

## Goal

Anchor advice generation eligibility to the last transaction date in the database rather than today's date, and provide extended historical context for first-time advice generation.

## User Stories

- As a user with October transactions viewing the app in December, I want to generate advice for September and October so that I can get recommendations based on months where I actually have data.
- As a new user generating my first advice, I want the AI to analyze all my available transaction history (up to 12 months) so that I get the most informed recommendations possible.

## Specific Requirements

**Eligibility Window Based on Transaction Data:**

- Find the most recent month with transactions in the database
- Allow advice generation only for that month and the previous month
- Example: If last transaction is October 2024, eligible months are September 2024 and October 2024
- Reject advice generation for months outside this 2-month window with clear error message

**Extended History for First Advice:**

- If no advice records exist in database: fetch up to 12 months of history
- If regenerating and it's the only advice record: also fetch 12 months (treat as first advice)
- Otherwise: fetch normal 3 months of history
- The `is_first_advice` flag indicates which scenario applies

**Backend Eligibility Service:**

- Create `eligibility.py` in `/backend/app/services/advice/`
- Implement `EligibilityResult` frozen dataclass with: `is_eligible`, `history_limit`, `is_first_advice`, `reason`
- Implement `check_eligibility()` function that queries repository for most recent month and advice count
- Use helper `_is_within_eligible_window()` for date arithmetic

**Backend API Enforcement:**

- Check eligibility in both `GET /api/advice/{year}/{month}` and `POST /api/advice/generate`
- Return eligibility info in `GetAdviceResponse` so frontend knows before user clicks
- Use dynamic `history_limit` from eligibility result instead of hardcoded `3`
- Return HTTP 403 with clear reason when generation is attempted for ineligible month

**Frontend Eligibility from Backend:**

- Remove the `isGenerationAllowed()` function from `advice-panel-content.tsx`
- Get eligibility status from `GET /api/advice` response
- Store `can_generate` in component state and use for UI decisions
- Display "Not available" message with backend-provided reason when ineligible

**Repository Extensions:**

- Add `get_most_recent()` to `MonthRepository` - returns newest month by year/month
- Add `has_any()` to `AdviceRepository` - checks if any advice exists
- Add `count()` to `AdviceRepository` - counts total advice records

## Visual Design

No visual assets provided. UI behavior remains the same - only the source of eligibility truth changes from frontend to backend.

## Existing Code to Leverage

**Reverted Eligibility Implementation — `git show 3e746f3:backend/app/services/advice/eligibility.py`**

- What it does: Previous implementation with `EligibilityResult` dataclass and `check_eligibility()` function
- How to reuse: Reference patterns for dataclass structure and window calculation logic
- Key methods: `_is_within_eligible_window()`, `_is_first_advice_scenario()`

**Advice Router — `/backend/app/api/advice.py`**

- What it does: Handles `/api/advice/generate` and `/api/advice/{year}/{month}` endpoints
- How to reuse: Insert eligibility check at line 105, use `eligibility.history_limit` for dynamic limit
- Key methods: `generate_advice()` (line 50), `get_advice()` (line 170)

**Month Repository — `/backend/app/repositories/month.py`**

- What it does: All database operations for months
- How to reuse: Add `get_most_recent()` method following existing patterns
- Key methods: `get_recent()`, `get_recent_with_transactions()`

**Advice Repository — `/backend/app/repositories/advice.py`**

- What it does: All database operations for advice records
- How to reuse: Add `has_any()` and `count()` methods
- Key methods: `get_by_month_id()`, `get_by_month_ids()`

**Frontend Advice Component — `/frontend/components/history/advice-panel-content.tsx`**

- What it does: Displays advice panel with generate/regenerate buttons
- How to reuse: Replace `isGenerationAllowed()` (lines 112-129) with backend-provided eligibility
- Key methods: `isGenerationAllowed()` (to be removed), reducer pattern for state

## Architecture Approach

**Component Design:**

| Component                                | Responsibility                          |
| ---------------------------------------- | --------------------------------------- |
| `eligibility.py` service                 | Determine eligibility and history limit |
| `EligibilityResult` dataclass            | Immutable result container              |
| `MonthRepository.get_most_recent()`      | Find newest month in database           |
| `AdviceRepository.has_any()` / `count()` | Check for first-advice scenario         |
| Router integration                       | Check eligibility, use dynamic limit    |
| Frontend state                           | Store eligibility from response         |

**Data Flow:**

```bash
GET /api/advice/{year}/{month}
    │
    ├─► MonthRepository.get_most_recent() ─► Last transaction month
    │
    ├─► EligibilityService.check_eligibility() ─► EligibilityResult
    │       ├─► is target in [last_month - 1, last_month]?
    │       └─► is first advice? (determines 3 vs 12)
    │
    └─► Response with eligibility: { can_generate, reason, is_first_advice }
```

```text
POST /api/advice/generate
    │
    ├─► Check eligibility (same as above)
    │
    ├─► If not eligible ─► HTTP 403 with reason
    │
    ├─► Fetch history with eligibility.history_limit (3 or 12)
    │
    └─► Generate advice with appropriate context
```

**Integration Points:**

- Router line 105: Replace `limit=3` with `eligibility.history_limit`
- Router line 92: Insert eligibility check after cache lookup
- Frontend `FETCH_SUCCESS`: Include `eligibility` from response in state
- Frontend render: Use `state.eligibility.can_generate` instead of `isGenerationAllowed()`

## Out of Scope

- Changes to advice prompt content or structure
- Changes to advice display UI beyond eligibility
- Transaction categorization logic
- Score calculation logic
- Month selector or history page changes
- Database schema changes
- Authentication or authorization
- Advice caching strategy changes
- Performance optimizations beyond the feature scope
- Internationalization of eligibility messages
