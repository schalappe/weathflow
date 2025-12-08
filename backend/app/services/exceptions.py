"""Custom exceptions for CSV parsing operations."""


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
    partial_results : list
        Successfully categorized results before the failure.

    Attributes
    ----------
    failed_ids : list[int]
        IDs of failed transactions for retry logic.
    partial_results : list
        Partial results to preserve successful categorizations.
    """

    def __init__(self, failed_ids: list[int], partial_results: list[dict[str, str]]) -> None:
        self.failed_ids = failed_ids
        self.partial_results = partial_results
        super().__init__(f"Failed to categorize {len(failed_ids)} transactions")
