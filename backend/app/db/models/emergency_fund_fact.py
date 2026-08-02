"""Persisted emergency-fund context."""

from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

EmergencyFundFactType = Literal["liquid_reserve", "safety_floor", "priority_allocation"]


class EmergencyFundFact(Base):
    """One independently fresh emergency-fund amount.

    Attributes
    ----------
    fact_type : str
        Closed-catalog fact key.
    amount : float
        Declared euro amount.
    state : str
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime
        Reuse cutoff.
    """

    __tablename__ = "emergency_fund_fact"

    fact_type: Mapped[str] = mapped_column(String(30), primary_key=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
