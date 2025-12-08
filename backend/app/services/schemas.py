"""Pydantic models for parsed CSV data."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Base model for immutable data structures."""

    model_config = ConfigDict(frozen=True)


class ParsedTransaction(FrozenModel):
    """
    Single parsed transaction from Bankin' CSV.

    This model represents one row from a Bankin' export file, with fields
    mapped to their English equivalents.

    Attributes
    ----------
    date : date
        Transaction date.
    description : str
        Transaction description.
    account : str
        Account name (Compte).
    amount : Decimal
        Transaction amount with 2 decimal precision.
    bankin_category : str
        Bankin's category (Catégorie).
    bankin_subcategory : str
        Bankin's subcategory (Sous-Catégorie).
    note : str | None
        Optional note attached to the transaction.
    is_pointed : bool
        Whether the transaction is reconciled (Pointée).
    """

    date: date
    description: str
    account: str
    amount: Decimal
    bankin_category: str
    bankin_subcategory: str
    note: str | None = None
    is_pointed: bool = False


class MonthSummary(FrozenModel):
    """
    Summary statistics for a single month.

    Attributes
    ----------
    year : int
        The year of this summary.
    month : int
        The month (1-12) of this summary.
    transaction_count : int
        Number of transactions in this month.
    total_income : Decimal
        Sum of all positive amounts.
    total_expenses : Decimal
        Sum of absolute values of all negative amounts.
    """

    year: int
    month: int
    transaction_count: int
    total_income: Decimal
    total_expenses: Decimal


class MonthData(FrozenModel):
    """
    All data for a single month.

    Groups transactions with their summary statistics for a specific month.

    Attributes
    ----------
    year : int
        The year of this month.
    month : int
        The month (1-12).
    transactions : list[ParsedTransaction]
        All transactions in this month.
    summary : MonthSummary
        Aggregated statistics for this month.
    """

    year: int
    month: int
    transactions: list[ParsedTransaction]
    summary: MonthSummary


class ParseResult(FrozenModel):
    """
    Complete result from parsing a Bankin' CSV file.

    Attributes
    ----------
    total_transactions : int
        Total number of transactions parsed.
    months : dict[str, MonthData]
        Transactions grouped by month. Key format is "YYYY-MM".
    """

    total_transactions: int
    months: dict[str, MonthData]
