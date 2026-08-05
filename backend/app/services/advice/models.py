"""Pydantic models for advice generation."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, model_validator

from app.db.models.emergency_fund_fact import EmergencyFundFactType
from app.repositories.commitment_fact import CommitmentFactType
from app.repositories.income_fact import IncomeFactType
from app.services.models import FrozenModel

ClarificationFactType = Literal[
    "period_coverage",
    "transaction_nature",
    "active_priority",
    "liquid_reserve",
    "safety_floor",
    "priority_allocation",
    "recurring_obligation",
    "one_off_obligation",
    "debt_position",
    "debt_terms",
    "usual_disposable_income",
    "expected_one_off_income",
    "financial_limit",
    "action_unavailability",
]
DecisionLever = Literal["action_or_priority", "amount", "deadline", "abstention"]
AnswerEase = Literal["easy", "moderate", "hard"]


class TransactionSample(FrozenModel):
    """Observed transaction.

    Attributes
    ----------
    description : str
        Transaction label.
    transaction_id : int
        Stable observed identifier.
    amount : float
        Absolute amount.
    account : str | None
        Source account.
    subcategory : str | None
        Money Map subcategory.
    date : date
        Booking date.
    """

    transaction_id: int
    description: str
    amount: float
    date: date
    account: str | None = None
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
    evidence_type: Literal["presence", "absence", "aggregate", "comparison"]
    source_months: list[str] = Field(min_length=1)
    transaction_ids: list[int] = Field(default_factory=list)


class PeriodCoverageContext(DecisionModel):
    """Exact analyzed-window coverage.

    Attributes
    ----------
    coverage_months : list[str]
        Exact covered months.
    complete : bool
        Complete and gap-free marker.
    state : Literal["active", "corrected", "to_confirm"]
        Confirmation lifecycle.
    """

    coverage_months: list[str] = Field(min_length=1)
    accounts: list[str] = Field(default_factory=list)
    complete: bool
    missing_elements: list[str] = Field(default_factory=list)
    state: Literal["active", "corrected", "to_confirm"]
    last_confirmed_at: datetime
    valid_until: None = None
    provenance_issues: list[str] = Field(default_factory=list)


class PeriodCoverageSignal(DecisionModel):
    """Admitted provenance limit in analyzed window.

    Attributes
    ----------
    coverage_months : list[str]
        Affected months.
    provenance_issues : list[str]
        Admitted source limits.
    """

    coverage_months: list[str] = Field(min_length=1)
    provenance_issues: list[str] = Field(min_length=1)
    details: list[str] = Field(default_factory=list)


TransactionNature = Literal[
    "income",
    "reimbursement",
    "transfer",
    "expense",
    "debt_payment",
    "saving",
]


class TransactionNatureContext(DecisionModel):
    """Confirmed meaning for explicit historical occurrences.

    Attributes
    ----------
    transaction_ids : list[int]
        Explicitly confirmed occurrences.
    source_months : list[str]
        Months containing those occurrences.
    nature : TransactionNature
        Confirmed financial nature.
    scope : Literal["occurrence", "series"]
        Narrow confirmation scope.
    """

    fact_id: int
    transaction_ids: list[int] = Field(min_length=1)
    source_months: list[str] = Field(min_length=1)
    nature: TransactionNature
    scope: Literal["occurrence", "series"]
    state: Literal["active", "corrected", "to_confirm"]
    last_confirmed_at: datetime
    valid_until: None = None


class TransactionNatureSignal(DecisionModel):
    """New structural link affecting transaction meaning.

    Attributes
    ----------
    signal_type : Literal
        Structural contradiction kind.
    transaction_ids : list[int]
        Confirmed transactions affected.
    linked_transaction_ids : list[int]
        Newly linked transactions.
    """

    signal_type: Literal[
        "counter_entry",
        "paired_transfer",
        "cancellation",
        "linked_reimbursement",
        "source_correction",
    ]
    transaction_ids: list[int] = Field(min_length=1)
    linked_transaction_ids: list[int] = Field(min_length=1)
    fact_id: int | None = None


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


class IncomeFactContext(DecisionModel):
    """Declared income available to generation."""

    fact_type: IncomeFactType
    label: str | None = Field(default=None, min_length=1, max_length=200)
    amount: float = Field(gt=0, allow_inf_nan=False)
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"] | None = None
    expected_date: date | None = None
    matched_transaction: bool = False
    state: Literal["active", "corrected", "to_confirm", "session"]
    last_confirmed_at: datetime
    valid_until: datetime | None

    @model_validator(mode="after")
    def require_variant_fields(self) -> Self:
        """Reject incomplete income variants.

        Returns
        -------
        Self
            Validated fact.

        Raises
        ------
        ValueError
            Variant-specific field is absent.
        """
        if self.fact_type == "usual_disposable_income" and self.frequency is None:
            raise ValueError("usual_disposable_income requires frequency")
        if self.fact_type == "expected_one_off_income" and self.expected_date is None:
            raise ValueError("expected_one_off_income requires expected_date")
        return self


class FinancialLimitContext(DecisionModel):
    """Scoped declared amount boundary.

    Attributes
    ----------
    fact_id : int | None
        Stored identifier.
    fact_type : Literal["financial_limit"]
        Discriminator.
    scope_type : Literal["expense", "action"]
        Scope kind.
    scope : str
        Exact scope.
    limit_type : Literal["floor", "cap", "sustainable_amount"]
        Boundary kind.
    amount : float
        Boundary amount.
    state : Literal["active", "corrected", "to_confirm", "session"]
        Lifecycle state.
    last_confirmed_at : datetime
        Last declaration timestamp.
    valid_until : datetime | None
        Freshness cutoff.
    """

    fact_id: int | None = None
    fact_type: Literal["financial_limit"]
    scope_type: Literal["expense", "action"]
    scope: str = Field(min_length=1)
    limit_type: Literal["floor", "cap", "sustainable_amount"]
    amount: float = Field(gt=0)
    state: Literal["active", "corrected", "to_confirm", "session"]
    last_confirmed_at: datetime
    valid_until: datetime | None


class ActionUnavailabilityContext(DecisionModel):
    """Action unavailable until explicit review date.

    Attributes
    ----------
    fact_id : int | None
        Stored identifier.
    fact_type : Literal["action_unavailability"]
        Discriminator.
    action : str
        Exact unavailable action.
    review_date : date
        Review date.
    state : Literal["active", "corrected", "to_confirm", "session"]
        Lifecycle state.
    last_confirmed_at : datetime
        Last declaration timestamp.
    valid_until : datetime | None
        Freshness cutoff.
    """

    fact_id: int | None = None
    fact_type: Literal["action_unavailability"]
    action: str = Field(min_length=1)
    review_date: date
    state: Literal["active", "corrected", "to_confirm", "session"]
    last_confirmed_at: datetime
    valid_until: datetime | None


ConstraintFactContext = Annotated[
    FinancialLimitContext | ActionUnavailabilityContext,
    Field(discriminator="fact_type"),
]


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
    income_facts : list[IncomeFactContext]
        Declared income context.
    constraint_facts : list[ConstraintFactContext]
        Financial limits and unavailable actions.
    asked_fact_types : list[ClarificationFactType]
        Facts already consumed in current request.
    clarifications_remaining : int
        Questions available before abstention.
    """

    active_priority: ActivePriorityContext | None = None
    period_coverages: list[PeriodCoverageContext] = Field(default_factory=list)
    coverage_signals: list[PeriodCoverageSignal] = Field(default_factory=list)
    transaction_natures: list[TransactionNatureContext] = Field(default_factory=list)
    transaction_nature_signals: list[TransactionNatureSignal] = Field(default_factory=list)
    emergency_fund_facts: list[EmergencyFundFactContext] = Field(default_factory=list)
    commitment_facts: list[CommitmentFactContext] = Field(default_factory=list)
    income_facts: list[IncomeFactContext] = Field(default_factory=list)
    constraint_facts: list[ConstraintFactContext] = Field(default_factory=list)
    asked_fact_types: list[ClarificationFactType] = Field(default_factory=list, max_length=3)
    clarifications_remaining: int = Field(default=3, ge=0, le=3)


