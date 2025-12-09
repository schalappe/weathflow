"""Pydantic models for Monthly Data API endpoints."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.db.models.month import Month
    from app.db.models.transaction import Transaction


class MonthSummary(BaseModel):
    """Month summary with financial totals and Money Map score."""

    id: int = Field(ge=1)
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float = Field(ge=0, le=100)
    choice_percentage: float = Field(ge=0, le=100)
    compound_percentage: float = Field(ge=0, le=100)
    score: int = Field(ge=0, le=3)
    score_label: str | None
    transaction_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, month: "Month", transaction_count: int) -> Self:
        """
        Create a MonthSummary from a database Month model.

        Parameters
        ----------
        month : Month
            Database month record.
        transaction_count : int
            Number of transactions for this month.

        Returns
        -------
        MonthSummary
            Pydantic model instance.
        """
        return cls(
            id=month.id,
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
            score_label=month.score_label,
            transaction_count=transaction_count,
            created_at=month.created_at,
            updated_at=month.updated_at,
        )


class TransactionResponse(BaseModel):
    """Single transaction in month detail response."""

    id: int = Field(ge=1)
    date: date
    description: str
    account: str | None
    amount: float
    bankin_category: str | None
    bankin_subcategory: str | None
    money_map_type: str | None
    money_map_subcategory: str | None
    is_manually_corrected: bool

    @classmethod
    def from_model(cls, tx: "Transaction") -> Self:
        """
        Create a TransactionResponse from a database Transaction model.

        Parameters
        ----------
        tx : Transaction
            Database transaction record.

        Returns
        -------
        TransactionResponse
            Pydantic model instance.
        """
        return cls(
            id=tx.id,
            date=tx.date,
            description=tx.description,
            account=tx.account,
            amount=tx.amount,
            bankin_category=tx.bankin_category,
            bankin_subcategory=tx.bankin_subcategory,
            money_map_type=tx.money_map_type,
            money_map_subcategory=tx.money_map_subcategory,
            is_manually_corrected=tx.is_manually_corrected,
        )


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
