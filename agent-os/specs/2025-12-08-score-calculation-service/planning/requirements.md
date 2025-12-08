# Spec Requirements: Score Calculation Service

## Initial Description

Create a service that calculates Money Map percentages and scores (0-3) based on categorized transactions and the 50/30/20 thresholds.

## Requirements Discussion

### Source Document

All requirements are defined in the existing specification:
`docs/product-development/features/04-score-calculation-service.md`

### Key Requirements Confirmed

**Q1:** How should percentages be calculated?
**Answer:** Percentages are calculated from **Total Income** (not total spending):

- Core % = (Total Core / Total Income) x 100
- Choice % = (Total Choice / Total Income) x 100
- Compound % = (Total Compound / Total Income) x 100

**Q2:** What is the scoring logic?
**Answer:** Score (0-3) based on:

- +1 point if Core <= 50%
- +1 point if Choice <= 30%
- +1 point if Compound >= 20%

**Q3:** How is Compound calculated?
**Answer:** Compound is **derived**, not summed from transactions:
`Total Compound = Total Income - Total Core - Total Choice`

**Q4:** What labels map to scores?
**Answer:**

- 3 = Great
- 2 = Okay
- 1 = Need Improvement
- 0 = Poor

**Q5:** Should the service persist to database?
**Answer:** Yes. The service includes `calculate_and_update_month()` which persists results to the months table.

### Existing Code to Reference

**Similar Features Identified:**

- Enums: `backend/app/db/enums.py` - Contains `MoneyMapType` and `ScoreLabel` (already exists!)
- Schemas: `backend/app/services/schemas.py` - Uses `FrozenModel` pattern for immutable Pydantic models
- Services: `backend/app/services/categorizer.py` - Similar service structure pattern
- Database: `backend/app/db/database.py` - Database session patterns

### Visual Assets

**Files Provided:**
No visual assets provided (backend service, no UI).

## Requirements Summary

### Functional Requirements

1. Calculate totals for Income, Core, Choice from categorized transactions
2. Derive Compound as: Income - Core - Choice
3. Calculate percentages relative to Income (rounded to 1 decimal)
4. Calculate score (0-3) based on 50/30/20 thresholds
5. Assign human-readable label (Great/Okay/Need Improvement/Poor)
6. Persist calculated stats to the months table

### Service Interface

Three public functions:

1. `calculate_score(core_pct, choice_pct, compound_pct)` - Pure calculation
2. `calculate_month_stats(income, core, choice)` - Pure calculation returning MonthStats
3. `calculate_and_update_month(db, month_id)` - Database integration

### Output Schema

```python
class MonthStats(BaseModel):
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float      # Rounded to 1 decimal
    choice_percentage: float    # Rounded to 1 decimal
    compound_percentage: float  # Rounded to 1 decimal
    score: int                  # 0-3
    score_label: str            # "Great" | "Okay" | "Need Improvement" | "Poor"
```

### Scope Boundaries

**In Scope:**

- Pure calculation functions for percentages and scores
- MonthStats Pydantic model for output
- Database update function for months table
- Edge case handling (zero income, negative compound, no transactions)

**Out of Scope:**

- Trend analysis across months
- Advice generation
- Historical comparisons
- Transaction-level breakdowns by subcategory

### Technical Considerations

- File location: `backend/app/services/calculator.py`
- Reuse existing `ScoreLabel` enum from `backend/app/db/enums.py`
- Follow `FrozenModel` pattern from `backend/app/services/schemas.py`
- Percentages rounded to 1 decimal place
- Compound can be negative (overspending scenario)

### Edge Cases

| Scenario               | Handling                                       |
| ---------------------- | ---------------------------------------------- |
| Zero income            | All percentages = 0, score = 0, label = "Poor" |
| Negative compound      | Allowed (overspent month)                      |
| No transactions        | Return zeroed stats                            |
| Missing categorization | Skip EXCLUDED transactions                     |

### Acceptance Criteria

- [ ] `calculate_score` correctly assigns points for each threshold
- [ ] `calculate_month_stats` returns accurate percentages rounded to 1 decimal
- [ ] `calculate_and_update_month` persists results to the database
- [ ] Edge case: Zero income returns score 0 with label "Poor"
- [ ] Edge case: Negative compound (overspent) is calculated correctly
- [ ] All functions have complete type annotations
- [ ] Unit tests cover happy path, edge cases, and boundary conditions
