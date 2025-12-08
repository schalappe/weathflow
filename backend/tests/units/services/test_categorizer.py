"""Tests for TransactionCategorizer service."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import anthropic

from app.db.enums import MoneyMapType
from app.services.categorization_cache import CategorizationCache
from app.services.categorizer import TransactionCategorizer
from app.services.exceptions import (
    APIConnectionError,
    BatchCategorizationError,
    InvalidResponseError,
)
from app.services.schemas import TransactionInput


def _make_transaction(
    id: int,
    description: str = "Test Transaction",
    bankin_category: str = "Other",
    bankin_subcategory: str = "Other",
    amount: float = -50.0,
) -> TransactionInput:
    """Create a test transaction with defaults."""
    return TransactionInput(
        id=id,
        date="2025-01-15",
        description=description,
        amount=amount,
        bankin_category=bankin_category,
        bankin_subcategory=bankin_subcategory,
    )


class TestTransactionCategorizerCache(unittest.TestCase):
    """Tests for cache lookup pipeline."""

    def setUp(self) -> None:
        """Create categorizer with temp cache."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.categorizer._client = MagicMock()

    def test_returns_cached_result_without_api_call(self) -> None:
        """Should return cache hit without calling Claude API."""
        self.cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)
        transaction = _make_transaction(id=1, description="NETFLIX.COM 12/05")

        results = self.categorizer.categorize([transaction])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].money_map_type, MoneyMapType.CHOICE)
        self.assertEqual(results[0].money_map_subcategory, "Subscription services")
        self.categorizer._client.messages.create.assert_not_called()

    def test_cache_hit_preserves_transaction_id(self) -> None:
        """Should preserve original transaction ID in result."""
        self.cache.put("SPOTIFY.COM", MoneyMapType.CHOICE, "Subscription services", 0.99)
        transaction = _make_transaction(id=42, description="SPOTIFY.COM")

        results = self.categorizer.categorize([transaction])

        self.assertEqual(results[0].id, 42)


class TestTransactionCategorizerDeterministicRules(unittest.TestCase):
    """Tests for deterministic rules pipeline."""

    def setUp(self) -> None:
        """Create categorizer with mocked API client."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.categorizer._client = MagicMock()

    def test_internal_transfer_returns_excluded(self) -> None:
        """Should return EXCLUDED for internal transfer without API call."""
        transaction = _make_transaction(id=1, description="Virement interne vers Livret A")

        results = self.categorizer.categorize([transaction])

        self.assertEqual(results[0].money_map_type, MoneyMapType.EXCLUDED)
        self.assertEqual(results[0].confidence, 1.0)
        self.categorizer._client.messages.create.assert_not_called()

    def test_deterministic_mapping_returns_correct_category(self) -> None:
        """Should return correct category for known Bankin' mapping."""
        transaction = _make_transaction(
            id=1,
            description="CARREFOUR",
            bankin_category="Alimentation & Restau.",
            bankin_subcategory="Supermarché / Epicerie",
        )

        results = self.categorizer.categorize([transaction])

        self.assertEqual(results[0].money_map_type, MoneyMapType.CORE)
        self.assertEqual(results[0].money_map_subcategory, "Groceries")
        self.categorizer._client.messages.create.assert_not_called()


