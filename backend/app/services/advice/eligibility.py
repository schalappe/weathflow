"""Eligibility determination for advice generation."""

from dataclasses import dataclass

from app.repositories.advice import AdviceRepository
from app.repositories.month import MonthRepository

# ##>: History limits for advice generation context.
REGULAR_HISTORY_LIMIT = 3
EXTENDED_HISTORY_LIMIT = 12

# ##>: Minimum months required for advice generation.
MIN_MONTHS_REQUIRED = 2

# ##>: Only the N most recent months are eligible for advice.
ELIGIBLE_MONTH_WINDOW = 2


@dataclass(frozen=True)
class EligibilityResult:
    """
    Result of an eligibility check for advice generation.

    Attributes
    ----------
    is_eligible : bool
        Whether the month is eligible for advice generation.
    history_limit : int
        Number of months to include in history (3 or 12).
    is_first_advice : bool
        Whether this is the first advice generation.
    reason : str | None
        Explanation if not eligible, None otherwise.
    """

    is_eligible: bool
    history_limit: int
    is_first_advice: bool
    reason: str | None = None


def check_eligibility(
    target_year: int,
    target_month: int,
    target_month_id: int,
    month_repo: MonthRepository,
    advice_repo: AdviceRepository,
) -> EligibilityResult:
    """
    Check if a month is eligible for advice generation.

    Eligibility is determined by whether the target month falls within
    the 2 most recent months in the database. History limit is extended
    to 12 months for first-time advice generation or when regenerating
    the only/first advice.

    Parameters
    ----------
    target_year : int
        Year of the month to check.
    target_month : int
        Month number to check.
    target_month_id : int
        Database ID of the target month.
    month_repo : MonthRepository
        Repository for month data access.
    advice_repo : AdviceRepository
        Repository for advice data access.

    Returns
    -------
    EligibilityResult
        Eligibility status with history limit and reason if ineligible.
    """
    most_recent = month_repo.get_most_recent_month()

    if most_recent is None:
        return EligibilityResult(
            is_eligible=False,
            history_limit=REGULAR_HISTORY_LIMIT,
            is_first_advice=True,
            reason="No months available in database.",
        )

    # ##>: Check if we have enough months.
    all_months = month_repo.get_recent(limit=0)
    if len(all_months) < MIN_MONTHS_REQUIRED:
        return EligibilityResult(
            is_eligible=False,
            history_limit=REGULAR_HISTORY_LIMIT,
            is_first_advice=True,
            reason=f"Not enough data. At least {MIN_MONTHS_REQUIRED} months required.",
        )

    # ##>: Check if target is within the eligible window.
    is_within_window = _is_within_eligible_window(target_year, target_month, most_recent.year, most_recent.month)

    if not is_within_window:
        return EligibilityResult(
            is_eligible=False,
            history_limit=REGULAR_HISTORY_LIMIT,
            is_first_advice=False,
            reason=f"Advice can only be generated for the 2 most recent months. "
            f"Your last transaction is in {most_recent.year}-{most_recent.month:02d}.",
        )

    # ##>: Determine if this is first advice scenario.
    is_first = _is_first_advice_scenario(advice_repo, target_month_id)
    history_limit = EXTENDED_HISTORY_LIMIT if is_first else REGULAR_HISTORY_LIMIT

    return EligibilityResult(
        is_eligible=True,
        history_limit=history_limit,
        is_first_advice=is_first,
        reason=None,
    )


def _is_within_eligible_window(target_year: int, target_month: int, ref_year: int, ref_month: int) -> bool:
    """
    Check if target month is within the eligible window of the reference month.

    The eligible window includes the reference month and the previous month.

    Parameters
    ----------
    target_year : int
        Year of the target month.
    target_month : int
        Month number of the target month.
    ref_year : int
        Year of the reference (most recent) month.
    ref_month : int
        Month number of the reference month.

    Returns
    -------
    bool
        True if target is within 2 months of reference (inclusive).
    """
    # ##>: Convert to absolute month count for easier comparison.
    target_absolute = target_year * 12 + target_month
    ref_absolute = ref_year * 12 + ref_month

    # ##>: Target must be within [ref - 1, ref] (2 most recent months).
    return ref_absolute - 1 <= target_absolute <= ref_absolute


def _is_first_advice_scenario(advice_repo: AdviceRepository, target_month_id: int) -> bool:
    """
    Determine if this is a first-advice scenario.

    First advice means:
    - No advice records exist in the database, OR
    - The only advice that exists is for the target month (regenerating first advice)

    Parameters
    ----------
    advice_repo : AdviceRepository
        Repository for advice data access.
    target_month_id : int
        Database ID of the target month.

    Returns
    -------
    bool
        True if this should use extended history context.
    """
    # ##>: No advice exists at all.
    if not advice_repo.has_any_advice():
        return True

    # ##>: If regenerating and it's the only advice, treat as first advice.
    other_advice_count = advice_repo.count_advice_excluding_month(target_month_id)
    return other_advice_count == 0
