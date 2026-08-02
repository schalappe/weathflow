"""Persisted active financial priority."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ActivePriority(Base):
    """Single user-declared active priority.

    Attributes
    ----------
    goal : str
        Current objective.
    target : str
        Objective target.
    deadline : date | None
        Optional objective date.
    state : str
        Lifecycle state.
    last_confirmed_at : datetime
        Explicit answer time.
    valid_until : datetime
        Reuse cutoff.
    """

    __tablename__ = "active_priority"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    goal: Mapped[str] = mapped_column(String(500), nullable=False)
    target: Mapped[str] = mapped_column(String(500), nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
