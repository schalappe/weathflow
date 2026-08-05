"""Persisted observation coverage and transaction meaning."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PeriodCoverageFact(Base):
    """Persist exact analyzed-window coverage.

    Attributes
    ----------
    coverage_months : list[str]
        Exact calendar window.
    accounts : list[str]
        Accounts imported for that window.
    complete : bool
        Whether the source is complete and gap-free.
    missing_elements : list[str]
        Known source omissions.
    state : str
        Active, corrected, or confirmation-required state.
    last_confirmed_at : datetime
        Latest explicit confirmation.
    source_revisions : dict[str, int]
        Import revision by month.
    provenance_issues : list[str]
        Source limits known at confirmation.
    """

    __tablename__ = "period_coverage_fact"
    __table_args__ = (UniqueConstraint("scope_key", name="uq_period_coverage_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scope_key: Mapped[str] = mapped_column(String(300), nullable=False)
    coverage_months: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    accounts: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    complete: Mapped[bool] = mapped_column(nullable=False)
    missing_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source_revisions: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    provenance_issues: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class ImportCoverageEvidence(Base):
    """Persist import provenance by calendar month.

    Attributes
    ----------
    year : int
        Calendar year.
    month : int
        Calendar month.
    accounts : list[str]
        Accounts in the latest import.
    revision : int
        Monotonic import revision.
    issue : str | None
        Known provenance limit.
    issue_details : list[str]
        Missing accounts or rows.
    updated_at : datetime
        Latest import attempt.
    """

    __tablename__ = "import_coverage_evidence"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_import_coverage_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    accounts: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue: Mapped[str | None] = mapped_column(String(40))
    issue_details: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TransactionNatureFact(Base):
    """Persist confirmed meaning for explicit historical occurrences.

    Attributes
    ----------
    transaction_keys : list[str]
        Stable source transaction keys.
    nature : str
        Confirmed financial nature.
    scope : str
        Occurrence or explicit-series scope.
    state : str
        Active or corrected state.
    last_confirmed_at : datetime
        Latest explicit confirmation.
    acknowledged_links : list[str]
        Structural links present at confirmation.
    """

    __tablename__ = "transaction_nature_fact"
    __table_args__ = (UniqueConstraint("scope_key", name="uq_transaction_nature_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scope_key: Mapped[str] = mapped_column(String(64), nullable=False)
    transaction_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    nature: Mapped[str] = mapped_column(String(30), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    acknowledged_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class ContradictionAcknowledgement(Base):
    """Persist acknowledged evidence for one declared fact.

    Attributes
    ----------
    fact_key : str
        Declared fact identity.
    observation_keys : list[str]
        Evidence identities accepted by the user.
    confirmed_at : datetime
        Latest explicit resolution.
    """

    __tablename__ = "contradiction_acknowledgement"
    __table_args__ = (UniqueConstraint("fact_key", name="uq_contradiction_fact"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fact_key: Mapped[str] = mapped_column(String(80), nullable=False)
    observation_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
