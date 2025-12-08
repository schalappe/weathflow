"""Month model for monthly financial summaries."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import utc_now

if TYPE_CHECKING:
    from app.db.models.advice import Advice
    from app.db.models.transaction import Transaction


class Month(Base):
    """Monthly financial summary with Money Map score."""

    __tablename__ = "months"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_year_month"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_valid_month"),
        Index("idx_months_year_month", "year", "month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    total_income: Mapped[float] = mapped_column(Float, default=0.0)
    total_core: Mapped[float] = mapped_column(Float, default=0.0)
    total_choice: Mapped[float] = mapped_column(Float, default=0.0)
    total_compound: Mapped[float] = mapped_column(Float, default=0.0)

    core_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    choice_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    compound_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    score: Mapped[int] = mapped_column(Integer, default=0)
    score_label: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # ##>: Cascade delete ensures orphan transactions and advice are removed when a month is deleted.
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="month",
        cascade="all, delete-orphan",
    )
    advice_records: Mapped[list["Advice"]] = relationship(
        back_populates="month",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Month(id={self.id}, year={self.year}, month={self.month}, score={self.score})>"
