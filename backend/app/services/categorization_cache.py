"""In-memory cache with JSON persistence for transaction categorizations."""

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

from app.db.enums import MoneyMapType
from app.services.schemas import CachedCategorization


class CategorizationCache:
    """
    Cache for recurring transaction categorizations.

    Stores categorization results in memory with JSON file persistence.
    Only caches high-confidence results (>= 0.95) to ensure quality.

    Examples
    --------
    >>> cache = CategorizationCache()
    >>> cache.put("NETFLIX.COM", MoneyMapType.CHOICE, "Subscription services", 0.98)
    >>> result = cache.get("netflix.com 12/05")
    >>> result.money_map_type
    <MoneyMapType.CHOICE: 'CHOICE'>
    """

    DEFAULT_CACHE_PATH: ClassVar[Path] = Path("data/categorization_cache.json")
    CONFIDENCE_THRESHOLD: ClassVar[float] = 0.95
    STALE_DAYS: ClassVar[int] = 180

    def __init__(self, cache_path: Path | None = None) -> None:
        """
        Initialize cache with optional custom path.

        Parameters
        ----------
        cache_path : Path | None
            Path to JSON cache file. Defaults to data/categorization_cache.json.
        """
        self._cache_path = cache_path or self.DEFAULT_CACHE_PATH
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _normalize_key(self, description: str) -> str:
        """
        Normalize transaction description for cache key.

        Removes variable parts like dates and reference numbers to
        match recurring transactions with different suffixes.

        Parameters
        ----------
        description : str
            Raw transaction description.

        Returns
        -------
        str
            Normalized cache key.
        """
        normalized = description.lower().strip()
        # ##>: Remove date patterns like "12/05", "31/12/2024".
        normalized = re.sub(r"\b\d{1,2}/\d{2}(?:/\d{2,4})?\b", "", normalized)
        # ##>: Remove reference patterns like "REF:ABC123", "REF:12345".
        normalized = re.sub(r"\bref:\s*[a-z0-9]+\b", "", normalized, flags=re.IGNORECASE)
        # ##>: Collapse multiple spaces and strip again.
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def get(self, description: str) -> CachedCategorization | None:
        """
        Retrieve cached categorization for a description.

        Increments hit_count when a cache entry is found.

        Parameters
        ----------
        description : str
            Transaction description to look up.

        Returns
        -------
        CachedCategorization | None
            Cached result if found, None otherwise.
        """
        key = self._normalize_key(description)
        if key not in self._cache:
            return None

        entry = self._cache[key]
        # ##>: Update hit_count and last_hit_at for stale entry tracking.
        entry["hit_count"] = entry.get("hit_count", 0) + 1
        entry["last_hit_at"] = datetime.now(UTC).isoformat()

        return CachedCategorization(
            money_map_type=MoneyMapType(entry["money_map_type"]),
            money_map_subcategory=entry["money_map_subcategory"],
            confidence=entry["confidence"],
            hit_count=entry["hit_count"],
        )

    def put(
        self,
        description: str,
        money_map_type: MoneyMapType,
        money_map_subcategory: str,
        confidence: float,
    ) -> bool:
        """
        Cache a categorization result if confidence is high enough.

        Parameters
        ----------
        description : str
            Transaction description to cache.
        money_map_type : MoneyMapType
            Assigned Money Map category.
        money_map_subcategory : str
            Assigned subcategory.
        confidence : float
            Confidence score (0.0 to 1.0).

        Returns
        -------
        bool
            True if cached, False if confidence too low.
        """
        if confidence < self.CONFIDENCE_THRESHOLD:
            return False

        key = self._normalize_key(description)
        self._cache[key] = {
            "money_map_type": money_map_type.value,
            "money_map_subcategory": money_map_subcategory,
            "confidence": confidence,
            "hit_count": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "last_hit_at": datetime.now(UTC).isoformat(),
        }
        return True

    def save(self) -> None:
        """
        Persist cache to JSON file, removing stale entries.

        Stale entries are those not accessed in the last 180 days.
        """
        self._remove_stale_entries()
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_path.open("w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        """Clear all cache entries (for testing)."""
        self._cache.clear()

    def _load_cache(self) -> None:
        """Load cache from JSON file if it exists."""
        if self._cache_path.exists():
            with self._cache_path.open(encoding="utf-8") as f:
                self._cache = json.load(f)

    def _remove_stale_entries(self) -> None:
        """Remove entries not accessed in the last 180 days."""
        cutoff = datetime.now(UTC) - timedelta(days=self.STALE_DAYS)
        stale_keys = []

        for key, entry in self._cache.items():
            last_hit = entry.get("last_hit_at")
            if last_hit:
                last_hit_dt = datetime.fromisoformat(last_hit)
                # ##>: Ensure timezone-aware comparison for old cache entries.
                if last_hit_dt.tzinfo is None:
                    last_hit_dt = last_hit_dt.replace(tzinfo=UTC)
                if last_hit_dt < cutoff:
                    stale_keys.append(key)

        for key in stale_keys:
            del self._cache[key]
