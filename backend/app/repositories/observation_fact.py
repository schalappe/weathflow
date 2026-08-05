"""Observation validity persistence."""

from collections.abc import Sequence
from hashlib import sha256

from sqlalchemy.orm import Session

from app.db.models.base import utc_now
from app.db.models.observation_fact import (
    ContradictionAcknowledgement,
    ImportCoverageEvidence,
    PeriodCoverageFact,
    TransactionNatureFact,
)
from app.db.models.transaction import Transaction


class ObservationFactRepository:
    """Store exact coverage facts and import provenance.

    Attributes
    ----------
    _db : Session
        Database transaction.
    """

    def __init__(self, db: Session) -> None:
        """Bind database transaction.

        Parameters
        ----------
        db : Session
            Database transaction.
        """
        self._db = db

    @staticmethod
    def _coverage_key(coverage_months: Sequence[str]) -> str:
        """Return canonical analyzed-window key.

        Parameters
        ----------
        coverage_months : Sequence[str]
            Calendar months in analyzed window.

        Returns
        -------
        str
            Sorted unique month key.
        """
        return ",".join(sorted(set(coverage_months)))

    def get_period_coverage(self, coverage_months: Sequence[str]) -> PeriodCoverageFact | None:
        """Return exact-window coverage.

        Parameters
        ----------
        coverage_months : Sequence[str]
            Calendar months in analyzed window.

        Returns
        -------
        PeriodCoverageFact | None
            Exact fact when confirmed.
        """
        scope_key = self._coverage_key(coverage_months)
        return self._db.query(PeriodCoverageFact).filter(PeriodCoverageFact.scope_key == scope_key).first()

    def put_period_coverage(
        self,
        coverage_months: Sequence[str],
        complete: bool,
        missing_elements: Sequence[str],
    ) -> PeriodCoverageFact:
        """Confirm exact-window coverage.

        Parameters
        ----------
        coverage_months : Sequence[str]
            Calendar months in analyzed window.
        complete : bool
            Whether source scope is complete and gap-free.
        missing_elements : Sequence[str]
            Known missing accounts, dates, or imports.

        Returns
        -------
        PeriodCoverageFact
            Persisted narrow fact.
        """
        months = sorted(set(coverage_months))
        evidence = self.get_import_evidence(months)
        accounts = sorted({account for item in evidence for account in item.accounts})
        revisions = {f"{item.year:04d}-{item.month:02d}": item.revision for item in evidence}
        issues = sorted({item.issue for item in evidence if item.issue is not None})
        fact = self.get_period_coverage(months)
        now = utc_now().replace(tzinfo=None)
        if fact is None:
            fact = PeriodCoverageFact(scope_key=self._coverage_key(months), state="active")
            self._db.add(fact)
        else:
            fact.state = "corrected"
        fact.coverage_months = months
        fact.accounts = accounts
        fact.complete = complete
        fact.missing_elements = list(missing_elements)
        fact.last_confirmed_at = now
        fact.source_revisions = revisions
        fact.provenance_issues = issues
        self._db.commit()
        self._db.refresh(fact)
        return fact

    def get_import_evidence(self, coverage_months: Sequence[str]) -> list[ImportCoverageEvidence]:
        """Return provenance for requested months.

        Parameters
        ----------
        coverage_months : Sequence[str]
            Calendar months in analyzed window.

        Returns
        -------
        list[ImportCoverageEvidence]
            Existing monthly evidence.
        """
        keys = {tuple(map(int, month.split("-"))) for month in coverage_months}
        if not keys:
            return []
        return [item for item in self._db.query(ImportCoverageEvidence).all() if (item.year, item.month) in keys]

    def begin_import(self, year: int, month: int) -> ImportCoverageEvidence:
        """Record attempted import before external categorization.

        Parameters
        ----------
        year : int
            Calendar year.
        month : int
            Calendar month.

        Returns
        -------
        ImportCoverageEvidence
            Pending provenance revision.
        """
        evidence = (
            self._db.query(ImportCoverageEvidence)
            .filter(ImportCoverageEvidence.year == year, ImportCoverageEvidence.month == month)
            .first()
        )
        if evidence is None:
            evidence = ImportCoverageEvidence(
                year=year,
                month=month,
                accounts=[],
                revision=0,
                issue_details=[],
            )
            self._db.add(evidence)
        evidence.revision += 1
        evidence.issue = "failed_import"
        evidence.issue_details = []
        evidence.updated_at = utc_now().replace(tzinfo=None)
        self._db.commit()
        self._db.refresh(evidence)
        return evidence

    def finish_import(
        self,
        evidence: ImportCoverageEvidence,
        accounts: Sequence[str],
        issue: str | None,
        missing_result_count: int,
    ) -> ImportCoverageEvidence:
        """Record successful import and admitted provenance limits.

        Parameters
        ----------
        evidence : ImportCoverageEvidence
            Pending import revision.
        accounts : Sequence[str]
            Accounts in the imported source.
        issue : str | None
            Explicit source limit.
        missing_result_count : int
            Rows omitted after categorization.

        Returns
        -------
        ImportCoverageEvidence
            Updated provenance.
        """
        imported_accounts = sorted(set(accounts))
        missing_accounts = sorted(set(evidence.accounts) - set(imported_accounts))
        if issue is not None:
            evidence.issue = issue
            evidence.issue_details = []
        elif missing_result_count:
            evidence.issue = "incomplete_import"
            evidence.issue_details = [f"{missing_result_count} transaction(s) non importée(s)"]
        elif missing_accounts:
            evidence.issue = "account_missing"
            evidence.issue_details = missing_accounts
        else:
            evidence.issue = None
            evidence.issue_details = []
        evidence.accounts = imported_accounts
        evidence.updated_at = utc_now().replace(tzinfo=None)
        self._db.commit()
        self._db.refresh(evidence)
        return evidence

    @staticmethod
    def transaction_key(transaction: Transaction) -> str:
        """Hash stable source fields.

        Parameters
        ----------
        transaction : Transaction
            Source transaction.

        Returns
        -------
        str
            Stable key unaffected by category edits.
        """
        source = "|".join(
            (
                transaction.date.isoformat(),
                transaction.description,
                f"{transaction.amount:.2f}",
                transaction.account or "",
            )
        )
        return sha256(source.encode()).hexdigest()

    def get_transaction_natures(self) -> list[TransactionNatureFact]:
        """Return durable transaction-meaning facts.

        Returns
        -------
        list[TransactionNatureFact]
            Stored narrow facts.
        """
        return self._db.query(TransactionNatureFact).order_by(TransactionNatureFact.id).all()

    def put_transaction_nature(
        self,
        transactions: Sequence[Transaction],
        nature: str,
        scope: str,
        acknowledged_links: Sequence[str],
    ) -> TransactionNatureFact:
        """Confirm exact occurrences without merchant extrapolation.

        Parameters
        ----------
        transactions : Sequence[Transaction]
            Explicitly confirmed occurrences.
        nature : str
            Confirmed financial nature.
        scope : str
            Occurrence or explicit-series scope.
        acknowledged_links : Sequence[str]
            Structural links present at confirmation.

        Returns
        -------
        TransactionNatureFact
            Persisted narrow fact.
        """
        transaction_keys = list(dict.fromkeys(self.transaction_key(transaction) for transaction in transactions))
        scope_key = sha256(",".join(sorted(transaction_keys)).encode()).hexdigest()
        fact = self._db.query(TransactionNatureFact).filter(TransactionNatureFact.scope_key == scope_key).first()
        now = utc_now().replace(tzinfo=None)
        if fact is None:
            fact = TransactionNatureFact(scope_key=scope_key, state="active")
            self._db.add(fact)
        else:
            fact.state = "corrected"
        fact.transaction_keys = transaction_keys
        fact.nature = nature
        fact.scope = scope
        fact.last_confirmed_at = now
        fact.acknowledged_links = sorted(set(acknowledged_links))
        self._db.commit()
        self._db.refresh(fact)
        return fact

    def get_contradiction_acknowledgement(
        self,
        fact_key: str,
    ) -> ContradictionAcknowledgement | None:
        """Return latest evidence acknowledgement.

        Parameters
        ----------
        fact_key : str
            Declared fact identity.

        Returns
        -------
        ContradictionAcknowledgement | None
            Stored acknowledgement when present.
        """
        return (
            self._db.query(ContradictionAcknowledgement)
            .filter(ContradictionAcknowledgement.fact_key == fact_key)
            .first()
        )

    def acknowledge_contradiction(
        self,
        fact_key: str,
        observation_keys: Sequence[str],
    ) -> ContradictionAcknowledgement:
        """Replace acknowledged evidence after explicit resolution.

        Parameters
        ----------
        fact_key : str
            Declared fact identity.
        observation_keys : Sequence[str]
            Evidence identities accepted by the user.

        Returns
        -------
        ContradictionAcknowledgement
            Stored acknowledgement.
        """
        acknowledgement = self.get_contradiction_acknowledgement(fact_key)
        if acknowledgement is None:
            acknowledgement = ContradictionAcknowledgement(fact_key=fact_key)
            self._db.add(acknowledgement)
        acknowledgement.observation_keys = sorted(set(observation_keys))
        acknowledgement.confirmed_at = utc_now().replace(tzinfo=None)
        self._db.commit()
        self._db.refresh(acknowledgement)
        return acknowledgement