class TestTransactionCategorizerAPI(unittest.TestCase):
    """Tests for Claude API integration."""

    def setUp(self) -> None:
        """Create categorizer with mocked API client."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.mock_client = MagicMock()
        self.categorizer._client = self.mock_client

    def test_calls_api_for_unknown_transaction(self) -> None:
        """Should call Claude API for transactions not in cache or rules."""
        transaction = _make_transaction(
            id=1,
            description="UNKNOWN STORE XYZ",
            bankin_category="Unknown",
            bankin_subcategory="Unknown",
        )

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='[{"id": 1, "money_map_type": "CHOICE", "money_map_subcategory": "Shopping", "confidence": 0.85}]'
            )
        ]
        self.mock_client.messages.create.return_value = mock_response

        results = self.categorizer.categorize([transaction])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].money_map_type, MoneyMapType.CHOICE)
        self.assertEqual(results[0].money_map_subcategory, "Shopping")
        self.assertEqual(results[0].confidence, 0.85)
        self.mock_client.messages.create.assert_called_once()

    def test_api_response_defaults_confidence_to_one(self) -> None:
        """Should default confidence to 1.0 if missing from API response."""
        transaction = _make_transaction(id=1, description="UNKNOWN STORE")

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"id": 1, "money_map_type": "CORE", "money_map_subcategory": "Groceries"}]')
        ]
        self.mock_client.messages.create.return_value = mock_response

        results = self.categorizer.categorize([transaction])

        self.assertEqual(results[0].confidence, 1.0)


class TestTransactionCategorizerRetry(unittest.TestCase):
    """Tests for retry behavior on API errors."""

    def setUp(self) -> None:
        """Create categorizer with mocked API client."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.mock_client = MagicMock()
        self.categorizer._client = self.mock_client

    def test_api_connection_error_raises_with_retry_count(self) -> None:
        """Should raise APIConnectionError with retry count on connection failure."""
        transaction = _make_transaction(id=1, description="UNKNOWN STORE")
        self.mock_client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())

        with self.assertRaises(APIConnectionError) as context:
            self.categorizer.categorize([transaction])

        self.assertEqual(context.exception.retry_count, 3)

    def test_rate_limit_error_raises_api_connection_error(self) -> None:
        """Should raise APIConnectionError on rate limit after retries."""
        transaction = _make_transaction(id=1, description="UNKNOWN STORE")
        mock_response = MagicMock()
        mock_response.status_code = 429
        self.mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded", response=mock_response, body=None
        )

        with self.assertRaises(APIConnectionError) as context:
            self.categorizer.categorize([transaction])

        self.assertEqual(context.exception.retry_count, 3)


class TestTransactionCategorizerResponseParsing(unittest.TestCase):
    """Tests for API response parsing."""

    def setUp(self) -> None:
        """Create categorizer with mocked API client."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.mock_client = MagicMock()
        self.categorizer._client = self.mock_client

    def test_invalid_json_raises_invalid_response_error(self) -> None:
        """Should raise InvalidResponseError on malformed JSON."""
        transaction = _make_transaction(id=1, description="UNKNOWN STORE")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json {{{")]
        self.mock_client.messages.create.return_value = mock_response

        with self.assertRaises(InvalidResponseError) as context:
            self.categorizer.categorize([transaction])

        self.assertIn("not valid json", context.exception.raw_response)

    def test_strips_markdown_code_blocks(self) -> None:
        """Should strip markdown code blocks from response."""
        transaction = _make_transaction(id=1, description="UNKNOWN STORE")

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='```json\n[{"id": 1, "money_map_type": "CORE", "money_map_subcategory": "Groceries"}]\n```')
        ]
        self.mock_client.messages.create.return_value = mock_response

        results = self.categorizer.categorize([transaction])

        self.assertEqual(results[0].money_map_type, MoneyMapType.CORE)

    def test_missing_transaction_raises_batch_error(self) -> None:
        """Should raise BatchCategorizationError when response is missing transactions."""
        transactions = [
            _make_transaction(id=1, description="STORE A"),
            _make_transaction(id=2, description="STORE B"),
        ]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"id": 1, "money_map_type": "CORE", "money_map_subcategory": "Groceries"}]')
        ]
        self.mock_client.messages.create.return_value = mock_response

        with self.assertRaises(BatchCategorizationError) as context:
            self.categorizer.categorize(transactions)

        self.assertIn(2, context.exception.failed_ids)
        self.assertEqual(len(context.exception.partial_results), 1)


class TestTransactionCategorizerMixedPipeline(unittest.TestCase):
    """Tests for mixed pipeline scenarios."""

    def setUp(self) -> None:
        """Create categorizer with cache and mocked API client."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.mock_client = MagicMock()
        self.categorizer._client = self.mock_client

    def test_mixed_scenario_processes_all_paths(self) -> None:
        """Should process cached, deterministic, and API transactions correctly."""
        # Setup cache hit
        self.cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)

        transactions = [
            _make_transaction(id=1, description="NETFLIX.COM"),  # Cache hit
            _make_transaction(id=2, description="Virement interne"),  # Internal transfer
            _make_transaction(
                id=3,
                description="CARREFOUR",
                bankin_category="Alimentation & Restau.",
                bankin_subcategory="Supermarché / Epicerie",
            ),  # Deterministic
            _make_transaction(id=4, description="UNKNOWN STORE"),  # API needed
        ]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"id": 4, "money_map_type": "CHOICE", "money_map_subcategory": "Shopping"}]')
        ]
        self.mock_client.messages.create.return_value = mock_response

        results = self.categorizer.categorize(transactions)

        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].money_map_type, MoneyMapType.CHOICE)  # Netflix
        self.assertEqual(results[1].money_map_type, MoneyMapType.EXCLUDED)  # Transfer
        self.assertEqual(results[2].money_map_type, MoneyMapType.CORE)  # Carrefour
        self.assertEqual(results[3].money_map_type, MoneyMapType.CHOICE)  # Unknown

    def test_results_maintain_original_order(self) -> None:
        """Should return results in same order as input transactions."""
        self.cache.put("SPOTIFY", MoneyMapType.CHOICE, "Subscription", 0.99)

        transactions = [
            _make_transaction(id=100, description="UNKNOWN"),
            _make_transaction(id=50, description="SPOTIFY"),
            _make_transaction(id=75, description="Virement interne"),
        ]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"id": 100, "money_map_type": "CORE", "money_map_subcategory": "Other"}]')
        ]
        self.mock_client.messages.create.return_value = mock_response

        results = self.categorizer.categorize(transactions)

        self.assertEqual([r.id for r in results], [100, 50, 75])


