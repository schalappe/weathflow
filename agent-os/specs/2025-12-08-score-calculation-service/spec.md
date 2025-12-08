# Specification: Score Calculation Service

## Goal

Create a service that calculates Money Map percentages and scores (0-3) based on categorized transactions and the 50/30/20 thresholds, then persists results to the database.

## User Stories

- As a budget-conscious user, I want my monthly budget score calculated automatically after transactions are categorized so that I can see my Money Map health at a glance.
- As a user who corrects transaction categories, I want the month score to recalculate when I make changes so that my score always reflects accurate data.

## Specific Requirements

**Pure score calculation function:**

- Takes three percentages as input: `core_pct`, `choice_pct`, `compound_pct`
- Returns a tuple of `(score: int, label: ScoreLabel)`
- Awards +1 point if Core <= 50%, +1 if Choice <= 30%, +1 if Compound >= 20%
- Maps score to label: 3=Great, 2=Okay, 1=Need Improvement, 0=Poor
- No side effects - purely mathematical

**Pure month stats calculation function:**

- Takes three totals as input: `income`, `core`, `choice`
- Derives Compound as: `income - core - choice` (not summed from transactions)
- Calculates percentages as `(category / income) * 100`, rounded to 1 decimal
- Handles zero income edge case by returning zeroed stats with score 0
- Returns immutable `MonthStats` Pydantic model

**Database integration function:**

- Takes `db: Session` and `month_id: int` as input
- Aggregates transaction totals using a single efficient SQL query
- Filters by `MoneyMapType` (INCOME, CORE, CHOICE) - excludes EXCLUDED and COMPOUND
- Updates all stat fields on the Month model and commits
- Raises `MonthNotFoundError` if month_id doesn't exist
- Logs the update for observability

**MonthStats Pydantic schema:**

- Add to existing `backend/app/services/schemas.py`
- Inherit from `FrozenModel` for immutability
- Fields: `total_income`, `total_core`, `total_choice`, `total_compound`, percentages, `score`, `score_label`
- Use `Field(ge=0)` for non-negative constraints, allow negative `total_compound`

**Custom exception:**

- Add `MonthNotFoundError` to `backend/app/services/exceptions.py`
- Store `month_id` attribute for programmatic access
- Follow existing exception pattern with typed attributes

**Transaction aggregation:**

- Use conditional `func.sum()` with `filter()` in a single query for efficiency
- Income: SUM where `money_map_type == INCOME` and `amount > 0`
- Core: ABS(SUM) where `money_map_type == CORE` and `amount < 0`
- Choice: ABS(SUM) where `money_map_type == CHOICE` and `amount < 0`
- Use `func.coalesce(..., 0.0)` to handle NULL results

**Edge case handling:**

- Zero income: Return all percentages as 0.0, score as 0, label as "Poor"
- Negative compound (overspent): Calculate correctly as negative value, don't error
- No transactions: Return zeroed stats (handled by COALESCE in SQL)
- Month not found: Raise `MonthNotFoundError` with month_id

## Visual Design

No visual assets provided (backend service, no UI).

## Existing Code to Leverage

**ScoreLabel enum - `backend/app/db/enums.py`**

- What it does: Defines POOR, NEED_IMPROVEMENT, OKAY, GREAT labels
- How to reuse: Import directly, no changes needed
- Key exports: `ScoreLabel.POOR`, `ScoreLabel.GREAT`, etc.
- Found by: code-explorer analysis of db layer

**Month model - `backend/app/db/models/month.py`**

- What it does: Stores all required stat fields (total_income, core_percentage, score, score_label, etc.)
- How to reuse: Query by month_id, update fields directly, commit
- Key fields: `total_income`, `total_core`, `total_choice`, `total_compound`, percentages, `score`, `score_label`
- Found by: code-explorer analysis of db layer

**FrozenModel pattern - `backend/app/services/schemas.py`**

- What it does: Base class with `ConfigDict(frozen=True)` for immutable Pydantic models
- How to reuse: Inherit `MonthStats` from `FrozenModel`
- Key pattern: `class MonthStats(FrozenModel): ...`
- Found by: code-explorer analysis of schemas

**Categorizer service patterns - `backend/app/services/categorizer.py`**

- What it does: Shows service organization, NumPy docstrings, type annotations, logging
- How to reuse: Follow same docstring format, logging patterns, type annotation style
- Key patterns: Module-level logger, `ClassVar` for constants, `# ##>:` comments
- Found by: code-explorer analysis of categorizer service

**Exception pattern - `backend/app/services/exceptions.py`**

- What it does: Shows how to create custom exceptions with typed attributes
- How to reuse: Add `MonthNotFoundError` following same pattern
- Key pattern: Store context in attributes, provide human-readable message
- Found by: code-explorer analysis of categorizer service

## Architecture Approach

**Component Design:**

- Pure functions for stateless calculations (no class needed)
- Three public functions: `calculate_score`, `calculate_month_stats`, `calculate_and_update_month`
- One private helper: `_aggregate_transaction_totals`
- Constants for thresholds: `CORE_THRESHOLD = 50.0`, etc.

**Data Flow:**

1. `calculate_and_update_month(db, month_id)` - Entry point
2. Fetch Month record by ID (raise if not found)
3. `_aggregate_transaction_totals(db, month_id)` - Single SQL query
4. `calculate_month_stats(income, core, choice)` - Pure calculation
5. `calculate_score(core_pct, choice_pct, compound_pct)` - Nested call
6. Update Month record fields, commit, refresh, return

**Integration Points:**

- Import `ScoreLabel` from `app.db.enums`
- Import `Month`, `Transaction` from `app.db.models`
- Add `MonthStats` to `app.services.schemas`
- Add `MonthNotFoundError` to `app.services.exceptions`

## Out of Scope

- Trend analysis across multiple months
- Advice generation based on scores
- Historical comparisons or charts
- Transaction-level breakdowns by subcategory
- API endpoints (separate roadmap item #6)
- UI components (separate roadmap item #8)
- Automatic recalculation triggers (caller's responsibility)
- Caching of calculated results
- Batch processing of multiple months
- Score notifications or alerts