class PeriodCoverageCitation(PeriodCoverageContext):
    """Coverage fact cited by decision.

    Attributes
    ----------
    fact_type : Literal["period_coverage"]
        Closed-catalog discriminator.
    can_correct : Literal[True]
        Correction capability.
    can_delete : Literal[True]
        Deletion capability.
    """

    fact_type: Literal["period_coverage"]
    state: Literal["active", "corrected"]
    can_correct: Literal[True]
    can_delete: Literal[True]


class TransactionNatureCitation(TransactionNatureContext):
    """Transaction meaning cited by decision.

    Attributes
    ----------
    fact_type : Literal["transaction_nature"]
        Closed-catalog discriminator.
    can_correct : Literal[True]
        Correction capability.
    can_delete : Literal[True]
        Deletion capability.
    """

    fact_type: Literal["transaction_nature"]
    state: Literal["active", "corrected"]
    can_correct: Literal[True]
    can_delete: Literal[True]


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


class IncomeFactCitation(IncomeFactContext):
    """Income fact cited by decision."""

    state: Literal["active", "corrected", "session"]
    can_correct: Literal[True]
    can_delete: Literal[True]


class FinancialLimitCitation(FinancialLimitContext):
    """Financial limit cited by decision.

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


class ActionUnavailabilityCitation(ActionUnavailabilityContext):
    """Unavailable action cited by decision.

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
    ActivePriorityCitation
    | PeriodCoverageCitation
    | TransactionNatureCitation
    | EmergencyFundFactCitation
    | CommitmentFactCitation
    | IncomeFactCitation
    | FinancialLimitCitation
    | ActionUnavailabilityCitation,
    Field(discriminator="fact_type"),
]


