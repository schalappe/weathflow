"""Tests for Money Map enums."""

import unittest
from enum import Enum

from app.db.enums import MoneyMapType, ScoreLabel


class TestMoneyMapType(unittest.TestCase):
    """Tests for the MoneyMapType enum."""

    def test_values_are_correct_strings(self) -> None:
        """MoneyMapType should have the expected string values."""
        self.assertEqual(MoneyMapType.INCOME.value, "INCOME")
        self.assertEqual(MoneyMapType.CORE.value, "CORE")
        self.assertEqual(MoneyMapType.CHOICE.value, "CHOICE")
        self.assertEqual(MoneyMapType.COMPOUND.value, "COMPOUND")
        self.assertEqual(MoneyMapType.EXCLUDED.value, "EXCLUDED")

    def test_inherits_from_str_and_enum(self) -> None:
        """MoneyMapType should inherit from str and Enum for SQLite compatibility."""
        self.assertTrue(issubclass(MoneyMapType, str))
        self.assertTrue(issubclass(MoneyMapType, Enum))

        # ##>: String inheritance allows direct string comparison without .value.
        self.assertEqual(MoneyMapType.INCOME, "INCOME")


class TestScoreLabel(unittest.TestCase):
    """Tests for the ScoreLabel enum."""

    def test_values_match_expected_labels(self) -> None:
        """ScoreLabel should have human-readable string values."""
        self.assertEqual(ScoreLabel.POOR.value, "Poor")
        self.assertEqual(ScoreLabel.NEED_IMPROVEMENT.value, "Need Improvement")
        self.assertEqual(ScoreLabel.OKAY.value, "Okay")
        self.assertEqual(ScoreLabel.GREAT.value, "Great")

    def test_inherits_from_str_and_enum(self) -> None:
        """ScoreLabel should inherit from str and Enum for SQLite compatibility."""
        self.assertTrue(issubclass(ScoreLabel, str))
        self.assertTrue(issubclass(ScoreLabel, Enum))

        # ##>: String inheritance allows direct string comparison without .value.
        self.assertEqual(ScoreLabel.GREAT, "Great")


if __name__ == "__main__":
    unittest.main()
