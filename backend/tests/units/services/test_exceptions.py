"""Tests for CSV parsing exceptions."""

import unittest

from app.services.exceptions import (
    CSVParseError,
    InvalidFormatError,
    MissingColumnsError,
    RowParseError,
)


class TestCSVParseErrorHierarchy(unittest.TestCase):
    """Tests for exception inheritance structure."""

    def test_invalid_format_error_inherits_from_csv_parse_error(self) -> None:
        """InvalidFormatError should inherit from CSVParseError."""
        self.assertTrue(issubclass(InvalidFormatError, CSVParseError))

    def test_missing_columns_error_inherits_from_csv_parse_error(self) -> None:
        """MissingColumnsError should inherit from CSVParseError."""
        self.assertTrue(issubclass(MissingColumnsError, CSVParseError))

    def test_row_parse_error_inherits_from_csv_parse_error(self) -> None:
        """RowParseError should inherit from CSVParseError."""
        self.assertTrue(issubclass(RowParseError, CSVParseError))


class TestMissingColumnsError(unittest.TestCase):
    """Tests for MissingColumnsError behavior."""

    def test_stores_missing_columns_as_attribute(self) -> None:
        """Should store the missing columns list as an attribute."""
        missing = ["Date", "Montant", "Description"]
        error = MissingColumnsError(missing)

        self.assertEqual(error.missing, missing)

    def test_message_contains_comma_separated_columns(self) -> None:
        """Should format message with comma-separated column names."""
        error = MissingColumnsError(["Date", "Montant"])

        self.assertEqual(str(error), "Missing required columns: Date, Montant")

    def test_single_missing_column_formats_correctly(self) -> None:
        """Should format correctly with a single missing column."""
        error = MissingColumnsError(["Catégorie"])

        self.assertEqual(str(error), "Missing required columns: Catégorie")

    def test_can_be_caught_as_csv_parse_error(self) -> None:
        """Should be catchable as CSVParseError."""
        with self.assertRaises(CSVParseError):
            raise MissingColumnsError(["Date"])


class TestRowParseError(unittest.TestCase):
    """Tests for RowParseError behavior."""

    def test_stores_line_number_as_attribute(self) -> None:
        """Should store the line number as an attribute."""
        error = RowParseError("Invalid date format", 5)

        self.assertEqual(error.line_number, 5)

    def test_message_includes_line_number_prefix(self) -> None:
        """Should format message with line number prefix."""
        error = RowParseError("Invalid amount", 10)

        self.assertEqual(str(error), "Line 10: Invalid amount")

    def test_preserves_original_message_in_output(self) -> None:
        """Should include the original message after the line prefix."""
        original_message = "Could not parse date: 99/99/2025"
        error = RowParseError(original_message, 3)

        self.assertIn(original_message, str(error))

    def test_can_be_caught_as_csv_parse_error(self) -> None:
        """Should be catchable as CSVParseError."""
        with self.assertRaises(CSVParseError):
            raise RowParseError("Error", 1)


class TestInvalidFormatError(unittest.TestCase):
    """Tests for InvalidFormatError behavior."""

    def test_can_be_instantiated_without_message(self) -> None:
        """Should allow instantiation without a custom message."""
        error = InvalidFormatError()

        self.assertIsInstance(error, CSVParseError)

    def test_can_be_instantiated_with_message(self) -> None:
        """Should allow instantiation with a custom message."""
        error = InvalidFormatError("File is empty")

        self.assertEqual(str(error), "File is empty")
