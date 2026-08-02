"""Persisted obligation and debt facts."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CommitmentFact(Base):
    """Persist one declared obligation or debt fact.

    Attributes
    ----------
    fact_type : str
        Closed-catalog fact type.
    label : str
        User-facing identifier.
    amount : float | None
        Obligation amount.
    frequency : str | None
        Recurrence.
    balance : float | None
        Current debt balance.
    overdue_amount : float | None
        Known overdue amount.
    minimum_payment : float | None
        Contractual minimum.
    annual_rate : float | None
        Annual percentage rate.
    cost : float | None
        Known debt cost.
    due_date : date | None
        One-off due date.
    end_date : date | None
        Explicit end.
    state : str
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime
        Reuse cutoff.
    """

    __tablename__ = "commitment_fact"

    id: Mapped[int] = mapped_column(primary_key=True)
    fact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float)
    frequency: Mapped[str | None] = mapped_column(String(20))
    balance: Mapped[float | None] = mapped_column(Float)
    overdue_amount: Mapped[float | None] = mapped_column(Float)
    minimum_payment: Mapped[float | None] = mapped_column(Float)
    annual_rate: Mapped[float | None] = mapped_column(Float)
    cost: Mapped[float | None] = mapped_column(Float)
    due_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
