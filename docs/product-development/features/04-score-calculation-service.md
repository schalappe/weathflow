# Score Calculation Service

## Overview

Create a service that calculates Money Map percentages and scores (0-3) based on categorized transactions and the 50/30/20 thresholds.

**Size**: S (Small)
**Dependencies**: Requires completed Transaction Categorization Service (#3)

---

## Objective

Calculate monthly budget health using the Money Map framework:

| Category   | Target | Description                   |
| ---------- | ------ | ----------------------------- |
| `CORE`     | ≤ 50%  | Necessities (housing, food)   |
| `CHOICE`   | ≤ 30%  | Wants (dining, entertainment) |
| `COMPOUND` | ≥ 20%  | Savings and investments       |

---

## Formulas

### Step 1: Aggregate Totals

```text
Total Income   = Σ transactions WHERE money_map_type = 'INCOME' AND amount > 0
Total Core     = |Σ transactions WHERE money_map_type = 'CORE' AND amount < 0|
Total Choice   = |Σ transactions WHERE money_map_type = 'CHOICE' AND amount < 0|
Total Compound = Total Income - Total Core - Total Choice
```

### Step 2: Calculate Percentages

```text
Core %     = (Total Core / Total Income) × 100
Choice %   = (Total Choice / Total Income) × 100
Compound % = (Total Compound / Total Income) × 100
```

### Step 3: Calculate Score (0-3)

| Condition      | Points |
| -------------- | ------ |
| Core ≤ 50%     | +1     |
| Choice ≤ 30%   | +1     |
| Compound ≥ 20% | +1     |

### Step 4: Assign Label

| Score | Label            |
| ----- | ---------------- |
| 3     | Great            |
| 2     | Okay             |
| 1     | Need Improvement |
| 0     | Poor             |

---

## Service Interface

### Input

The service receives a `month_id` and retrieves categorized transactions from the database.

### Output

```python
from pydantic import BaseModel

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

---

## Implementation

### Location

`backend/app/services/calculator.py`

### Public Functions

```python
def calculate_score(
    core_pct: float,
    choice_pct: float,
    compound_pct: float
) -> tuple[int, ScoreLabel]:
    """
    Calculate Money Map score based on percentages.

    Parameters
    ----------
    core_pct : float
        Core spending as percentage of income.
    choice_pct : float
        Choice spending as percentage of income.
    compound_pct : float
        Compound (savings) as percentage of income.

    Returns
    -------
    tuple[int, ScoreLabel]
        Score (0-3) and corresponding label.
    """

def calculate_month_stats(
    income: float,
    core: float,
    choice: float
) -> MonthStats:
    """
    Calculate all statistics for a month.

    Parameters
    ----------
    income : float
        Total income for the month.
    core : float
        Total core spending (absolute value).
    choice : float
        Total choice spending (absolute value).

    Returns
    -------
    MonthStats
        Complete statistics including percentages and score.
    """

async def calculate_and_update_month(
    db: Session,
    month_id: int
) -> Month:
    """
    Recalculate stats for a month and persist to database.

    Parameters
    ----------
    db : Session
        Database session.
    month_id : int
        ID of the month to recalculate.

    Returns
    -------
    Month
        Updated month record with new statistics.
    """
```

### ScoreLabel Enum

```python
class ScoreLabel(str, Enum):
    GREAT = "Great"
    OKAY = "Okay"
    NEED_IMPROVEMENT = "Need Improvement"
    POOR = "Poor"
```

---

## Database Integration

### Months Table Fields (to update)

| Field                 | Type    | Description                        |
| --------------------- | ------- | ---------------------------------- |
| `total_income`        | REAL    | Sum of income transactions         |
| `total_core`          | REAL    | Sum of core expenses (abs)         |
| `total_choice`        | REAL    | Sum of choice expenses (abs)       |
| `total_compound`      | REAL    | Calculated: income - core - choice |
| `core_percentage`     | REAL    | Percentage rounded to 1 decimal    |
| `choice_percentage`   | REAL    | Percentage rounded to 1 decimal    |
| `compound_percentage` | REAL    | Percentage rounded to 1 decimal    |
| `score`               | INTEGER | 0-3                                |
| `score_label`         | TEXT    | Human-readable label               |

---

## Edge Cases

| Scenario               | Handling                             |
| ---------------------- | ------------------------------------ |
| Zero income            | All percentages = 0, score = 0       |
| Negative compound      | Compound can be negative (overspent) |
| No transactions        | Return zeroed stats                  |
| Missing categorization | Skip EXCLUDED, handle missing types  |

---

## Usage Context

This service is called:

1. **After categorization** - When transactions are imported and categorized
2. **After manual correction** - When user edits a transaction's category
3. **On month data retrieval** - To ensure stats are current (optional recalc)

---

## Acceptance Criteria

- [ ] `calculate_score` correctly assigns points for each threshold
- [ ] `calculate_month_stats` returns accurate percentages rounded to 1 decimal
- [ ] `calculate_and_update_month` persists results to the database
- [ ] Edge case: Zero income returns score 0 with label "Poor"
- [ ] Edge case: Negative compound (overspent) is calculated correctly
- [ ] All functions have complete type annotations
- [ ] Unit tests cover happy path, edge cases, and boundary conditions

---

## Test Cases

### Unit Tests

```python
# Happy path - Perfect score
def test_calculate_score_perfect():
    score, label = calculate_score(45.0, 25.0, 30.0)
    assert score == 3
    assert label == ScoreLabel.GREAT

# Boundary - Exactly at thresholds
def test_calculate_score_at_thresholds():
    score, label = calculate_score(50.0, 30.0, 20.0)
    assert score == 3

# Over threshold - Core exceeds 50%
def test_calculate_score_core_over():
    score, label = calculate_score(55.0, 25.0, 20.0)
    assert score == 2

# Zero income
def test_calculate_month_stats_zero_income():
    stats = calculate_month_stats(0, 0, 0)
    assert stats.score == 0
    assert stats.score_label == "Poor"

# Overspending (negative compound)
def test_calculate_month_stats_overspent():
    stats = calculate_month_stats(1000, 600, 500)
    assert stats.total_compound == -100
    assert stats.compound_percentage == -10.0
```

### Integration Tests

```python
# Recalculation after transaction update
async def test_recalculate_after_update(db, sample_month):
    # Update transaction category
    # Call calculate_and_update_month
    # Verify new stats persisted
```

---

## Notes

- Percentages are always calculated from income (not total expenses)
- Compound is derived, not summed from transactions directly
- The service is stateless - all state lives in the database
