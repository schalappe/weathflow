"""Pydantic models for score calculation operations."""

from pydantic import Field, model_validator

from app.db.enums import SCORE_TO_LABEL, ScoreLabel
from app.services.models import FrozenModel


class MonthStats(FrozenModel):
    """
    Complete statistics for a month's budget health.

    Contains aggregated totals, calculated percentages, and the Money Map score
    based on the 50/30/20 framework thresholds.

    Attributes
    ----------
    total_income : float
        Sum of all income transactions.
    total_core : float
        Sum of core expenses (absolute value).
    total_choice : float
        Sum of choice expenses (absolute value).
    total_compound : float
        Derived: income - core - choice (can be negative if overspent).
    core_percentage : float
        Core spending as percentage of income (rounded to 1 decimal).
    choice_percentage : float
        Choice spending as percentage of income (rounded to 1 decimal).
    compound_percentage : float
        Compound (savings) as percentage of income (rounded to 1 decimal).
    score : int
        Money Map score (0-3) based on thresholds met.
    score_label : ScoreLabel
        Human-readable label for the score.
    """

    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int = Field(ge=0, le=3)
    score_label: ScoreLabel

    @model_validator(mode="after")
    def validate_score_label_consistency(self) -> "MonthStats":
        """Ensure score and score_label match."""
        expected_label = SCORE_TO_LABEL[self.score]
        if self.score_label != expected_label:
            raise ValueError(f"score_label {self.score_label.value} does not match score {self.score}")
        return self
