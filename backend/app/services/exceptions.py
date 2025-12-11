"""Custom exceptions for CSV parsing, transaction categorization, and score calculation operations."""

from typing import Any


class CSVParseError(Exception):
    """
    Base exception for all CSV parsing errors.

    All CSV-specific exceptions inherit from this class, allowing callers
    to catch all parsing errors with a single except clause.
    """


class InvalidFormatError(CSVParseError):
    """
    Raised when CSV format is invalid.

    This includes empty files or files without a header row.
    """


class MissingColumnsError(CSVParseError):
    """
    Raised when required columns are missing from the CSV header.

    Parameters
    ----------
    missing : list[str]
        List of column names that are missing from the CSV.

    Attributes
    ----------
    missing : list[str]
        The list of missing column names for programmatic access.
    """

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Missing required columns: {', '.join(missing)}")


class RowParseError(CSVParseError):
    """
    Raised when a specific row cannot be parsed.

    Parameters
    ----------
    message : str
        Description of the parsing error.
    line_number : int
        The 1-based line number where the error occurred (header is line 1).

    Attributes
    ----------
    line_number : int
        The line number for programmatic access.
    """

    def __init__(self, message: str, line_number: int) -> None:
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}")


class CategorizationError(Exception):
    """
    Base exception for all transaction categorization errors.

    All categorization-specific exceptions inherit from this class, allowing
    callers to catch all categorization errors with a single except clause.
    """


class APIConnectionError(CategorizationError):
    """
    Raised when Claude API is unreachable after all retries.

    Parameters
    ----------
    retry_count : int
        Number of retry attempts made before giving up.

    Attributes
    ----------
    retry_count : int
        The number of retries for programmatic access.
    """

    def __init__(self, retry_count: int) -> None:
        self.retry_count = retry_count
        super().__init__(f"Claude API unreachable after {retry_count} retries")


class InvalidResponseError(CategorizationError):
    """
    Raised when Claude API returns unparseable JSON response.

    Parameters
    ----------
    raw_response : str
        The raw response text that could not be parsed.

    Attributes
    ----------
    raw_response : str
        The raw response for debugging and logging.
    """

    def __init__(self, raw_response: str) -> None:
        self.raw_response = raw_response
        # ##>: Truncate response in message for readability but keep full in attribute.
        preview = raw_response[:100] + "..." if len(raw_response) > 100 else raw_response
        super().__init__(f"Invalid JSON response from Claude API: {preview}")


class BatchCategorizationError(CategorizationError):
    """
    Raised when some transactions in a batch fail to categorize.

    Parameters
    ----------
    failed_ids : list[int]
        IDs of transactions that failed to categorize.
    partial_results : list[dict[str, Any]]
        Successfully categorized results before the failure.

    Attributes
    ----------
    failed_ids : list[int]
        IDs of failed transactions for retry logic.
    partial_results : list[dict[str, Any]]
        Partial results to preserve successful categorizations.
    """

    def __init__(self, failed_ids: list[int], partial_results: list[dict[str, Any]]) -> None:
        self.failed_ids = failed_ids
        self.partial_results = partial_results
        super().__init__(f"Failed to categorize {len(failed_ids)} transactions")


class ScoreCalculationError(Exception):
    """
    Base exception for all score calculation errors.

    All score calculation-specific exceptions inherit from this class, allowing
    callers to catch all score calculation errors with a single except clause.
    """


class MonthNotFoundError(ScoreCalculationError):
    """
    Raised when a month record is not found in the database.

    Parameters
    ----------
    month_id : int
        The ID of the month that was not found.

    Attributes
    ----------
    month_id : int
        The month ID for programmatic access.
    """

    def __init__(self, month_id: int) -> None:
        self.month_id = month_id
        super().__init__(f"Month with id={month_id} not found")


class TransactionAggregationError(ScoreCalculationError):
    """
    Raised when transaction aggregation query fails.

    Parameters
    ----------
    month_id : int
        The ID of the month being aggregated.
    reason : str
        Description of the failure.

    Attributes
    ----------
    month_id : int
        The month ID for programmatic access.
    reason : str
        The failure reason for debugging.
    """

    def __init__(self, month_id: int, reason: str) -> None:
        self.month_id = month_id
        self.reason = reason
        super().__init__(f"Failed to aggregate transactions for month {month_id}: {reason}")


class ScorePersistenceError(ScoreCalculationError):
    """
    Raised when score calculation succeeds but database update fails.

    Parameters
    ----------
    month_id : int
        The ID of the month that could not be updated.

    Attributes
    ----------
    month_id : int
        The month ID for programmatic access.
    """

    def __init__(self, month_id: int) -> None:
        self.month_id = month_id
        super().__init__(f"Failed to persist score calculation for month {month_id}")


class UploadError(Exception):
    """
    Base exception for all upload operation errors.

    All upload-specific exceptions inherit from this class, allowing callers
    to catch all upload errors with a single except clause.
    """


