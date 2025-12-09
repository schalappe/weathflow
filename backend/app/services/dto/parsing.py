"""Pydantic models for CSV parsing operations."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from app.services.dto._base import FrozenModel


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
        Bankin's category (Categorie).
    bankin_subcategory : str
        Bankin's subcategory (Sous-Categorie).
    note : str | None
        Optional note attached to the transaction.
    is_pointed : bool
        Whether the transaction is reconciled (Pointee).
    """

    date: date
    description: str
    account: str
    amount: Decimal
    bankin_category: str
    bankin_subcategory: str
    note: str | None = None
    is_pointed: bool = False


class ParsedMonthSummary(FrozenModel):
    """
    Summary statistics from CSV parsing for a single month.

    This differs from the API's MonthSummary which includes score data.
    ParsedMonthSummary only contains raw income/expenses before categorization.

    Attributes
    ----------
    year : int
        The year of this summary (2000-2100).
    month : int
        The month (1-12) of this summary.
    transaction_count : int
        Number of transactions in this month (>= 0).
    total_income : Decimal
        Sum of all positive amounts (>= 0).
    total_expenses : Decimal
        Sum of absolute values of all negative amounts (>= 0).
    """

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    transaction_count: int = Field(ge=0)
    total_income: Decimal = Field(ge=0)
    total_expenses: Decimal = Field(ge=0)


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
    summary : ParsedMonthSummary
        Aggregated statistics for this month.
    """

    year: int
    month: int
    transactions: list[ParsedTransaction]
    summary: ParsedMonthSummary


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
