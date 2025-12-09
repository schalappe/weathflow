"""Pydantic models for transaction categorization operations."""

from pydantic import Field

from app.db.enums import MoneyMapType
from app.services.dto._base import FrozenModel


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
