"""Pydantic models for parsed CSV data and categorization."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.enums import SCORE_TO_LABEL, MoneyMapType, ScoreLabel


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


class TransactionInput(FrozenModel):
    """
    Transaction data to be categorized by the Claude API.

    This model represents the input to the categorization service,
    containing all fields needed for accurate classification.

    Attributes
    ----------
    id : int
        Unique identifier for the transaction.
    date : str
        Transaction date in string format.
    description : str
        Transaction description (merchant name, payment details).
    amount : float
        Transaction amount (positive for income, negative for expenses).
    bankin_category : str
        Original Bankin' category.
    bankin_subcategory : str
        Original Bankin' subcategory.
    """

    id: int
    date: str
    description: str
    amount: float
    bankin_category: str
    bankin_subcategory: str


class CategorizationResult(FrozenModel):
    """
    Result of categorizing a single transaction.

    Attributes
    ----------
    id : int
        Transaction ID matching the input.
    money_map_type : MoneyMapType
        Assigned Money Map category (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED).
    money_map_subcategory : str
        Specific subcategory within the Money Map type.
    confidence : float
        Confidence score between 0.0 and 1.0 (1.0 = certain).
    """

    id: int
    money_map_type: MoneyMapType
    money_map_subcategory: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class CachedCategorization(FrozenModel):
    """
    Cached categorization result for recurring transaction patterns.

    Stores the categorization result along with usage statistics.

    Attributes
    ----------
    money_map_type : MoneyMapType
        Cached Money Map category.
    money_map_subcategory : str
        Cached subcategory.
    confidence : float
        Original confidence score when cached.
    hit_count : int
        Number of times this cache entry has been used.
    """

    money_map_type: MoneyMapType
    money_map_subcategory: str
    confidence: float = Field(ge=0.0, le=1.0)
    hit_count: int = Field(ge=0, default=0)


class MonthStats(FrozenModel):
    """
    Complete statistics for a month's budget health.

    Contains aggregated totals, calculated percentages, and the Money Map score
    based on the 50/30/20 framework thresholds.

    Attributes
    ----------
    total_income : float
        Sum of all income transactions.
    total_core : float
        Sum of core expenses (absolute value).
    total_choice : float
        Sum of choice expenses (absolute value).
    total_compound : float
        Derived: income - core - choice (can be negative if overspent).
    core_percentage : float
        Core spending as percentage of income (rounded to 1 decimal).
    choice_percentage : float
        Choice spending as percentage of income (rounded to 1 decimal).
    compound_percentage : float
        Compound (savings) as percentage of income (rounded to 1 decimal).
    score : int
        Money Map score (0-3) based on thresholds met.
    score_label : ScoreLabel
        Human-readable label for the score.
    """

    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int = Field(ge=0, le=3)
    score_label: ScoreLabel

    @model_validator(mode="after")
    def validate_score_label_consistency(self) -> "MonthStats":
        """Ensure score and score_label match."""
        expected_label = SCORE_TO_LABEL[self.score]
        if self.score_label != expected_label:
            raise ValueError(f"score_label {self.score_label.value} does not match score {self.score}")
        return self
