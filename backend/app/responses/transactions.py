"""Pydantic models for Transaction API endpoints."""

from pydantic import BaseModel, Field

from app.db.enums import MoneyMapType
from app.responses.months import MonthSummary, TransactionResponse


class UpdateTransactionRequest(BaseModel):
    """Request body for PATCH /api/transactions/{id}."""

    money_map_type: MoneyMapType = Field(..., description="New Money Map category type")
    money_map_subcategory: str | None = Field(None, description="New subcategory (null for EXCLUDED)")


class UpdateTransactionResponse(BaseModel):
    """Response for PATCH /api/transactions/{id}."""

    success: bool = Field(default=True)
    transaction: TransactionResponse
    updated_month_stats: MonthSummary
