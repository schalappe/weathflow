"""Tests for CategoryMapping class and categorization prompt."""

import unittest

from app.db.enums import MoneyMapType
from app.services.categorization_prompt import CATEGORIZATION_SYSTEM_PROMPT
from app.services.category_mapping import CategoryMapping


class TestCategoryMappingDeterministicCategory(unittest.TestCase):
    """Tests for get_deterministic_category method."""

    def test_returns_correct_mapping_for_known_pair(self) -> None:
        """Should return correct Money Map category for known Bankin' pair."""
        result = CategoryMapping.get_deterministic_category("Alimentation & Restau.", "Supermarché / Epicerie")

        self.assertEqual(result, (MoneyMapType.CORE, "Groceries"))

    def test_returns_none_for_unknown_pair(self) -> None:
        """Should return None for unknown Bankin' category pair."""
        result = CategoryMapping.get_deterministic_category("Unknown Category", "Unknown Subcategory")

        self.assertIsNone(result)

    def test_returns_excluded_for_internal_transfers(self) -> None:
        """Should return EXCLUDED for internal transfer mappings."""
        result = CategoryMapping.get_deterministic_category("Entrées d'argent", "Virements internes")

        self.assertEqual(result, (MoneyMapType.EXCLUDED, ""))


class TestCategoryMappingInternalTransfer(unittest.TestCase):
    """Tests for is_internal_transfer method."""

    def test_detects_virement_interne(self) -> None:
        """Should detect 'virement interne' in description."""
        result = CategoryMapping.is_internal_transfer("Virement interne vers Livret A")

        self.assertTrue(result)

    def test_returns_false_for_regular_transaction(self) -> None:
        """Should return False for regular transaction descriptions."""
        result = CategoryMapping.is_internal_transfer("NETFLIX.COM")

        self.assertFalse(result)

    def test_case_insensitive_detection(self) -> None:
        """Should detect internal transfer regardless of case."""
        result = CategoryMapping.is_internal_transfer("VIREMENT INTERNE")

        self.assertTrue(result)

    def test_detects_vir_interne_abbreviation(self) -> None:
        """Should detect abbreviated 'vir interne' form."""
        result = CategoryMapping.is_internal_transfer("Vir interne CEL")

        self.assertTrue(result)


class TestCategorizationPrompt(unittest.TestCase):
    """Tests for categorization system prompt."""

    def test_prompt_is_non_empty_string(self) -> None:
        """Should be a non-empty string constant."""
        self.assertIsInstance(CATEGORIZATION_SYSTEM_PROMPT, str)
        self.assertGreater(len(CATEGORIZATION_SYSTEM_PROMPT), 100)

    def test_prompt_contains_money_map_categories(self) -> None:
        """Should contain all Money Map category names."""
        self.assertIn("INCOME", CATEGORIZATION_SYSTEM_PROMPT)
        self.assertIn("CORE", CATEGORIZATION_SYSTEM_PROMPT)
        self.assertIn("CHOICE", CATEGORIZATION_SYSTEM_PROMPT)
        self.assertIn("COMPOUND", CATEGORIZATION_SYSTEM_PROMPT)
        self.assertIn("EXCLUDED", CATEGORIZATION_SYSTEM_PROMPT)

    def test_prompt_contains_json_format_instruction(self) -> None:
        """Should include JSON output format instructions."""
        self.assertIn("money_map_type", CATEGORIZATION_SYSTEM_PROMPT)
        self.assertIn("money_map_subcategory", CATEGORIZATION_SYSTEM_PROMPT)
