"""Pydantic models for Transaction API endpoints."""

from pydantic import BaseModel, Field, model_validator

from app.db.enums import MoneyMapType
from app.domain.categories import ALLOWED_SUBCATEGORIES
from app.responses.months import MonthSummary, TransactionResponse


class UpdateTransactionRequest(BaseModel):
    """Request body for PATCH /api/transactions/{id}."""

    money_map_type: MoneyMapType = Field(..., description="New Money Map category type")
    money_map_subcategory: str | None = Field(None, description="New subcategory (null for EXCLUDED)")

    @model_validator(mode="after")
    def validate_subcategory_for_type(self) -> "UpdateTransactionRequest":
        """Validate subcategory is allowed for the given money_map_type."""
        # ##>: EXCLUDED type must have null subcategory.
        if self.money_map_type == MoneyMapType.EXCLUDED:
            if self.money_map_subcategory is not None:
                msg = "EXCLUDED type must have null subcategory"
                raise ValueError(msg)
            return self

        # ##>: Allow None subcategory for any type (optional field).
        if self.money_map_subcategory is None:
            return self

        allowed = ALLOWED_SUBCATEGORIES.get(self.money_map_type, [])
        if self.money_map_subcategory not in allowed:
            msg = f"Invalid subcategory '{self.money_map_subcategory}' for type {self.money_map_type.value}"
            raise ValueError(msg)

        return self


class UpdateTransactionResponse(BaseModel):
    """Response for PATCH /api/transactions/{id}."""

    success: bool = Field(default=True)
    transaction: TransactionResponse
    updated_month_stats: MonthSummary
