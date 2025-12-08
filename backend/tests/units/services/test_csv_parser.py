"""Tests for BankinCSVParser class."""

import unittest
from datetime import date
from decimal import Decimal

from app.services.csv_parser import BankinCSVParser
from app.services.exceptions import InvalidFormatError, MissingColumnsError, RowParseError


class TestBankinCSVParserValidCSV(unittest.TestCase):
    """Tests for parsing valid CSV data."""

    def setUp(self) -> None:
        """Create parser instance for each test."""
        self.parser = BankinCSVParser()

    def test_parse_single_transaction(self) -> None:
        """Should parse a valid CSV with a single transaction."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"31/10/2025";"Salary";"Checking";"2500,00";"Income";"Salary";"";"Oui"\n'
        )

        result = self.parser.parse(csv_content)

        self.assertEqual(result.total_transactions, 1)
        self.assertIn("2025-10", result.months)

        transaction = result.months["2025-10"].transactions[0]
        self.assertEqual(transaction.date, date(2025, 10, 31))
        self.assertEqual(transaction.description, "Salary")
        self.assertEqual(transaction.account, "Checking")
        self.assertEqual(transaction.amount, Decimal("2500.00"))
        self.assertEqual(transaction.bankin_category, "Income")
        self.assertEqual(transaction.bankin_subcategory, "Salary")
        self.assertIsNone(transaction.note)
        self.assertTrue(transaction.is_pointed)

    def test_parse_multiple_months(self) -> None:
        """Should group transactions by month and sort chronologically."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"15/10/2025";"October expense";"Checking";"-50,00";"Food";"Restaurant";"";"Non"\n'
            '"20/09/2025";"September expense";"Checking";"-30,00";"Food";"Groceries";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        self.assertEqual(result.total_transactions, 2)
        month_keys = list(result.months.keys())
        self.assertEqual(month_keys, ["2025-09", "2025-10"])

    def test_french_decimal_format_with_comma(self) -> None:
        """Should parse French decimal format with comma separator."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"01/01/2025";"Test";"Account";"1234,56";"Cat";"Sub";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        self.assertEqual(result.months["2025-01"].transactions[0].amount, Decimal("1234.56"))

    def test_month_grouping_and_chronological_sorting(self) -> None:
        """Should sort months chronologically with oldest first."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"15/12/2025";"December";"Account";"100,00";"Cat";"Sub";"";"Non"\n'
            '"10/01/2025";"January";"Account";"200,00";"Cat";"Sub";"";"Non"\n'
            '"20/06/2025";"June";"Account";"300,00";"Cat";"Sub";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        month_keys = list(result.months.keys())
        self.assertEqual(month_keys, ["2025-01", "2025-06", "2025-12"])


class TestBankinCSVParserErrors(unittest.TestCase):
    """Tests for error handling."""

    def setUp(self) -> None:
        """Create parser instance for each test."""
        self.parser = BankinCSVParser()

    def test_empty_file_raises_invalid_format_error(self) -> None:
        """Should raise InvalidFormatError for empty file."""
        with self.assertRaises(InvalidFormatError):
            self.parser.parse("")

    def test_missing_columns_raises_missing_columns_error(self) -> None:
        """Should raise MissingColumnsError with list of missing columns."""
        csv_content = 'Date;Description;Compte\n"01/01/2025";"Test";"Account"\n'

        with self.assertRaises(MissingColumnsError) as context:
            self.parser.parse(csv_content)

        self.assertIn("Montant", context.exception.missing)
        self.assertIn("Catégorie", context.exception.missing)

    def test_invalid_date_raises_row_parse_error_with_line_number(self) -> None:
        """Should raise RowParseError with line number for invalid date."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"99/99/2025";"Test";"Account";"100,00";"Cat";"Sub";"";"Non"\n'
        )

        with self.assertRaises(RowParseError) as context:
            self.parser.parse(csv_content)

        self.assertEqual(context.exception.line_number, 2)

    def test_invalid_amount_raises_row_parse_error_with_line_number(self) -> None:
        """Should raise RowParseError with line number for invalid amount."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"01/01/2025";"Test";"Account";"not_a_number";"Cat";"Sub";"";"Non"\n'
        )

        with self.assertRaises(RowParseError) as context:
            self.parser.parse(csv_content)

        self.assertEqual(context.exception.line_number, 2)


