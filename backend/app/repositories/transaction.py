"""Repository for Transaction data access operations."""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.transaction import Transaction


class TransactionRepository:
    """
    Repository for Transaction data access operations.

    Encapsulates all database queries related to Transaction entities,
    providing a clean interface for services to access transaction data
    without direct SQLAlchemy coupling.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Parameters
        ----------
        db : Session
            SQLAlchemy database session.
        """
        self._db = db

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """
        Get transaction by primary key.

        Parameters
        ----------
        transaction_id : int
            Primary key of the transaction.

        Returns
        -------
        Transaction | None
            Transaction record or None if not found.
        """
        return self._db.get(Transaction, transaction_id)

    def get_filtered(
        self,
        month_id: int,
        *,
        category_types: list[str] | None = None,
        search: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Transaction], int]:
        """
        Get filtered, paginated transactions for a month.

        Parameters
        ----------
        month_id : int
            Month ID to filter transactions.
        category_types : list[str] | None
            Filter by money_map_type values.
        search : str | None
            Case-insensitive partial match on description.
        start_date : date | None
            Filter transactions on or after this date.
        end_date : date | None
            Filter transactions on or before this date.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        tuple[list[Transaction], int]
            Tuple of (transactions, total_count) for pagination.

        Notes
        -----
        Search string should be escaped by caller using escape_like_pattern().
        All filters are applied with AND logic.
        """
        query = self._db.query(Transaction).filter(Transaction.month_id == month_id)

        if category_types is not None and len(category_types) > 0:
            query = query.filter(Transaction.money_map_type.in_(category_types))

        if search is not None and search.strip():
            escaped_search = self._escape_like_pattern(search.strip())
            query = query.filter(Transaction.description.ilike(f"%{escaped_search}%", escape="\\"))

        if start_date is not None:
            query = query.filter(Transaction.date >= start_date)

        if end_date is not None:
            query = query.filter(Transaction.date <= end_date)

        total_count = query.count()
        # [>]: Order by date ascending (start of month to end of month).
        transactions = query.order_by(Transaction.date.asc()).offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total_count

    def get_all_for_month(self, month_id: int) -> list[Transaction]:
        """
        Get all transactions for a month without pagination.

        Used for export functionality where all transactions are needed.

        Parameters
        ----------
        month_id : int
            Month ID to filter transactions.

        Returns
        -------
        list[Transaction]
            All transactions for the month, ordered by date ascending.
        """
        query = self._db.query(Transaction).filter(Transaction.month_id == month_id)
        # [>]: Order by date ascending (start of month to end of month).
        return query.order_by(Transaction.date.asc()).all()

    def aggregate_totals(self, month_id: int) -> tuple[float, float, float]:
        """
        Aggregate income, core, choice totals for a month.

        Uses a single SQL query with conditional aggregation for efficiency.
        Income is summed from positive amounts with INCOME type.
        Core and Choice are summed as absolute values from negative amounts.

        Parameters
        ----------
        month_id : int
            Month ID to aggregate.

        Returns
        -------
        tuple[float, float, float]
            Tuple of (income, core, choice) totals.
        """
        result = (
            self._db.query(
                func.coalesce(
                    func.sum(Transaction.amount).filter(
                        Transaction.money_map_type == MoneyMapType.INCOME.value,
                        Transaction.amount > 0,
                    ),
                    0.0,
                ).label("income"),
                func.coalesce(
                    func.abs(
                        func.sum(Transaction.amount).filter(
                            Transaction.money_map_type == MoneyMapType.CORE.value,
                            Transaction.amount < 0,
                        )
                    ),
                    0.0,
                ).label("core"),
                func.coalesce(
                    func.abs(
                        func.sum(Transaction.amount).filter(
                            Transaction.money_map_type == MoneyMapType.CHOICE.value,
                            Transaction.amount < 0,
                        )
                    ),
                    0.0,
                ).label("choice"),
            )
            .filter(Transaction.month_id == month_id)
            .one()
        )
        return float(result.income), float(result.core), float(result.choice)

    def add_bulk(self, transactions: list[Transaction]) -> None:
        """
        Add multiple transactions in bulk.

        Parameters
        ----------
        transactions : list[Transaction]
            List of Transaction objects to add.

        Notes
        -----
        Uses add_all() for efficiency. Caller should flush/commit as needed.
        """
        if transactions:
            self._db.add_all(transactions)

    def delete_for_month(self, month_id: int) -> int:
        """
        Delete all transactions for a month.

        Parameters
        ----------
        month_id : int
            Month ID whose transactions should be deleted.

        Returns
        -------
        int
            Number of transactions deleted.

        Notes
        -----
        Uses flush() after delete. Caller is responsible for commit().
        """
        count = self._db.query(Transaction).filter(Transaction.month_id == month_id).delete()
        self._db.flush()
        return count

    def get_keys_for_month(self, month_id: int) -> set[str]:
        """
        Get transaction keys for duplicate detection.

        Returns keys in format: "date_description_amount_account"

        Parameters
        ----------
        month_id : int
            Month ID to get keys for.

        Returns
        -------
        set[str]
            Set of unique transaction keys.
        """
        transactions = (
            self._db.query(Transaction.date, Transaction.description, Transaction.amount, Transaction.account)
            .filter(Transaction.month_id == month_id)
            .all()
        )
        return {f"{t.date.isoformat()}_{t.description}_{float(t.amount)}_{t.account}" for t in transactions}

    def flush(self) -> None:
        """Flush pending changes to database without committing."""
        self._db.flush()

    @staticmethod
    def _escape_like_pattern(search: str) -> str:
        """
        Escape SQL LIKE wildcards to treat them as literal characters.

        Parameters
        ----------
        search : str
            The search string to escape.

        Returns
        -------
        str
            Search string with %, _, and \\ escaped.
        """
        return search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
