"""Pydantic models for upload and categorize API endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

from app.responses._types import ScoreLabelLiteral


class TransactionPreview(BaseModel):
    """Single transaction preview for upload response."""

    date: str
    description: str
    amount: float


class MonthSummaryResponse(BaseModel):
    """Summary statistics for a detected month."""

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    transaction_count: int = Field(ge=0)
    total_income: float = Field(ge=0)
    total_expenses: float = Field(ge=0)


class UploadResponse(BaseModel):
    """Response for POST /api/upload endpoint."""

    success: bool
    total_transactions: int
    months_detected: list[MonthSummaryResponse]
    preview_by_month: dict[str, list[TransactionPreview]]


class MonthResult(BaseModel):
    """Result of categorizing a single month."""

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    transactions_categorized: int = Field(ge=0)
    low_confidence_count: int = Field(ge=0, description="Transactions with confidence below 0.8")
    score: int = Field(ge=0, le=3)
    score_label: ScoreLabelLiteral


class CategorizeResponse(BaseModel):
    """Response for POST /api/categorize endpoint."""

    success: bool
    months_processed: list[MonthResult]
    months_not_found: list[str] = Field(default_factory=list, description="Requested months not in CSV")
    total_api_calls: int


ImportMode = Literal["replace", "merge"]