class TestBankinCSVParserSummary(unittest.TestCase):
    """Tests for summary calculation."""

    def setUp(self) -> None:
        """Create parser instance for each test."""
        self.parser = BankinCSVParser()

    def test_income_and_expenses_calculated_correctly(self) -> None:
        """Should calculate income from positive and expenses from negative amounts."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"15/10/2025";"Salary";"Checking";"3000,00";"Income";"Salary";"";"Oui"\n'
            '"16/10/2025";"Rent";"Checking";"-1200,00";"Housing";"Rent";"";"Non"\n'
            '"17/10/2025";"Groceries";"Checking";"-150,50";"Food";"Groceries";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)
        summary = result.months["2025-10"].summary

        self.assertEqual(summary.transaction_count, 3)
        self.assertEqual(summary.total_income, Decimal("3000.00"))
        self.assertEqual(summary.total_expenses, Decimal("1350.50"))


class TestBankinCSVParserPointedField(unittest.TestCase):
    """Tests for Pointée boolean conversion."""

    def setUp(self) -> None:
        """Create parser instance for each test."""
        self.parser = BankinCSVParser()

    def test_oui_converts_to_true_case_insensitive(self) -> None:
        """Should convert 'Oui', 'oui', 'OUI' to True."""
        for value in ["Oui", "oui", "OUI"]:
            csv_content = (
                "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
                f'"01/01/2025";"Test";"Account";"100,00";"Cat";"Sub";"";"{value}"\n'
            )

            result = self.parser.parse(csv_content)

            self.assertTrue(result.months["2025-01"].transactions[0].is_pointed)

    def test_non_converts_to_false(self) -> None:
        """Should convert 'Non' and other values to False."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"01/01/2025";"Test";"Account";"100,00";"Cat";"Sub";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        self.assertFalse(result.months["2025-01"].transactions[0].is_pointed)


class TestBankinCSVParserEdgeCases(unittest.TestCase):
    """Tests for edge cases."""

    def setUp(self) -> None:
        """Create parser instance for each test."""
        self.parser = BankinCSVParser()

    def test_multi_year_file_spanning_december_to_january(self) -> None:
        """Should handle files spanning multiple years correctly."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"15/01/2025";"January";"Account";"100,00";"Cat";"Sub";"";"Non"\n'
            '"20/12/2024";"December";"Account";"200,00";"Cat";"Sub";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        month_keys = list(result.months.keys())
        self.assertEqual(month_keys, ["2024-12", "2025-01"])
        self.assertEqual(result.total_transactions, 2)

    def test_period_decimal_format_also_accepted(self) -> None:
        """Should accept period decimal format for robustness."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"01/01/2025";"Test";"Account";"1234.56";"Cat";"Sub";"";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        self.assertEqual(result.months["2025-01"].transactions[0].amount, Decimal("1234.56"))

    def test_note_field_preserved_when_provided(self) -> None:
        """Should preserve non-empty note field."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"01/01/2025";"Test";"Account";"100,00";"Cat";"Sub";"Important note";"Non"\n'
        )

        result = self.parser.parse(csv_content)

        self.assertEqual(result.months["2025-01"].transactions[0].note, "Important note")

    def test_bytes_input_decoded_as_utf8(self) -> None:
        """Should accept bytes input and decode as UTF-8."""
        csv_content = (
            "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée\n"
            '"01/01/2025";"Café";"Account";"10,00";"Cat";"Sub";"";"Non"\n'
        )

        result = self.parser.parse(csv_content.encode("utf-8"))

        self.assertEqual(result.total_transactions, 1)
        self.assertEqual(result.months["2025-01"].transactions[0].description, "Café")