class IncomeNormalization(DecisionModel):
    """Structured income conversion used by a decision.

    Attributes
    ----------
    fact_type : IncomeFactType
        Declared source key.
    source_amount : float
        Declared amount before conversion.
    source_frequency : Literal | None
        Declared recurrence, absent for one-off income.
    period : str
        Applicable month or exact expected date.
    conversion : Literal
        Canonical conversion rule.
    normalized_amount : float
        Amount after conversion.
    """

    fact_type: IncomeFactType
    source_amount: float = Field(gt=0, allow_inf_nan=False)
    source_frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"] | None = None
    period: str = Field(pattern=r"^\d{4}-\d{2}(?:-\d{2})?$")
    conversion: Literal[
        "weekly_x_52_div_12",
        "biweekly_x_26_div_12",
        "monthly",
        "quarterly_div_3",
        "yearly_div_12",
        "one_off",
    ]
    normalized_amount: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def require_variant_fields(self) -> Self:
        """Reject mismatched source and conversion variants.

        Returns
        -------
        Self
            Valid normalization.

        Raises
        ------
        ValueError
            Source variant and conversion disagree.
        """
        if self.fact_type == "expected_one_off_income":
            if self.source_frequency is not None or self.conversion != "one_off" or len(self.period) != 10:
                raise ValueError("expected income requires one-off dated normalization")
            return self
        if self.source_frequency is None:
            raise ValueError("habitual income requires a source frequency")
        expected_conversion = {
            "weekly": "weekly_x_52_div_12",
            "biweekly": "biweekly_x_26_div_12",
            "monthly": "monthly",
            "quarterly": "quarterly_div_3",
            "yearly": "yearly_div_12",
        }[self.source_frequency]
        if self.conversion != expected_conversion or len(self.period) != 7:
            raise ValueError("habitual income requires matching monthly normalization")
        return self


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
    income_normalizations : list[IncomeNormalization]
        Structured income conversions.
    limits : list[str]
        Data limits.
    """

    observations: list[ObservedFact] = Field(min_length=1)
    calculations: list[str] = Field(default_factory=list)
    conventions: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    income_normalizations: list[IncomeNormalization] = Field(default_factory=list)
    declared_facts: list[DeclaredFactCitation] = Field(default_factory=list)
    transitions: list[str] = Field(default_factory=list)


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
    subject : str | None
        Exact decision scope when constraints are available.
    action : str
        Supported action.
    income_dependent : bool
        Whether amount or deadline derives from income.
    amount : float | None
        Derived amount only.
    deadline : date | None
        Derived deadline only.
    trace : DecisionTrace
        Supporting decision trace.
    """

    type: Literal["recommendation"]
    priority: Literal["high", "medium", "low"]
    subject: str | None = Field(default=None, min_length=1, exclude_if=lambda value: value is None)
    action: str = Field(min_length=1)
    income_dependent: bool
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


