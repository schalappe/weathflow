"""Persisted declared income context."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IncomeFact(Base):
    """Persist one habitual or expected income fact."""

    __tablename__ = "income_fact"

    fact_type: Mapped[str] = mapped_column(String(40), primary_key=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    frequency: Mapped[str | None] = mapped_column(String(20))
    expected_date: Mapped[date | None] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
