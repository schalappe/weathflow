"""Transaction model for individual financial transactions."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.enums import MoneyMapType
from app.db.models.base import utc_now

if TYPE_CHECKING:
    from app.db.models.month import Month


# ##>: Generate CHECK constraint values dynamically from enum to avoid duplication.
_MONEY_MAP_VALUES = "', '".join(t.value for t in MoneyMapType)
_MONEY_MAP_CHECK = f"money_map_type IS NULL OR money_map_type IN ('{_MONEY_MAP_VALUES}')"


class Transaction(Base):
    """Individual financial transaction linked to a month."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(_MONEY_MAP_CHECK, name="ck_valid_money_map_type"),
        Index("idx_transactions_month", "month_id"),
        Index("idx_transactions_date", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id"), nullable=False)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    account: Mapped[str | None] = mapped_column(String(100))
    bankin_category: Mapped[str | None] = mapped_column(String(100))
    bankin_subcategory: Mapped[str | None] = mapped_column(String(100))

    money_map_type: Mapped[str | None] = mapped_column(String(50))
    money_map_subcategory: Mapped[str | None] = mapped_column(String(100))

    is_manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    month: Mapped[Month] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount})>"