class MaterialContradiction(DecisionModel):
    """Decision-changing mismatch.

    Attributes
    ----------
    fact_id : int | None
        Commitment identity when applicable.
    label : str | None
        Commitment label when applicable.
    frequency : Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"] | None
        Declared cadence when recurring.
    event_date : date | None
        Declared date when one-off.
    declared_value : float
        Last confirmed amount.
    last_confirmed_at : datetime
        Last explicit confirmation.
    signal : Literal
        Admitted contradiction signal.
    observed_value : float
        Median or direct observed amount.
    period : list[str]
        Exact admitted cycles or event.
    scope : str
        Compared financial object.
    affected_subject : str
        Decision output blocked by doubt.
    transaction_ids : list[int]
        Source transactions.
    observation_keys : list[str]
        Stable evidence identities.
    acknowledged_observations : list[str]
        Previously accepted evidence identities.
    resolution_options : list[Literal]
        Closed resolution catalog.
    """

    fact_id: int | None = Field(default=None, exclude_if=lambda value: value is None)
    label: str | None = Field(default=None, exclude_if=lambda value: value is None)
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    event_date: date | None = Field(default=None, exclude_if=lambda value: value is None)
    declared_value: float
    last_confirmed_at: datetime
    signal: Literal[
        "recurring_income_lower",
        "recurring_income_higher",
        "recurring_obligation_higher",
        "recurring_obligation_lower",
        "one_off_income_mismatch",
        "one_off_obligation_mismatch",
    ]
    observed_value: float
    period: list[str] = Field(min_length=1)
    scope: str = Field(min_length=1)
    affected_subject: str = Field(min_length=1)
    transaction_ids: list[int] = Field(default_factory=list)
    observation_keys: list[str] = Field(min_length=1)
    acknowledged_observations: list[str] = Field(default_factory=list)
    resolution_options: list[Literal["confirm", "correct", "session", "unknown", "skip", "delete"]] = Field(
        default=["confirm", "correct", "session", "unknown", "skip", "delete"]
    )

    @model_validator(mode="after")
    def require_resolution_fields(self) -> Self:
        """Require fields needed to submit every advertised resolution."""
        if self.signal.startswith("recurring_") and self.frequency is None:
            raise ValueError("recurring contradiction requires frequency")
        if self.signal.startswith("one_off_") and self.event_date is None:
            raise ValueError("one-off contradiction requires event_date")
        if "obligation" in self.signal and (self.fact_id is None or self.label is None):
            raise ValueError("obligation contradiction requires fact_id and label")
        return self


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
        One-based position in capped flow.
    decision_lever : DecisionLever
        Strongest possible decision change.
    answer_ease : AnswerEase
        Relative answer effort.
    fact_type : ClarificationFactType
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
    decision_lever: DecisionLever = "action_or_priority"
    answer_ease: AnswerEase = "moderate"
    fact_type: ClarificationFactType
    material_effects: list[str] = Field(min_length=2)
    coverage_months: list[str] | None = None
    transaction_ids: list[int] | None = None
    linked_transaction_ids: list[int] | None = None
    transitions: list[str] = Field(default_factory=list)
    contradiction: MaterialContradiction | None = None

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
        if self.fact_type == "period_coverage" and not self.coverage_months:
            raise ValueError("period coverage clarification requires coverage_months")
        if self.fact_type != "period_coverage" and self.coverage_months is not None:
            raise ValueError("coverage_months only apply to period coverage")
        if self.fact_type == "transaction_nature":
            if not self.transaction_ids:
                raise ValueError("transaction nature clarification requires transaction_ids")
            if not self.linked_transaction_ids:
                raise ValueError("transaction nature clarification requires linked_transaction_ids")
        elif self.contradiction is not None:
            if self.transaction_ids != self.contradiction.transaction_ids or self.linked_transaction_ids is not None:
                raise ValueError("contradiction transaction ids must match evidence")
        elif self.transaction_ids is not None or self.linked_transaction_ids is not None:
            raise ValueError("transaction links require transaction nature or contradiction")
        return self


