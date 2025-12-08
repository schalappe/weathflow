"""Domain enums for Money Map Manager."""

from enum import Enum


class MoneyMapType(str, Enum):
    """
    Budget category types for the Money Map (50/30/20) framework.

    Categories:
        INCOME: Revenue such as salary.
        CORE: Necessities (target ≤ 50% of income).
        CHOICE: Wants/discretionary spending (target ≤ 30% of income).
        COMPOUND: Savings/investments (target ≥ 20% of income).
        EXCLUDED: Internal transfers not counted in budget calculations.
    """

    INCOME = "INCOME"
    CORE = "CORE"
    CHOICE = "CHOICE"
    COMPOUND = "COMPOUND"
    EXCLUDED = "EXCLUDED"


class ScoreLabel(str, Enum):
    """
    Human-readable labels for Money Map scores.

    The score (0-3) indicates how many of the three budget thresholds are met:
        POOR (0): No thresholds met.
        NEED_IMPROVEMENT (1): One threshold met.
        OKAY (2): Two thresholds met.
        GREAT (3): All three thresholds met.
    """

    POOR = "Poor"
    NEED_IMPROVEMENT = "Need Improvement"
    OKAY = "Okay"
    GREAT = "Great"


SCORE_TO_LABEL: dict[int, ScoreLabel] = {
    0: ScoreLabel.POOR,
    1: ScoreLabel.NEED_IMPROVEMENT,
    2: ScoreLabel.OKAY,
    3: ScoreLabel.GREAT,
}
