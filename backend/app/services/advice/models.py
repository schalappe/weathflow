"""Pydantic models for advice generation."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, model_validator

from app.services.models import FrozenModel


class TransactionSample(FrozenModel):
    """Observed transaction.

    Attributes
    ----------
    description : str
        Transaction label.
    amount : float
        Absolute amount.
    subcategory : str | None
        Money Map subcategory.
    """

    description: str
    amount: float
    subcategory: str | None = None


class MonthData(FrozenModel):
    """Observed monthly generation input.

    Attributes
    ----------
    year : int
        Calendar year.
    month : int
        Calendar month.
    total_income : float
        Observed income.
    total_core : float
        Core spending.
    total_choice : float
        Choice spending.
    total_compound : float
        Compound amount.
    core_percentage : float
        Core income share.
    choice_percentage : float
        Choice income share.
    compound_percentage : float
        Compound income share.
    score : int
        Money Map score.
    score_label : str | None
        Score label.
    category_breakdown : dict[str, float] | None
        Optional subcategory totals.
    transactions : dict[str, list[TransactionSample]] | None
        Transactions grouped by category.
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


class DecisionModel(FrozenModel):
    """Strict decision model.

    Notes
    -----
    Unknown fields fail validation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


class ObservedFact(DecisionModel):
    """Fact calculated from imported transactions.

    Attributes
    ----------
    fact : str
        Observed statement.
    period : str
        Observation window.
    scope : str
        Covered transactions or category.
    source : Literal["observed_data"]
        Fixed provenance marker.
    """

    fact: str = Field(min_length=1)
    period: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    source: Literal["observed_data"]


class DecisionTraceDetails(DecisionModel):
    """Auditable decision detail.

    Attributes
    ----------
    observations : list[ObservedFact]
        Source facts.
    calculations : list[str]
        Reproducible derivations.
    conventions : list[str]
        Contestable rules.
    limits : list[str]
        Data limits.
    """

    observations: list[ObservedFact] = Field(min_length=1)
    calculations: list[str] = Field(default_factory=list)
    conventions: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)


class DecisionTrace(DecisionModel):
    """Two-level decision trace.

    Attributes
    ----------
    summary : str
        Visible explanation.
    details : DecisionTraceDetails
        Auditable evidence.
    """

    summary: str = Field(min_length=1)
    details: DecisionTraceDetails


class RecommendationOutput(DecisionModel):
    """Action supported by observed facts.

    Attributes
    ----------
    type : Literal["recommendation"]
        Output discriminator.
    priority : Literal["high", "medium", "low"]
        Decision priority.
    action : str
        Supported action.
    amount : float | None
        Derived amount only.
    deadline : date | None
        Derived deadline only.
    trace : DecisionTrace
        Supporting decision trace.
    """

    type: Literal["recommendation"]
    priority: Literal["high", "medium", "low"]
    action: str = Field(min_length=1)
    amount: float | None = Field(default=None, gt=0, exclude_if=lambda value: value is None)
    deadline: date | None = Field(default=None, exclude_if=lambda value: value is None)
    trace: DecisionTrace

    @model_validator(mode="after")
    def require_derived_optional_values(self) -> Self:
        """Validate optional decision values.

        Returns
        -------
        Self
            Valid recommendation.

        Raises
        ------
        ValueError
            Amount or deadline lacks calculation.
        """
        if (self.amount is not None or self.deadline is not None) and not self.trace.details.calculations:
            raise ValueError("amount and deadline require a supporting calculation")
        return self


class NoActionOutput(DecisionModel):
    """Conclusion that observed facts justify no action.

    Attributes
    ----------
    type : Literal["no_action"]
        Output discriminator.
    priority : Literal["high", "medium", "low"]
        Decision priority.
    conclusion : str
        No-action conclusion.
    trace : DecisionTrace
        Supporting decision trace.
    """

    type: Literal["no_action"]
    priority: Literal["high", "medium", "low"]
    conclusion: str = Field(min_length=1)
    trace: DecisionTrace


class UnresolvedOutput(DecisionModel):
    """Subject that observed facts cannot resolve.

    Attributes
    ----------
    type : Literal["unresolved"]
        Output discriminator.
    priority : Literal["high", "medium", "low"]
        Decision priority.
    conclusion : str
        Unresolved subject.
    trace : DecisionTrace
        Supporting decision trace.
    """

    type: Literal["unresolved"]
    priority: Literal["high", "medium", "low"]
    conclusion: str = Field(min_length=1)
    trace: DecisionTrace


DecisionOutput = Annotated[
    RecommendationOutput | NoActionOutput | UnresolvedOutput,
    Field(discriminator="type"),
]


class AdviceResponse(DecisionModel):
    """Monthly decision contract.

    Attributes
    ----------
    outputs : list[DecisionOutput]
        One or more outputs. No type quota.
    """

    outputs: list[DecisionOutput] = Field(min_length=1)
