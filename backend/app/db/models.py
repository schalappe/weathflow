"""SQLAlchemy models for Money Map Manager."""

from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    """Return current UTC timestamp for database defaults."""
    return datetime.now(UTC)


class MoneyMapType(str, Enum):
    """
    Budget category types for the Money Map (50/30/20) framework.

    Categories:
        INCOME: Revenue such as salary.
        CORE: Necessities (target ≤ 50% of income).
        CHOICE: Wants/discretionary spending (target ≤ 30% of income).
        COMPOUND: Savings/investments (target ≥ 20% of income).
        EXCLUDED: Internal transfers not counted in budget calculations.
    """

    INCOME = 'INCOME'
    CORE = 'CORE'
    CHOICE = 'CHOICE'
    COMPOUND = 'COMPOUND'
    EXCLUDED = 'EXCLUDED'


class ScoreLabel(str, Enum):
    """
    Human-readable labels for Money Map scores.

    The score (0-3) indicates how many of the three budget thresholds are met:
        POOR (0): No thresholds met.
        NEED_IMPROVEMENT (1): One threshold met.
        OKAY (2): Two thresholds met.
        GREAT (3): All three thresholds met.
    """

    POOR = 'Poor'
    NEED_IMPROVEMENT = 'Need Improvement'
    OKAY = 'Okay'
    GREAT = 'Great'


# ##>: Generate CHECK constraint values dynamically from enum to avoid duplication.
_MONEY_MAP_VALUES = "', '".join(t.value for t in MoneyMapType)
_MONEY_MAP_CHECK = f"money_map_type IS NULL OR money_map_type IN ('{_MONEY_MAP_VALUES}')"


class Month(Base):
    """Monthly financial summary with Money Map score."""

    __tablename__ = 'months'
    __table_args__ = (
        UniqueConstraint('year', 'month', name='uq_year_month'),
        CheckConstraint('month >= 1 AND month <= 12', name='ck_valid_month'),
        Index('idx_months_year_month', 'year', 'month'),
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

    transactions: Mapped[list['Transaction']] = relationship(
        back_populates='month',
        cascade='all, delete-orphan',
    )
    advice_records: Mapped[list['Advice']] = relationship(
        back_populates='month',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'<Month(id={self.id}, year={self.year}, month={self.month}, score={self.score})>'


class Transaction(Base):
    """Individual financial transaction linked to a month."""

    __tablename__ = 'transactions'
    __table_args__ = (
        CheckConstraint(_MONEY_MAP_CHECK, name='ck_valid_money_map_type'),
        Index('idx_transactions_month', 'month_id'),
        Index('idx_transactions_date', 'date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey('months.id'), nullable=False)

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

    month: Mapped['Month'] = relationship(back_populates='transactions')

    def __repr__(self) -> str:
        return f'<Transaction(id={self.id}, date={self.date}, amount={self.amount})>'


class Advice(Base):
    """AI-generated financial advice for a month."""

    __tablename__ = 'advice'
    __table_args__ = (Index('idx_advice_month', 'month_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey('months.id'), nullable=False)
    advice_text: Mapped[str] = mapped_column(String(5000), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    month: Mapped['Month'] = relationship(back_populates='advice_records')

    def __repr__(self) -> str:
        return f'<Advice(id={self.id}, month_id={self.month_id})>'
