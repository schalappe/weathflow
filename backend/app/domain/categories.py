"""Single source of truth for Money Map category and subcategory definitions."""

from app.db.enums import MoneyMapType

# ##>: Canonical subcategory list per MoneyMapType. All validation uses this dictionary.
ALLOWED_SUBCATEGORIES: dict[MoneyMapType, list[str]] = {
    MoneyMapType.INCOME: ["Job", "Investments", "Reimbursements", "Other"],
    MoneyMapType.CORE: [
        "Housing",
        "Groceries",
        "Utilities",
        "Healthcare",
        "Transportation",
        "Basic clothing",
        "Phone and internet",
        "Insurance",
        "Debt payments",
    ],
    MoneyMapType.CHOICE: [
        "Dining out",
        "Entertainment",
        "Travel and vacations",
        "Electronics and gadgets",
        "Hobby supplies",
        "Fancy clothing",
        "Subscription services",
        "Home decor",
        "Gifts",
    ],
    MoneyMapType.COMPOUND: ["Emergency Fund", "Education Fund", "Investments", "Other"],
    MoneyMapType.EXCLUDED: [],
}


def get_allowed_subcategories(money_map_type: MoneyMapType) -> list[str]:
    """
    Return allowed subcategories for a given MoneyMapType.

    Parameters
    ----------
    money_map_type : MoneyMapType
        The Money Map type.

    Returns
    -------
    list[str]
        List of allowed subcategories (empty for EXCLUDED).
    """
    return ALLOWED_SUBCATEGORIES.get(money_map_type, [])
