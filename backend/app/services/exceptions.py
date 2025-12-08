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
