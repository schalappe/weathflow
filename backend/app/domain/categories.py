"""Single source of truth for Money Map category and subcategory definitions."""

from collections.abc import Mapping
from types import MappingProxyType

from app.db.enums import MoneyMapType

# ##>: Canonical subcategory list per MoneyMapType. All validation uses this dictionary.
# ##>: Using MappingProxyType and tuples for immutability to prevent accidental modification.
ALLOWED_SUBCATEGORIES: Mapping[MoneyMapType, tuple[str, ...]] = MappingProxyType(
    {
        MoneyMapType.INCOME: ("Job", "Investments", "Reimbursements", "Other"),
        MoneyMapType.CORE: (
            "Housing",
            "Groceries",
            "Utilities",
            "Healthcare",
            "Transportation",
            "Basic clothing",
            "Phone and internet",
            "Insurance",
            "Debt payments",
        ),
        MoneyMapType.CHOICE: (
            "Dining out",
            "Entertainment",
            "Travel and vacations",
            "Electronics and gadgets",
            "Hobby supplies",
            "Fancy clothing",
            "Subscription services",
            "Home decor",
            "Gifts",
        ),
        MoneyMapType.COMPOUND: ("Emergency Fund", "Education Fund", "Investments", "Other"),
        MoneyMapType.EXCLUDED: (),
    }
)


def get_allowed_subcategories(money_map_type: MoneyMapType) -> tuple[str, ...]:
    """
    Return allowed subcategories for a given MoneyMapType.

    Parameters
    ----------
    money_map_type : MoneyMapType
        The Money Map type.

    Returns
    -------
    tuple[str, ...]
        Tuple of allowed subcategories (empty for EXCLUDED).
    """
    return ALLOWED_SUBCATEGORIES.get(money_map_type, ())


def is_valid_subcategory(money_map_type: MoneyMapType, subcategory: str) -> bool:
    """
    Check if a subcategory is valid for a given MoneyMapType.

    Parameters
    ----------
    money_map_type : MoneyMapType
        The Money Map type.
    subcategory : str
        The subcategory to validate.

    Returns
    -------
    bool
        True if the subcategory is valid for the type, False otherwise.
    """
    return subcategory in ALLOWED_SUBCATEGORIES.get(money_map_type, ())