DecisionOutput = Annotated[
    RecommendationOutput | NoActionOutput | UnresolvedOutput | ClarificationOutput,
    Field(discriminator="type"),
]


class ClarificationTraceEntry(DecisionModel):
    """One consumed clarification.

    Attributes
    ----------
    question_number : int
        One-based order.
    fact_type : ClarificationFactType
        Consumed fact.
    decision_lever : DecisionLever
        Decision effect.
    outcome : Literal
        Current resolution.
    """

    question_number: int = Field(ge=1, le=3)
    fact_type: ClarificationFactType
    decision_lever: DecisionLever
    outcome: Literal["pending", "answered", "skipped", "unknown"]


class ClarificationTrace(DecisionModel):
    """Auditable clarification session.

    Attributes
    ----------
    questions_consumed : int
        Questions shown.
    questions : list[ClarificationTraceEntry]
        Ordered history.
    stop_reason : Literal
        Pending or terminal reason.
    """

    questions_consumed: int = Field(default=0, ge=0, le=3)
    questions: list[ClarificationTraceEntry] = Field(default_factory=list, max_length=3)
    stop_reason: Literal["question_pending", "no_remaining_decision_impact", "quota_reached"] = (
        "no_remaining_decision_impact"
    )

    @model_validator(mode="after")
    def require_consistent_history(self) -> Self:
        """Validate count, order, and pending state.

        Returns
        -------
        Self
            Consistent trace.

        Raises
        ------
        ValueError
            Count, order, or pending state diverges.
        """
        if self.questions_consumed != len(self.questions):
            raise ValueError("questions_consumed must match questions")
        if [question.question_number for question in self.questions] != list(range(1, self.questions_consumed + 1)):
            raise ValueError("clarification question numbers must be sequential")
        has_pending = bool(self.questions and self.questions[-1].outcome == "pending")
        if (self.stop_reason == "question_pending") != has_pending:
            raise ValueError("pending stop reason must match final question")
        return self


class AdviceDraft(DecisionModel):
    """Internal decision outputs before queue selection.

    Attributes
    ----------
    outputs : list[DecisionOutput]
        Candidate decisions and questions.
    """

    outputs: list[DecisionOutput] = Field(min_length=1)


class AdviceResponse(AdviceDraft):
    """Monthly decisions with visible clarification state.

    Attributes
    ----------
    clarification_trace : ClarificationTrace
        Session count, order, and stop reason.
    """

    clarification_trace: ClarificationTrace = Field(default_factory=ClarificationTrace)

    @model_validator(mode="after")
    def allow_one_clarification(self) -> Self:
        """Enforce one visible question.

        Returns
        -------
        Self
            Progressive response.

        Raises
        ------
        ValueError
            Multiple question cards remain.
        """
        if sum(output.type == "clarification" for output in self.outputs) > 1:
            raise ValueError("advice allows one clarification at a time")
        return self
