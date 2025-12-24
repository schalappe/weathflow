"""Unit tests for MonthNotEligibleError exception."""

import unittest

from app.services.exceptions import AdviceGenerationError, MonthNotEligibleError


class TestMonthNotEligibleError(unittest.TestCase):
    """Tests for MonthNotEligibleError exception."""

    def test_stores_year_month_and_reason_attributes(self) -> None:
        """Exception stores year, month, and reason as attributes."""
        error = MonthNotEligibleError(year=2025, month=8, reason="Month is too old")

        self.assertEqual(error.year, 2025)
        self.assertEqual(error.month, 8)
        self.assertEqual(error.reason, "Month is too old")

    def test_message_formats_correctly(self) -> None:
        """Exception message includes year, month, and reason."""
        error = MonthNotEligibleError(year=2025, month=8, reason="Month is too old")

        self.assertIn("2025-08", str(error))
        self.assertIn("Month is too old", str(error))

    def test_inherits_from_advice_generation_error(self) -> None:
        """Exception can be caught as AdviceGenerationError."""
        with self.assertRaises(AdviceGenerationError):
            raise MonthNotEligibleError(year=2025, month=8, reason="Test")
