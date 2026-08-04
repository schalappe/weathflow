"""Persisted financial limits and action unavailability."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ConstraintFact(Base):
    """Persist one scoped decision constraint.

    Attributes
    ----------
    id : int
        Primary key.
    fact_type : str
        Constraint discriminator.
    scope_type : str | None
        Financial-limit scope kind.
    scope : str | None
        Financial-limit scope.
    limit_type : str | None
        Financial-limit boundary kind.
    amount : float | None
        Financial-limit amount.
    action : str | None
        Unavailable action.
    review_date : date | None
        Explicit action review date.
    state : str
        Lifecycle state.
    last_confirmed_at : datetime
        Last declaration timestamp.
    valid_until : datetime
        Freshness cutoff.
    """

    __tablename__ = "constraint_fact"

    id: Mapped[int] = mapped_column(primary_key=True)
    fact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    scope_type: Mapped[str | None] = mapped_column(String(20))
    scope: Mapped[str | None] = mapped_column(String(200))
    limit_type: Mapped[str | None] = mapped_column(String(30))
    amount: Mapped[float | None] = mapped_column(Float)
    action: Mapped[str | None] = mapped_column(String(200))
    review_date: Mapped[date | None] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
