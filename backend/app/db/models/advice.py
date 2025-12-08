"""Advice model for AI-generated financial recommendations."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import utc_now

if TYPE_CHECKING:
    from app.db.models.month import Month


class Advice(Base):
    """AI-generated financial advice for a month."""

    __tablename__ = "advice"
    __table_args__ = (Index("idx_advice_month", "month_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id"), nullable=False)
    advice_text: Mapped[str] = mapped_column(String(5000), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    month: Mapped[Month] = relationship(back_populates="advice_records")

    def __repr__(self) -> str:
        return f"<Advice(id={self.id}, month_id={self.month_id})>"
