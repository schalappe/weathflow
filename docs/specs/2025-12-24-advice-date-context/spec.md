# Specification: Advice Date Context Improvement

## Goal

Fix advice generation eligibility to use the last transaction date as reference (instead of today's date), and provide extended historical context (12 months) for first-time advice generation to give Claude maximum insight for initial recommendations.

## User Stories

- As a user, I want to generate advice for months with actual transaction data so that I receive relevant recommendations based on real spending patterns
- As a new user, I want my first advice to analyze all my historical data so that Claude can provide the most informed initial recommendations
- As a returning user, I want to regenerate my first advice with the same extended context so that I maintain consistency in my financial tracking

## Specific Requirements

**Date-Based Eligibility:**

- Advice eligibility must reference the last month with transactions, not today's date
- Only the 2 most recent months (relative to last transaction) are eligible for advice generation
- If last transaction is October 2025, eligible months are October and September only
- Requesting advice for ineligible months returns HTTP 400 with clear error message

**First Advice Extended Context:**

- Detect "first advice" scenario: no advice records exist anywhere in the database
- For first advice, fetch up to 12 months of historical data (instead of 3)
- Still enforce 2-month minimum requirement (first advice needs at least 2 months)
- All transactions from included months are sent to Claude for pattern analysis

**Regeneration Behavior:**

- When regenerating the chronologically first advice record: use extended 12-month context
- When regenerating any subsequent advice: use regular 3-month context
- Detection based on whether target month is the earliest month with advice potential

**Error Handling:**

- Month too old: "Advice can only be generated for the 2 most recent months. Your last transaction is in {year}-{month}."
- Month doesn't exist: "No transaction data found for {year}-{month}. Upload transactions first."
- Insufficient data: "Not enough historical data. Please upload at least 2 months of transactions."

## Visual Design

No visual assets - this is a backend-only change with no UI modifications.

## Existing Code to Leverage

**MonthRepository — `backend/app/repositories/month.py`**

- What it does: Data access for months with eager loading of transactions
- How to reuse: Add `get_most_recent_month()` method following existing query patterns
- Key methods: `get_recent_with_transactions(limit)` already supports variable limits

**AdviceRepository — `backend/app/repositories/advice.py`**

- What it does: Data access for advice records with batch lookups
- How to reuse: Add `has_any_advice()` method for first-advice detection
- Key methods: `get_by_month_ids()` for batch queries, `upsert()` for create/update

**AdviceGenerationError Hierarchy — `backend/app/services/exceptions.py`**

- What it does: Domain exceptions with structured error information
- How to reuse: Add `MonthNotEligibleError` following existing exception patterns
- Key methods: Existing exceptions like `InsufficientDataError` provide template

**Advice Router — `backend/app/api/advice.py`**

- What it does: Orchestrates advice generation with thin controller pattern
- How to reuse: Insert eligibility check before generation, use dynamic history limit
- Key methods: Line 105 has hardcoded `limit=3` to replace with dynamic value

**Months Service — `backend/app/services/data/months.py`**

- What it does: Service wrapper around month repository with error handling
- How to reuse: Add wrapper for `get_most_recent_month()` with error handling
- Key methods: `get_months_history_with_transactions(limit)` already supports variable limits

## Architecture Approach

**Component Design:**

- New module `eligibility.py` encapsulates all eligibility and context determination logic
- `EligibilityResult` dataclass carries eligibility status, history limit, and first-advice flag
- Pure functions for eligibility checks enable easy unit testing
- Follows existing thin-router pattern where services contain business logic

**Data Flow:**

1. Router receives generate request with year/month
2. Router calls `check_eligibility()` with repositories
3. Eligibility service queries most recent month and checks advice existence
4. Returns `EligibilityResult` with computed `history_limit` (3 or 12)
5. Router uses dynamic limit instead of hardcoded 3
6. If ineligible, raise `MonthNotEligibleError` → HTTP 400

**Integration Points:**

- `MonthRepository`: New `get_most_recent_month()` method (single query)
- `AdviceRepository`: New `has_any_advice()` method (existence check)
- `exceptions.py`: New `MonthNotEligibleError` in existing hierarchy
- `advice.py` router: Replace hardcoded limit with eligibility result
- No changes to Claude prompt, transaction filtering, or advice storage

**Constants (in `eligibility.py`):**

- `REGULAR_HISTORY_LIMIT = 3` — Normal context window
- `EXTENDED_HISTORY_LIMIT = 12` — First advice context window
- `MIN_MONTHS_REQUIRED = 2` — Minimum months for any advice
- `ELIGIBLE_MONTH_WINDOW = 2` — Only 2 most recent months eligible

## Out of Scope

- Changing the Claude prompt structure or content
- Modifying transaction filtering logic (CORE/CHOICE/COMPOUND)
- Frontend/UI changes or new frontend components
- Adding new API endpoints (only modifying existing generate endpoint)
- Changing advice storage format or database schema
- Modifying the scoring system or calculation logic
- Adding user-configurable history limits
- Caching eligibility results
- Adding eligibility information to month listing endpoints
