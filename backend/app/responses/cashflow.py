"""Pydantic response models for cash flow Sankey diagram API."""

from pydantic import BaseModel, Field


class CategoryBreakdown(BaseModel):
    """Breakdown of spending within a single subcategory."""

    subcategory: str = Field(..., description="Subcategory name (e.g., Housing, Groceries)")
    amount: float = Field(..., ge=0, description="Total amount in this subcategory (always positive)")


class CashFlowData(BaseModel):
    """Aggregated cash flow data for Sankey diagram visualization."""

    income_total: float = Field(..., ge=0, description="Total income across the period")
    core_total: float = Field(..., ge=0, description="Total Core spending (absolute value)")
    choice_total: float = Field(..., ge=0, description="Total Choice spending (absolute value)")
    compound_total: float = Field(..., ge=0, description="Total Compound (savings) - 0 if deficit exists")
    deficit: float = Field(..., ge=0, description="Deficit amount when spending > income")

    core_breakdown: list[CategoryBreakdown] = Field(
        default_factory=list, description="Subcategory breakdown for Core spending"
    )
    choice_breakdown: list[CategoryBreakdown] = Field(
        default_factory=list, description="Subcategory breakdown for Choice spending"
    )
    compound_breakdown: list[CategoryBreakdown] = Field(
        default_factory=list, description="Subcategory breakdown for Compound (savings)"
    )


class CashFlowResponse(BaseModel):
    """API response wrapper for cash flow data."""

    data: CashFlowData = Field(..., description="Cash flow data for the Sankey diagram")
    period_months: int = Field(..., ge=0, description="Number of months in the period (0 = all time)")
