"""Pydantic models for advice generation operations."""

from pydantic import Field

from app.services.models import FrozenModel


class TransactionSample(FrozenModel):
    """
    A sample transaction for context in advice generation.

    Provides Claude with specific transaction details to generate
    actionable, personalized recommendations.

    Attributes
    ----------
    description : str
        Merchant or transaction description (e.g., "Netflix", "Uber Eats").
    amount : float
        Transaction amount (absolute value).
    subcategory : str | None
        Money Map subcategory if assigned.
    """

    description: str
    amount: float
    subcategory: str | None = None


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
    transactions : dict[str, list[TransactionSample]] | None
        All transactions per category for pattern analysis.
        Keys are category types ('CORE', 'CHOICE', 'COMPOUND').
    past_advice : list[str] | None
        Previous recommendations given for this month to track follow-through.
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
    transactions: dict[str, list[TransactionSample]] | None = None
    past_advice: list[str] | None = None


class SpendingPattern(FrozenModel):
    """
    A recurring spending pattern identified in transaction data.

    Attributes
    ----------
    pattern_type : str
        Type of pattern (e.g., 'Abonnements récurrents', 'Livraisons repas').
    description : str
        Detailed description of the pattern with merchants/services.
    monthly_cost : float
        Total monthly cost of this pattern.
    occurrences : int
        Number of times this pattern occurs per month.
    insight : str
        Analysis of what this pattern reveals about financial habits.
    """

    pattern_type: str
    description: str
    monthly_cost: float
    occurrences: int
    insight: str


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
    root_cause : str | None
        Explanation of the underlying cause of the problem.
    impact : str | None
        Impact on achieving Money Map objectives.
    """

    category: str
    amount: float
    trend: str
    root_cause: str | None = None
    impact: str | None = None


class Recommendation(FrozenModel):
    """
    A prioritized actionable recommendation.

    Attributes
    ----------
    priority : int
        Priority ranking (1 = highest priority).
    action : str
        Main action to undertake.
    details : str
        Full explanation with context and specific transactions.
    expected_savings : str
        Estimated savings (monthly and annual).
    difficulty : str
        Difficulty level (Facile / Modéré / Exigeant).
    quick_win : bool
        Whether this is a quick win that can be implemented immediately.
    """

    priority: int = Field(ge=1, le=3)
    action: str
    details: str
    expected_savings: str
    difficulty: str
    quick_win: bool = False


class ProgressReview(FrozenModel):
    """
    Review of progress on previous advice.

    Attributes
    ----------
    previous_advice_followed : str
        Evaluation of how well previous advice was followed.
    wins : list[str]
        List of victories and progress to celebrate.
    areas_for_growth : list[str]
        Areas that still need work.
    """

    previous_advice_followed: str
    wins: list[str] = Field(default_factory=list)
    areas_for_growth: list[str] = Field(default_factory=list)


class MonthlyGoal(FrozenModel):
    """
    A specific measurable goal for the next month.

    Attributes
    ----------
    objective : str
        Precise and measurable objective.
    target_amount : float
        Target amount to save or reduce.
    strategy : str
        Concrete strategy to achieve the objective.
    """

    objective: str
    target_amount: float
    strategy: str


class AdviceResponse(FrozenModel):
    """
    Complete advice response from Claude API.

    Contains comprehensive analysis, spending patterns, problem areas,
    actionable recommendations, progress review, and encouragement.

    Attributes
    ----------
    analysis : str
        4-6 sentence in-depth analysis of financial trends.
    spending_patterns : list[SpendingPattern]
        Top 3 spending patterns identified.
    problem_areas : list[ProblemArea]
        Top 3 spending categories requiring attention with root cause analysis.
    recommendations : list[Recommendation]
        3 prioritized actionable recommendations.
    progress_review : ProgressReview
        Review of progress on previous advice.
    monthly_goal : MonthlyGoal
        Specific goal for the next month.
    encouragement : str
        Personalized 3-4 sentence encouragement message.
    """

    analysis: str
    spending_patterns: list[SpendingPattern] = Field(default_factory=list)
    problem_areas: list[ProblemArea]
    recommendations: list[Recommendation] = Field(default_factory=list)
    progress_review: ProgressReview | None = None
    monthly_goal: MonthlyGoal | None = None
    encouragement: str
