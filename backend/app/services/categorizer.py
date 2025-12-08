"""Transaction categorization service using Claude API."""

import json
import logging
from typing import ClassVar

import anthropic

from app.db.enums import MoneyMapType
from app.services.categorization_cache import CategorizationCache
from app.services.categorization_prompt import CATEGORIZATION_SYSTEM_PROMPT
from app.services.category_mapping import CategoryMapping
from app.services.exceptions import (
    APIConnectionError,
    BatchCategorizationError,
    CategorizationError,
    InvalidResponseError,
)
from app.services.schemas import CategorizationResult, TransactionInput

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    Categorize transactions into Money Map types using Claude API.

    Uses a three-tier approach for efficiency:
    1. Cache lookup for recurring patterns
    2. Deterministic rules for known Bankin' categories
    3. Claude API for remaining transactions (batched)

    Examples
    --------
    >>> categorizer = TransactionCategorizer(api_key="sk-ant-...")
    >>> transactions = [TransactionInput(id=1, date="2025-01-15", ...)]
    >>> results = categorizer.categorize(transactions)
    >>> results[0].money_map_type
    <MoneyMapType.CORE: 'CORE'>
    """

    MODEL: ClassVar[str] = "claude-sonnet-4-20250514"
    BATCH_SIZE: ClassVar[int] = 50
    MAX_TOKENS: ClassVar[int] = 4096
    MAX_RETRIES: ClassVar[int] = 3

    def __init__(self, api_key: str, base_url: str | None = None, cache: CategorizationCache | None = None) -> None:
        """
        Initialize categorizer with API key and optional cache.

        Parameters
        ----------
        api_key : str
            Anthropic API key for Claude API calls.
        base_url : str | None
            Optional base URL for Anthropic API.
        cache : CategorizationCache | None
            Cache instance for recurring patterns. Creates default if None.
        """
        self._client = anthropic.Anthropic(api_key=api_key, base_url=base_url, max_retries=self.MAX_RETRIES)
        self._cache = cache if cache is not None else CategorizationCache()

    def categorize(self, transactions: list[TransactionInput]) -> list[CategorizationResult]:
        """
        Categorize a list of transactions into Money Map types.

        Pipeline: cache lookup -> deterministic rules -> Claude API -> merge results.
        Results are returned in the same order as input transactions.

        Parameters
        ----------
        transactions : list[TransactionInput]
            Transactions to categorize.

        Returns
        -------
        list[CategorizationResult]
            Categorization results matching input order.

        Raises
        ------
        APIConnectionError
            If Claude API is unreachable after all retries.
        InvalidResponseError
            If Claude returns unparseable JSON.
        BatchCategorizationError
            If some transactions fail to categorize.
        """
        if not transactions:
            return []

        results: dict[int, CategorizationResult] = {}
        pending: list[TransactionInput] = []

        # ##>: Phase 1: Try cache and deterministic rules first.
        for tx in transactions:
            result = self._check_cache(tx)
            if result:
                results[tx.id] = result
                continue

            result = self._apply_deterministic_rules(tx)
            if result:
                results[tx.id] = result
                continue

            pending.append(tx)

        # ##>: Phase 2: Call Claude API for remaining transactions.
        if pending:
            api_results = self._categorize_with_api(pending)
            for result in api_results:
                results[result.id] = result

            self._update_cache(pending, api_results)
            self._cache.save()

        # ##>: Phase 3: Return results in original order.
        return [results[tx.id] for tx in transactions]

    def _check_cache(self, transaction: TransactionInput) -> CategorizationResult | None:
        """
        Look up transaction in cache.

        Parameters
        ----------
        transaction : TransactionInput
            Transaction to look up.

        Returns
        -------
        CategorizationResult | None
            Cached result if found, None otherwise.
        """
        cached = self._cache.get(transaction.description)
        if cached is None:
            return None

        return CategorizationResult(
            id=transaction.id,
            money_map_type=cached.money_map_type,
            money_map_subcategory=cached.money_map_subcategory,
            confidence=cached.confidence,
        )

    def _apply_deterministic_rules(self, transaction: TransactionInput) -> CategorizationResult | None:
        """
        Apply deterministic categorization rules.

        Checks internal transfer keywords and Bankin' category mapping.

        Parameters
        ----------
        transaction : TransactionInput
            Transaction to categorize.

        Returns
        -------
        CategorizationResult | None
            Deterministic result if matched, None otherwise.
        """
        # ##>: Check internal transfer by description keywords.
        if CategoryMapping.is_internal_transfer(transaction.description):
            return CategorizationResult(
                id=transaction.id,
                money_map_type=MoneyMapType.EXCLUDED,
                money_map_subcategory="",
                confidence=1.0,
            )

        # ##>: Check Bankin' category mapping.
        mapping = CategoryMapping.get_deterministic_category(
            transaction.bankin_category,
            transaction.bankin_subcategory,
        )
        if mapping is not None:
            money_map_type, subcategory = mapping
            return CategorizationResult(
                id=transaction.id,
                money_map_type=money_map_type,
                money_map_subcategory=subcategory,
                confidence=1.0,
            )

        return None

    def _categorize_with_api(self, transactions: list[TransactionInput]) -> list[CategorizationResult]:
        """
        Categorize transactions using Claude API with batching.

        Fail-fast: stops on first batch error.

        Parameters
        ----------
        transactions : list[TransactionInput]
            Transactions requiring API categorization.

        Returns
        -------
        list[CategorizationResult]
            API categorization results.

        Raises
        ------
        APIConnectionError
            If API is unreachable after retries.
        InvalidResponseError
            If response cannot be parsed.
        BatchCategorizationError
            If some transactions are missing from response.
        """
        results: list[CategorizationResult] = []

        for batch_start in range(0, len(transactions), self.BATCH_SIZE):
            batch = transactions[batch_start : batch_start + self.BATCH_SIZE]
            batch_results = self._call_claude_api(batch)
            results.extend(batch_results)

        return results

    def _call_claude_api(self, batch: list[TransactionInput]) -> list[CategorizationResult]:
        """
        Call Claude API for a single batch of transactions.

        Parameters
        ----------
        batch : list[TransactionInput]
            Batch of transactions (max 50).

        Returns
        -------
        list[CategorizationResult]
            Categorization results for the batch.
        """
        user_prompt = self._build_user_prompt(batch)

        try:
            response = self._client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=CATEGORIZATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.AuthenticationError as e:
            # ##!: Clear message for API key issues.
            raise CategorizationError(
                "Invalid Anthropic API key. Please check your ANTHROPIC_API_KEY environment variable."
            ) from e
        except (anthropic.APIConnectionError, anthropic.RateLimitError) as e:
            raise APIConnectionError(retry_count=self.MAX_RETRIES) from e
        except anthropic.APIStatusError as e:
            # ##!: Catch-all for other API errors (500s, etc.).
            logger.error("Anthropic API error (status %s): %s", e.status_code, e.message)
            raise APIConnectionError(retry_count=self.MAX_RETRIES) from e

        # ##>: Extract text content from response. Type narrowing for mypy.
        content_block = response.content[0]
        if not hasattr(content_block, "text"):
            raise InvalidResponseError("Response does not contain text content")
        response_text: str = content_block.text
        batch_ids = [tx.id for tx in batch]

        return self._parse_response(response_text, batch_ids)

    def _build_user_prompt(self, transactions: list[TransactionInput]) -> str:
        """
        Build user prompt with transactions for Claude.

        Parameters
        ----------
        transactions : list[TransactionInput]
            Transactions to include in prompt.

        Returns
        -------
        str
            Formatted user prompt.
        """
        tx_list = [
            {
                "id": tx.id,
                "date": tx.date,
                "description": tx.description,
                "amount": tx.amount,
                "bankin_category": tx.bankin_category,
                "bankin_subcategory": tx.bankin_subcategory,
            }
            for tx in transactions
        ]

        return (
            "Catégorise les transactions suivantes. "
            "Retourne UNIQUEMENT un tableau JSON, sans markdown ni texte additionnel.\n\n"
            f"{json.dumps(tx_list, ensure_ascii=False, indent=2)}"
        )

    def _parse_response(self, response_text: str, batch_ids: list[int]) -> list[CategorizationResult]:
        """
        Parse Claude's JSON response into CategorizationResult objects.

        Parameters
        ----------
        response_text : str
            Raw response text from Claude.
        batch_ids : list[int]
            Expected transaction IDs in the response.

        Returns
        -------
        list[CategorizationResult]
            Parsed categorization results.

        Raises
        ------
        InvalidResponseError
            If JSON is malformed or missing required fields.
        BatchCategorizationError
            If some transactions are missing from response.
        """
        cleaned = response_text.strip()

        # ##>: Strip markdown code blocks if present.
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:]).rsplit("```", 1)[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise InvalidResponseError(response_text) from e

        if not isinstance(data, list):
            raise InvalidResponseError(response_text)

        results: list[CategorizationResult] = []
        returned_ids: set[int] = set()

        for item in data:
            try:
                result = CategorizationResult(
                    id=item["id"],
                    money_map_type=MoneyMapType(item["money_map_type"]),
                    money_map_subcategory=item["money_map_subcategory"],
                    confidence=item.get("confidence", 1.0),
                )
                results.append(result)
                returned_ids.add(result.id)
            except (KeyError, ValueError) as e:
                raise InvalidResponseError(response_text) from e

        # ##>: Check for missing transactions.
        missing_ids = set(batch_ids) - returned_ids
        if missing_ids:
            raise BatchCategorizationError(
                failed_ids=list(missing_ids),
                partial_results=[r.model_dump() for r in results],
            )

        return results

    def _update_cache(self, transactions: list[TransactionInput], results: list[CategorizationResult]) -> None:
        """
        Cache high-confidence API results for future lookups.

        Parameters
        ----------
        transactions : list[TransactionInput]
            Original transactions.
        results : list[CategorizationResult]
            API results to potentially cache.
        """
        tx_by_id = {tx.id: tx for tx in transactions}

        for result in results:
            tx = tx_by_id.get(result.id)
            if tx is None:
                # ##!: This indicates a bug - API returned an ID we did not send.
                logger.warning(
                    "API returned result for unknown transaction ID %d. This may indicate a parsing bug.",
                    result.id,
                )
                continue

            self._cache.put(
                description=tx.description,
                money_map_type=result.money_map_type,
                money_map_subcategory=result.money_map_subcategory,
                confidence=result.confidence,
            )
