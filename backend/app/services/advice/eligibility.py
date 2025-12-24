"""Eligibility determination for advice generation."""

from dataclasses import dataclass

from app.repositories.advice import AdviceRepository
from app.repositories.month import MonthRepository

# ##>: History limits for advice generation context.
REGULAR_HISTORY_LIMIT = 3
EXTENDED_HISTORY_LIMIT = 12

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
    the only advice.

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
    most_recent = month_repo.get_most_recent()

    if most_recent is None:
        return EligibilityResult(
            is_eligible=False,
            history_limit=REGULAR_HISTORY_LIMIT,
            is_first_advice=True,
            reason="Aucun mois disponible dans la base de données.",
        )

    # ##>: Check if target is within the eligible window.
    is_within_window = _is_within_eligible_window(target_year, target_month, most_recent.year, most_recent.month)

    if not is_within_window:
        return EligibilityResult(
            is_eligible=False,
            history_limit=REGULAR_HISTORY_LIMIT,
            is_first_advice=False,
            reason=f"Les conseils ne peuvent être générés que pour les 2 mois les plus récents. "
            f"Votre dernière transaction date de {most_recent.year}-{most_recent.month:02d}.",
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

    # ##>: Target must be within [ref - (window-1), ref] (N most recent months).
    return ref_absolute - (ELIGIBLE_MONTH_WINDOW - 1) <= target_absolute <= ref_absolute


def _is_first_advice_scenario(advice_repo: AdviceRepository, target_month_id: int) -> bool:
    """
    Determine if this is a first-advice scenario.

    First advice means:
    - No advice records exist in the database, OR
    - Only one advice exists and it's for the target month (regenerating first advice)

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
    advice_count = advice_repo.count()

    # ##>: No advice exists at all.
    if advice_count == 0:
        return True

    # ##>: If only one advice exists, check if it's for the target month.
    if advice_count == 1:
        existing_advice = advice_repo.get_by_month_id(target_month_id)
        if existing_advice is not None:
            return True

    return False
