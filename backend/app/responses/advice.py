"""Pydantic models for advice API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field

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
    """

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    regenerate: bool = False


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
