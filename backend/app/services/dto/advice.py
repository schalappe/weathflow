"""Pydantic models for advice generation operations."""

from pydantic import Field

from app.services.dto._base import FrozenModel


class MonthData(FrozenModel):
    """
    Monthly financial data to be analyzed for advice generation.

    This model represents a single month's financial summary including
    totals, percentages, and category breakdowns.

    Attributes
    ----------
    year : int
        Year of the month (2000-2100).
    month : int
        Month number (1-12).
    total_income : float
        Total income for the month.
    total_core : float
        Total core (necessities) spending.
    total_choice : float
        Total choice (discretionary) spending.
    total_compound : float
        Total compound (savings/investments).
    core_percentage : float
        Core spending as percentage of income.
    choice_percentage : float
        Choice spending as percentage of income.
    compound_percentage : float
        Compound as percentage of income.
    score : int
        Money Map score (0-3).
    score_label : str | None
        Human-readable score label.
    category_breakdown : dict[str, float] | None
        Optional breakdown by subcategory (e.g., {'Subscriptions': 85.0}).
    """

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int = Field(ge=0, le=3)
    score_label: str | None = None
    category_breakdown: dict[str, float] | None = None


class ProblemArea(FrozenModel):
    """
    A spending category identified as a problem area.

    Represents a category where spending is increasing or exceeding targets,
    requiring the user's attention.

    Attributes
    ----------
    category : str
        Name of the spending category.
    amount : float
        Amount spent in this category.
    trend : str
        Trend indicator (e.g., '+20%', '-5%', 'N/A').
    """

    category: str
    amount: float
    trend: str


class AdviceResponse(FrozenModel):
    """
    Complete advice response from Claude API.

    Contains analysis, identified problem areas, actionable recommendations,
    and an encouragement message for the user.

    Attributes
    ----------
    analysis : str
        2-3 sentence trend analysis of the user's finances.
    problem_areas : list[ProblemArea]
        Top 3 spending categories requiring attention.
    recommendations : list[str]
        3 actionable improvement suggestions.
    encouragement : str
        Personalized encouragement message.
    """

    analysis: str
    problem_areas: list[ProblemArea]
    recommendations: list[str]
    encouragement: str
