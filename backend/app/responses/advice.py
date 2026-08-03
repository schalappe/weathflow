"""Pydantic models for advice API endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.db.models.emergency_fund_fact import EmergencyFundFactType
from app.services.advice.models import AdviceResponse

AdviceData = AdviceResponse


class GenerateAdviceRequest(BaseModel):
    """Advice generation request.

    Attributes
    ----------
    year : int
        Target year.
    month : int
        Target month.
    regenerate : bool
        Bypass cached advice.
    active_priority : ActivePriorityInput | None
        Clarification answer.
    remember_priority : bool
        Reuse answer after current session.
    emergency_fund_fact : EmergencyFundFactAnswer | None
        Emergency-fund clarification answer.
    remember_fact : bool
        Reuse emergency-fund answer after current session.
    clarification_action : Literal["skip", "unknown"] | None
        Resolve question without storing a fact.
    """

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    regenerate: bool = False
    active_priority: ActivePriorityInput | None = None
    remember_priority: bool = True
    emergency_fund_fact: EmergencyFundFactAnswer | None = None
    commitment_fact: CommitmentFactInput | None = None
    income_fact: IncomeFactInput | None = None
    remember_fact: bool = True
    clarification_action: Literal["skip", "unknown"] | None = None


class ActivePriorityInput(BaseModel):
    """User-declared active priority.

    Attributes
    ----------
    goal : str
        Current objective.
    target : str
        Objective target.
    deadline : date | None
        Optional objective date.
    """

    goal: str = Field(min_length=1, max_length=500)
    target: str = Field(min_length=1, max_length=500)
    deadline: date | None = None


class ActivePriorityData(ActivePriorityInput):
    """Stored priority lifecycle data.

    Attributes
    ----------
    state : Literal["active", "corrected", "to_confirm"]
        Current lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime
        Reuse cutoff.
    """

    state: Literal["active", "corrected", "to_confirm"]
    last_confirmed_at: datetime
    valid_until: datetime


class ActivePriorityResponse(BaseModel):
    """Current declared priority.

    Attributes
    ----------
    priority : ActivePriorityData | None
        Stored value, including inactive expired value.
    """

    priority: ActivePriorityData | None


class EmergencyFundFactInput(BaseModel):
    """Declared emergency-fund amount.

    Attributes
    ----------
    amount : float
        Non-negative euro amount.
    """

    amount: float = Field(ge=0, allow_inf_nan=False)


class EmergencyFundFactAnswer(EmergencyFundFactInput):
    """Emergency-fund clarification answer.

    Attributes
    ----------
    fact_type : EmergencyFundFactType
        Closed-catalog fact key.
    """

    fact_type: EmergencyFundFactType


class EmergencyFundFactData(EmergencyFundFactInput):
    """Stored emergency-fund amount lifecycle.

    Attributes
    ----------
    fact_type : EmergencyFundFactType
        Closed-catalog fact key.
    state : Literal["active", "corrected", "to_confirm"]
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime
        Reuse cutoff.
    """

    fact_type: EmergencyFundFactType
    state: Literal["active", "corrected", "to_confirm"]
    last_confirmed_at: datetime
    valid_until: datetime


class EmergencyFundFactResponse(BaseModel):
    """One emergency-fund amount.

    Attributes
    ----------
    fact : EmergencyFundFactData
        Stored lifecycle value.
    """

    fact: EmergencyFundFactData


class EmergencyFundContextResponse(BaseModel):
    """All declared emergency-fund amounts.

    Attributes
    ----------
    facts : list[EmergencyFundFactData]
        Stored values, including expired facts.
    """

    facts: list[EmergencyFundFactData]


class IncomeFactLifecycle(BaseModel):
    """Stored income lifecycle."""

    state: Literal["active", "corrected", "to_confirm"]
    last_confirmed_at: datetime
    valid_until: datetime


class UsualDisposableIncomeInput(BaseModel):
    """Habitual disposable income."""

    fact_type: Literal["usual_disposable_income"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"]


class ExpectedOneOffIncomeInput(BaseModel):
    """Dated expected income."""

    fact_type: Literal["expected_one_off_income"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    expected_date: date


IncomeFactInput = Annotated[
    UsualDisposableIncomeInput | ExpectedOneOffIncomeInput,
    Field(discriminator="fact_type"),
]


class UsualDisposableIncomeData(UsualDisposableIncomeInput, IncomeFactLifecycle):
    """Stored habitual income."""


class ExpectedOneOffIncomeData(ExpectedOneOffIncomeInput, IncomeFactLifecycle):
    """Stored expected income."""


IncomeFactData = Annotated[
    UsualDisposableIncomeData | ExpectedOneOffIncomeData,
    Field(discriminator="fact_type"),
]


class IncomeFactResponse(BaseModel):
    """One stored income fact."""

    fact: IncomeFactData


class IncomeContextResponse(BaseModel):
    """Stored income facts."""

    facts: list[IncomeFactData]


CommitmentFactType = Literal[
    "recurring_obligation",
    "one_off_obligation",
    "debt_position",
    "debt_terms",
]
Frequency = Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"]


class CommitmentFactBase(BaseModel):
    """Share declared-fact identity.

    Attributes
    ----------
    label : str
        User-facing identifier.
    """

    label: str = Field(min_length=1, max_length=200)


class RecurringObligationInput(CommitmentFactBase):
    """Accept a recurring obligation answer.

    Attributes
    ----------
    fact_type : Literal["recurring_obligation"]
        Discriminator.
    amount : float
        Payment amount.
    frequency : Frequency
        Recurrence.
    end_date : date | None
        Explicit end.
    """

    fact_type: Literal["recurring_obligation"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    frequency: Frequency
    end_date: date | None = None


class OneOffObligationInput(CommitmentFactBase):
    """Accept a dated obligation answer.

    Attributes
    ----------
    fact_type : Literal["one_off_obligation"]
        Discriminator.
    amount : float
        Payment amount.
    due_date : date
        Payment deadline.
    """

    fact_type: Literal["one_off_obligation"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    due_date: date


class DebtPositionInput(CommitmentFactBase):
    """Accept a current debt position.

    Attributes
    ----------
    fact_type : Literal["debt_position"]
        Discriminator.
    balance : float
        Current balance.
    overdue_amount : float | None
        Known overdue amount.
    """

    fact_type: Literal["debt_position"]
    balance: float = Field(ge=0, allow_inf_nan=False)
    overdue_amount: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class DebtTermsInput(CommitmentFactBase):
    """Accept essential debt terms.

    Attributes
    ----------
    fact_type : Literal["debt_terms"]
        Discriminator.
    minimum_payment : float
        Contractual minimum.
    annual_rate : float | None
        Annual percentage rate.
    cost : float | None
        Known cost.
    end_date : date | None
        Explicit end.
    """

    fact_type: Literal["debt_terms"]
    minimum_payment: float = Field(gt=0, allow_inf_nan=False)
    annual_rate: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    cost: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    end_date: date | None = None


CommitmentFactInput = Annotated[
    RecurringObligationInput | OneOffObligationInput | DebtPositionInput | DebtTermsInput,
    Field(discriminator="fact_type"),
]


class CommitmentFactLifecycle(BaseModel):
    """Expose stored fact lifecycle.

    Attributes
    ----------
    fact_id : int
        Stored fact id.
    state : Literal["active", "corrected", "to_confirm"]
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime
        Reuse cutoff.
    """

    fact_id: int
    state: Literal["active", "corrected", "to_confirm"]
    last_confirmed_at: datetime
    valid_until: datetime


class RecurringObligationData(RecurringObligationInput, CommitmentFactLifecycle):
    """Expose stored recurring obligation.

    Notes
    -----
    Combines recurring input and lifecycle fields.
    """


class OneOffObligationData(OneOffObligationInput, CommitmentFactLifecycle):
    """Expose stored dated obligation.

    Notes
    -----
    Combines dated input and lifecycle fields.
    """


class DebtPositionData(DebtPositionInput, CommitmentFactLifecycle):
    """Expose stored debt position.

    Notes
    -----
    Combines position input and lifecycle fields.
    """


class DebtTermsData(DebtTermsInput, CommitmentFactLifecycle):
    """Expose stored debt terms.

    Notes
    -----
    Combines terms input and lifecycle fields.
    """


CommitmentFactData = Annotated[
    RecurringObligationData | OneOffObligationData | DebtPositionData | DebtTermsData,
    Field(discriminator="fact_type"),
]


class CommitmentFactResponse(BaseModel):
    """Wrap one stored obligation or debt fact.

    Attributes
    ----------
    fact : CommitmentFactData
        Stored fact.
    """

    fact: CommitmentFactData


class CommitmentContextResponse(BaseModel):
    """List stored obligation and debt facts.

    Attributes
    ----------
    facts : list[CommitmentFactData]
        Stored facts.
    """

    facts: list[CommitmentFactData]


class GenerateAdviceResponse(BaseModel):
    """Generated monthly advice.

    Attributes
    ----------
    success : bool
        Request status.
    advice : AdviceData
        Decision outputs.
    generated_at : datetime
        Generation timestamp.
    is_valid : bool
        Source-data validity.
    was_cached : bool
        Cache reuse marker.
    """

    success: bool
    advice: AdviceData
    generated_at: datetime
    is_valid: bool
    was_cached: bool


class EligibilityInfo(BaseModel):
    """Advice generation eligibility.

    Attributes
    ----------
    can_generate : bool
        Generation allowed.
    is_first_advice : bool
        No prior advice exists.
    reason : str | None
        Ineligibility reason.
    """

    can_generate: bool
    is_first_advice: bool
    reason: str | None = None


class GetAdviceResponse(BaseModel):
    """Stored monthly advice result.

    Attributes
    ----------
    success : bool
        Request status.
    advice : AdviceData | None
        Valid decision outputs.
    generated_at : datetime | None
        Generation timestamp.
    is_valid : bool
        Source-data validity.
    exists : bool
        Stored advice marker.
    eligibility : EligibilityInfo
        Generation eligibility.
    """

    success: bool
    advice: AdviceData | None
    generated_at: datetime | None
    is_valid: bool
    exists: bool
    eligibility: EligibilityInfo
