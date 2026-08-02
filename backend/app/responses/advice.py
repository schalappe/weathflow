"""Pydantic models for advice API endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

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
