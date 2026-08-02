"""Pydantic models for advice generation."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, model_validator

from app.db.models.emergency_fund_fact import EmergencyFundFactType
from app.repositories.commitment_fact import CommitmentFactType
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


class ActivePriorityContext(DecisionModel):
    """Declared priority available to generation.

    Attributes
    ----------
    goal : str
        Current objective.
    target : str
        Objective target.
    deadline : date | None
        Optional objective date.
    state : Literal["active", "corrected", "to_confirm", "session"]
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime | None
        Reuse cutoff; None for session.
    """

    goal: str = Field(min_length=1)
    target: str = Field(min_length=1)
    deadline: date | None = None
    state: Literal["active", "corrected", "to_confirm", "session"]
    last_confirmed_at: datetime
    valid_until: datetime | None


class EmergencyFundFactContext(DecisionModel):
    """Declared emergency-fund amount available to generation.

    Attributes
    ----------
    fact_type : EmergencyFundFactType
        Closed-catalog fact key.
    amount : float
        Declared euro amount.
    state : Literal["active", "corrected", "to_confirm", "session"]
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime | None
        Reuse cutoff; None for session.
    """

    fact_type: EmergencyFundFactType
    amount: float = Field(ge=0)
    state: Literal["active", "corrected", "to_confirm", "session"]
    last_confirmed_at: datetime
    valid_until: datetime | None


class CommitmentFactContext(DecisionModel):
    """Provide one obligation or debt fact to generation.

    Attributes
    ----------
    fact_id : int | None
        Stored id; None for session.
    fact_type : CommitmentFactType
        Closed-catalog type.
    label : str
        User-facing identifier.
    amount : float | None
        Obligation amount.
    frequency : str | None
        Recurrence.
    balance : float | None
        Debt balance.
    overdue_amount : float | None
        Known overdue amount.
    minimum_payment : float | None
        Contractual minimum.
    annual_rate : float | None
        Annual percentage rate.
    cost : float | None
        Known debt cost.
    due_date : date | None
        One-off deadline.
    end_date : date | None
        Explicit end.
    state : str
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime | None
        Reuse cutoff.
    """

    fact_id: int | None = None
    fact_type: CommitmentFactType
    label: str = Field(min_length=1)
    amount: float | None = Field(default=None, gt=0)
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"] | None = None
    balance: float | None = Field(default=None, ge=0)
    overdue_amount: float | None = Field(default=None, ge=0)
    minimum_payment: float | None = Field(default=None, gt=0)
    annual_rate: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    due_date: date | None = None
    end_date: date | None = None
    state: Literal["active", "corrected", "to_confirm", "session"]
    last_confirmed_at: datetime
    valid_until: datetime | None

    @model_validator(mode="after")
    def require_fact_fields(self) -> Self:
        """Reject incomplete fact variants.

        Returns
        -------
        Self
            Validated fact.

        Raises
        ------
        ValueError
            Required variant field is absent.
        """
        required = {
            "recurring_obligation": ("amount", "frequency"),
            "one_off_obligation": ("amount", "due_date"),
            "debt_position": ("balance",),
            "debt_terms": ("minimum_payment",),
        }[self.fact_type]
        if any(getattr(self, field) is None for field in required):
            raise ValueError(f"{self.fact_type} requires {', '.join(required)}")
        return self


class AdviceContext(DecisionModel):
    """Declared facts and remaining clarification budget.

    Attributes
    ----------
    active_priority : ActivePriorityContext | None
        Current declared objective.
    emergency_fund_facts : list[EmergencyFundFactContext]
        Emergency-fund context.
    commitment_facts : list[CommitmentFactContext]
        Obligation and debt context.
    clarifications_remaining : int
        Questions available before abstention.
    """

    active_priority: ActivePriorityContext | None = None
    emergency_fund_facts: list[EmergencyFundFactContext] = Field(default_factory=list)
    commitment_facts: list[CommitmentFactContext] = Field(default_factory=list)
    clarifications_remaining: int = Field(default=3, ge=0, le=3)


class EmergencyFundFactCitation(EmergencyFundFactContext):
    """Emergency-fund amount cited by decision.

    Attributes
    ----------
    state : Literal["active", "corrected", "session"]
        Active citation state.
    can_correct : Literal[True]
        Correction capability.
    can_delete : Literal[True]
        Deletion capability.
    """

    state: Literal["active", "corrected", "session"]
    can_correct: Literal[True]
    can_delete: Literal[True]


class ActivePriorityCitation(ActivePriorityContext):
    """Active priority cited by decision.

    Attributes
    ----------
    fact_type : Literal["active_priority"]
        Citation discriminator.
    state : Literal["active", "corrected", "session"]
        Active citation state.
    can_correct : Literal[True]
        Correction capability.
    can_delete : Literal[True]
        Deletion capability.
    """

    fact_type: Literal["active_priority"]
    state: Literal["active", "corrected", "session"]
    can_correct: Literal[True]
    can_delete: Literal[True]


class CommitmentFactCitation(CommitmentFactContext):
    """Expose an obligation or debt fact cited by a decision.

    Attributes
    ----------
    state : Literal["active", "corrected", "session"]
        Active citation state.
    can_correct : Literal[True]
        Correction capability.
    can_delete : Literal[True]
        Deletion capability.
    """

    state: Literal["active", "corrected", "session"]
    can_correct: Literal[True]
    can_delete: Literal[True]


DeclaredFactCitation = Annotated[
    ActivePriorityCitation | EmergencyFundFactCitation | CommitmentFactCitation,
    Field(discriminator="fact_type"),
]


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
    declared_facts: list[DeclaredFactCitation] = Field(default_factory=list)


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


class ClarificationOutput(DecisionModel):
    """Material question for one closed-catalog fact.

    Attributes
    ----------
    type : Literal["clarification"]
        Output discriminator.
    priority : Literal["high", "medium", "low"]
        Decision priority.
    subject : str
        Blocked subject.
    observation : str
        Certain observation.
    possible_effect : str
        Decision effect of the missing fact.
    question : str
        User-facing question.
    question_number : int
        One-based position in the capped flow.
    fact_type : Literal
        Requested closed-catalog fact.
    material_effects : list[str]
        Distinct possible decisions.
    """

    type: Literal["clarification"]
    priority: Literal["high", "medium", "low"]
    subject: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    possible_effect: str = Field(min_length=1)
    question: str = Field(min_length=1)
    question_number: int = Field(default=1, ge=1, le=3)
    fact_type: Literal[
        "active_priority",
        "liquid_reserve",
        "safety_floor",
        "priority_allocation",
        "recurring_obligation",
        "one_off_obligation",
        "debt_position",
        "debt_terms",
    ]
    material_effects: list[str] = Field(min_length=2)

    @model_validator(mode="after")
    def require_distinct_effects(self) -> Self:
        """Reject wording-only clarification.

        Returns
        -------
        Self
            Material clarification.

        Raises
        ------
        ValueError
            Fewer than two distinct effects.
        """
        if len(set(self.material_effects)) < 2:
            raise ValueError("clarification requires distinct decision effects")
        return self


DecisionOutput = Annotated[
    RecommendationOutput | NoActionOutput | UnresolvedOutput | ClarificationOutput,
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

    @model_validator(mode="after")
    def allow_one_clarification(self) -> Self:
        """Enforce progressive single-card flow.

        Returns
        -------
        Self
            Advice with zero or one clarification.

        Raises
        ------
        ValueError
            Multiple clarification cards.
        """
        if sum(output.type == "clarification" for output in self.outputs) > 1:
            raise ValueError("advice allows one clarification at a time")
        return self
