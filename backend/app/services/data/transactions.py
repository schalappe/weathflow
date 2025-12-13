"""Service functions for transaction operations."""

from loguru import logger

from app.db.enums import MoneyMapType
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.month import MonthRepository
from app.repositories.transaction import TransactionRepository
from app.services.calculation.service import calculate_and_update_month
from app.services.exceptions import InvalidSubcategoryError, TransactionNotFoundError

# ##>: Allowed subcategories per MoneyMapType from requirements.md.
ALLOWED_SUBCATEGORIES: dict[MoneyMapType, list[str]] = {
    MoneyMapType.INCOME: ["Job"],
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


def validate_subcategory(money_map_type: MoneyMapType, subcategory: str | None) -> str | None:
    """
    Validate subcategory against allowed values for the given type.

    Parameters
    ----------
    money_map_type : MoneyMapType
        The Money Map type.
    subcategory : str | None
        The subcategory to validate.

    Returns
    -------
    str | None
        The validated subcategory, or None for EXCLUDED type.

    Raises
    ------
    InvalidSubcategoryError
        If subcategory is not valid for the given type.
    """
    # ##>: EXCLUDED type auto-clears subcategory to null.
    if money_map_type == MoneyMapType.EXCLUDED:
        return None

    allowed = ALLOWED_SUBCATEGORIES.get(money_map_type, [])

    # ##>: Allow None subcategory for any type (optional field).
    if subcategory is None:
        return None

    if subcategory not in allowed:
        raise InvalidSubcategoryError(money_map_type.value, subcategory)

    return subcategory


def update_transaction_category(
    month_repo: MonthRepository,
    transaction_repo: TransactionRepository,
    transaction_id: int,
    money_map_type: MoneyMapType,
    money_map_subcategory: str | None,
) -> tuple[Transaction, Month]:
    """
    Update transaction category and recalculate month stats.

    Parameters
    ----------
    month_repo : MonthRepository
        Repository for month data access.
    transaction_repo : TransactionRepository
        Repository for transaction data access.
    transaction_id : int
        ID of the transaction to update.
    money_map_type : MoneyMapType
        New Money Map type.
    money_map_subcategory : str | None
        New subcategory (validated against allowed values).

    Returns
    -------
    tuple[Transaction, Month]
        Updated transaction and recalculated month.

    Raises
    ------
    TransactionNotFoundError
        If transaction does not exist.
    InvalidSubcategoryError
        If subcategory is invalid for the type.
    """
    transaction = transaction_repo.get_by_id(transaction_id)
    if transaction is None:
        raise TransactionNotFoundError(transaction_id)

    # ##>: Validate and normalize subcategory before update.
    validated_subcategory = validate_subcategory(money_map_type, money_map_subcategory)

    try:
        transaction.money_map_type = money_map_type.value
        transaction.money_map_subcategory = validated_subcategory
        transaction.is_manually_corrected = True

        # ##>: Flush transaction changes so aggregation query sees updated values.
        transaction_repo.flush()

        # ##>: Recalculate month stats using existing service.
        updated_month = calculate_and_update_month(month_repo, transaction_repo, transaction.month_id)

        logger.info(
            "Updated transaction %d: type=%s, subcategory=%s, month_id=%d",
            transaction_id,
            money_map_type.value,
            validated_subcategory,
            transaction.month_id,
        )

        return transaction, updated_month
    except Exception:
        # ##>: Rollback on any failure to maintain session consistency.
        month_repo.rollback()
        raise