class MonthDataError(Exception):
    """
    Base exception for all month data retrieval errors.

    All month data-specific exceptions inherit from this class, allowing callers
    to catch all month data errors with a single except clause.
    """


class MonthQueryError(MonthDataError):
    """
    Raised when a database query for months fails.

    Parameters
    ----------
    reason : str
        Description of the failure.

    Attributes
    ----------
    reason : str
        The failure reason for debugging.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Failed to query months: {reason}")


class TransactionQueryError(MonthDataError):
    """
    Raised when a transaction query fails.

    Parameters
    ----------
    month_id : int
        The ID of the month being queried.
    reason : str
        Description of the failure.

    Attributes
    ----------
    month_id : int
        The month ID for programmatic access.
    reason : str
        The failure reason for debugging.
    """

    def __init__(self, month_id: int, reason: str) -> None:
        self.month_id = month_id
        self.reason = reason
        super().__init__(f"Failed to query transactions for month {month_id}: {reason}")


class InvalidMonthFormatError(UploadError):
    """
    Raised when month format is not YYYY-MM.

    Parameters
    ----------
    value : str
        The invalid month string that was provided.

    Attributes
    ----------
    value : str
        The invalid value for programmatic access.
    """

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Invalid month format: '{value}'. Expected YYYY-MM")


class NoTransactionsFoundError(UploadError):
    """Raised when CSV contains no transactions after parsing."""

    def __init__(self) -> None:
        super().__init__("No transactions found in the uploaded file")


class TransactionError(Exception):
    """
    Base exception for all transaction operation errors.

    All transaction-specific exceptions inherit from this class, allowing
    callers to catch all transaction errors with a single except clause.
    """


class TransactionNotFoundError(TransactionError):
    """
    Raised when a transaction record is not found in the database.

    Parameters
    ----------
    transaction_id : int
        The ID of the transaction that was not found.

    Attributes
    ----------
    transaction_id : int
        The transaction ID for programmatic access.
    """

    def __init__(self, transaction_id: int) -> None:
        self.transaction_id = transaction_id
        super().__init__(f"Transaction with id={transaction_id} not found")


class InvalidSubcategoryError(TransactionError):
    """
    Raised when subcategory is invalid for the given MoneyMapType.

    Parameters
    ----------
    money_map_type : str
        The Money Map type that was specified.
    subcategory : str
        The invalid subcategory value.

    Attributes
    ----------
    money_map_type : str
        The type for programmatic access.
    subcategory : str
        The invalid subcategory for programmatic access.
    """

    def __init__(self, money_map_type: str, subcategory: str) -> None:
        self.money_map_type = money_map_type
        self.subcategory = subcategory
        super().__init__(f"Invalid subcategory '{subcategory}' for type {money_map_type}")


class AdviceGenerationError(Exception):
    """
    Base exception for all advice generation errors.

    All advice-specific exceptions inherit from this class, allowing
    callers to catch all advice errors with a single except clause.
    """


class InsufficientDataError(AdviceGenerationError):
    """
    Raised when there is not enough historical data for advice generation.

    Parameters
    ----------
    min_months_required : int
        Minimum number of months required for advice generation.

    Attributes
    ----------
    min_months_required : int
        The minimum months required for programmatic access.
    """

    def __init__(self, min_months_required: int) -> None:
        self.min_months_required = min_months_required
        super().__init__(f"Advice generation requires at least {min_months_required} months of data")


class AdviceAPIError(AdviceGenerationError):
    """
    Raised when Claude API is unreachable or returns an error.

    Parameters
    ----------
    retry_count : int
        Number of retry attempts made before giving up.

    Attributes
    ----------
    retry_count : int
        The number of retries for programmatic access.
    """

    def __init__(self, retry_count: int) -> None:
        self.retry_count = retry_count
        super().__init__(f"Claude API unreachable after {retry_count} retries")


class AdviceParseError(AdviceGenerationError):
    """
    Raised when Claude API returns unparseable JSON response.

    Parameters
    ----------
    raw_response : str
        The raw response text that could not be parsed.

    Attributes
    ----------
    raw_response : str
        The raw response for debugging and logging.
    """

    def __init__(self, raw_response: str) -> None:
        self.raw_response = raw_response
        # ##>: Truncate response in message for readability but keep full in attribute.
        preview = raw_response[:100] + "..." if len(raw_response) > 100 else raw_response
        super().__init__(f"Invalid JSON response from Claude API: {preview}")


class AdviceQueryError(AdviceGenerationError):
    """
    Raised when a database query for advice fails.

    Parameters
    ----------
    month_id : int
        The ID of the month being queried.
    reason : str
        Description of the failure.

    Attributes
    ----------
    month_id : int
        The month ID for programmatic access.
    reason : str
        The failure reason for debugging.
    """

    def __init__(self, month_id: int, reason: str) -> None:
        self.month_id = month_id
        self.reason = reason
        super().__init__(f"Failed to query advice for month {month_id}: {reason}")
