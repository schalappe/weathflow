"""Pydantic models for upload and categorize API endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


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

    year: int
    month: int
    transactions_categorized: int
    low_confidence_count: int
    score: int = Field(ge=0, le=3)
    score_label: str


class CategorizeResponse(BaseModel):
    """Response for POST /api/categorize endpoint."""

    success: bool
    months_processed: list[MonthResult]
    total_api_calls: int


ImportMode = Literal["replace", "merge"]
