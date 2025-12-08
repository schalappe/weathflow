"""Pydantic models for Monthly Data API endpoints."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

# ##>: Valid score labels matching the ScoreLabel enum in db/enums.py.
ScoreLabelLiteral = Literal["Poor", "Need Improvement", "Okay", "Great"]


class MonthSummary(BaseModel):
    """Month summary with financial totals and Money Map score."""

    id: int
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
    score_label: str | None
    transaction_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class TransactionResponse(BaseModel):
    """Single transaction in month detail response."""

    id: int
    date: date
    description: str
    account: str | None
    amount: float
    bankin_category: str | None
    bankin_subcategory: str | None
    money_map_type: str | None
    money_map_subcategory: str | None
    is_manually_corrected: bool


class PaginationInfo(BaseModel):
    """Pagination metadata for transaction lists."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class MonthsListResponse(BaseModel):
    """Response for GET /api/months endpoint."""

    months: list[MonthSummary]
    total: int = Field(ge=0)


class MonthDetailResponse(BaseModel):
    """Response for GET /api/months/{year}/{month} endpoint."""

    month: MonthSummary
    transactions: list[TransactionResponse]
    pagination: PaginationInfo
