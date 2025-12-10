"""Pydantic models for Historical Data API endpoint."""

from datetime import datetime
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field, computed_field

from app.responses._types import ScoreLabelLiteral, ScoreTrendLiteral

if TYPE_CHECKING:
    from app.db.models.month import Month


class MonthReference(BaseModel):
    """Reference to a specific month for best/worst identification."""

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    score: int = Field(ge=0, le=3)


class MonthHistory(BaseModel):
    """Single month in historical data response."""

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float = Field(ge=0.0)
    choice_percentage: float = Field(ge=0.0)
    compound_percentage: float = Field(ge=0.0)
    score: int = Field(ge=0, le=3)
    score_label: ScoreLabelLiteral | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def month_label(self) -> str:
        """Return formatted label (e.g., 'Oct 2025')."""
        return datetime(self.year, self.month, 1).strftime("%b %Y")

    @classmethod
    def from_model(cls, month: "Month") -> Self:
        """
        Create a MonthHistory from a database Month model.

        Parameters
        ----------
        month : Month
            Database month record.

        Returns
        -------
        MonthHistory
            Pydantic model instance.
        """
        # ##>: score_label from database is str | None, validated by Pydantic against literal.
        return cls(
            year=month.year,
            month=month.month,
            total_income=month.total_income,
            total_core=month.total_core,
            total_choice=month.total_choice,
            total_compound=month.total_compound,
            core_percentage=month.core_percentage,
            choice_percentage=month.choice_percentage,
            compound_percentage=month.compound_percentage,
            score=month.score,
            score_label=month.score_label,  # type: ignore[arg-type]
        )


class HistorySummary(BaseModel):
    """Summary statistics for historical data."""

    total_months: int = Field(ge=0)
    average_score: float = Field(ge=0.0, le=3.0)
    score_trend: ScoreTrendLiteral
    best_month: MonthReference | None = None
    worst_month: MonthReference | None = None


class HistoryResponse(BaseModel):
    """Response for GET /api/months/history endpoint."""

    months: list[MonthHistory]
    summary: HistorySummary