class TestTransactionCategorizerEmptyInput(unittest.TestCase):
    """Tests for edge cases."""

    def setUp(self) -> None:
        """Create categorizer."""
        self.cache_path = Path(tempfile.mktemp())
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.categorizer._client = MagicMock()

    def test_empty_input_returns_empty_list(self) -> None:
        """Should return empty list for empty input."""
        results = self.categorizer.categorize([])

        self.assertEqual(results, [])
        self.categorizer._client.messages.create.assert_not_called()


class TestTransactionCategorizerCachePersistence(unittest.TestCase):
    """Tests for cache update behavior."""

    def setUp(self) -> None:
        """Create categorizer with real temp cache."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_path = Path(self.temp_dir) / "cache.json"
        self.cache = CategorizationCache(cache_path=self.cache_path)
        self.categorizer = TransactionCategorizer(api_key="test-key", cache=self.cache)
        self.mock_client = MagicMock()
        self.categorizer._client = self.mock_client

    def test_high_confidence_results_are_cached(self) -> None:
        """Should cache high-confidence API results for future lookups."""
        transaction = _make_transaction(id=1, description="NEW MERCHANT ABC")

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='[{"id": 1, "money_map_type": "CHOICE", "money_map_subcategory": "Shopping", "confidence": 0.98}]'
            )
        ]
        self.mock_client.messages.create.return_value = mock_response

        self.categorizer.categorize([transaction])

        # Verify cache was updated
        cached = self.cache.get("NEW MERCHANT ABC")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.money_map_type, MoneyMapType.CHOICE)

    def test_low_confidence_results_not_cached(self) -> None:
        """Should not cache low-confidence API results."""
        transaction = _make_transaction(id=1, description="UNCERTAIN MERCHANT")

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='[{"id": 1, "money_map_type": "CHOICE", "money_map_subcategory": "Unknown", "confidence": 0.70}]'
            )
        ]
        self.mock_client.messages.create.return_value = mock_response

        self.categorizer.categorize([transaction])

        # Verify cache was NOT updated
        cached = self.cache.get("UNCERTAIN MERCHANT")
        self.assertIsNone(cached)
