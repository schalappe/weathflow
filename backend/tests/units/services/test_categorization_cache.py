"""Tests for CategorizationCache class."""

import tempfile
import unittest
from pathlib import Path

from app.db.enums import MoneyMapType
from app.services.categorization_cache import CategorizationCache


class TestCategorizationCacheNormalizeKey(unittest.TestCase):
    """Tests for key normalization."""

    def test_normalize_key_handles_date_suffix(self) -> None:
        """Should remove date patterns like '12/05' from description."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))

        key = cache._normalize_key("NETFLIX.COM 12/05")

        self.assertEqual(key, "netflix.com")

    def test_normalize_key_handles_reference_suffix(self) -> None:
        """Should remove reference patterns like 'REF:ABC123'."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))

        key = cache._normalize_key("PAYMENT REF:XYZ789")

        self.assertEqual(key, "payment")

    def test_normalize_key_lowercases_and_strips(self) -> None:
        """Should lowercase and strip whitespace."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))

        key = cache._normalize_key("  NETFLIX.COM  ")

        self.assertEqual(key, "netflix.com")


class TestCategorizationCacheGet(unittest.TestCase):
    """Tests for cache get operations."""

    def test_get_returns_none_for_cache_miss(self) -> None:
        """Should return None when description not in cache."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))

        result = cache.get("Unknown Transaction")

        self.assertIsNone(result)

    def test_get_returns_cached_categorization(self) -> None:
        """Should return CachedCategorization for cache hit."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))
        cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)

        result = cache.get("NETFLIX.COM")

        self.assertIsNotNone(result)
        self.assertEqual(result.money_map_type, MoneyMapType.CHOICE)  # type: [union-attr]
        self.assertEqual(result.money_map_subcategory, "Subscription services")  # type: [union-attr]

    def test_get_increments_hit_count(self) -> None:
        """Should increment hit_count on each get."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))
        cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)

        cache.get("NETFLIX.COM")
        result = cache.get("NETFLIX.COM")

        self.assertEqual(result.hit_count, 2)  # type: [union-attr]


class TestCategorizationCachePut(unittest.TestCase):
    """Tests for cache put operations."""

    def test_put_stores_high_confidence_result(self) -> None:
        """Should store result when confidence >= 0.95."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))

        result = cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.95)

        self.assertTrue(result)
        self.assertIsNotNone(cache.get("NETFLIX.COM"))

    def test_put_rejects_low_confidence_result(self) -> None:
        """Should reject result when confidence < 0.95."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))

        result = cache.put("Unknown Store", MoneyMapType.CHOICE, "Shopping", 0.80)

        self.assertFalse(result)
        self.assertIsNone(cache.get("Unknown Store"))


class TestCategorizationCachePersistence(unittest.TestCase):
    """Tests for cache persistence."""

    def test_save_and_load_roundtrip(self) -> None:
        """Should persist cache to file and reload correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Save cache
            cache1 = CategorizationCache(cache_path=cache_path)
            cache1.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)
            cache1.save()

            # Load in new instance
            cache2 = CategorizationCache(cache_path=cache_path)
            result = cache2.get("NETFLIX.COM")

            self.assertIsNotNone(result)
            self.assertEqual(result.money_map_type, MoneyMapType.CHOICE)  # type: [union-attr]


class TestCategorizationCacheClear(unittest.TestCase):
    """Tests for cache clear operation."""

    def test_clear_empties_cache(self) -> None:
        """Should remove all entries from cache."""
        cache = CategorizationCache(cache_path=Path(tempfile.mktemp()))
        cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)
        cache.put("SPOTIFY.COM", MoneyMapType.CHOICE, "Subscription services", 0.97)

        cache.clear()

        self.assertIsNone(cache.get("NETFLIX.COM"))
        self.assertIsNone(cache.get("SPOTIFY.COM"))
