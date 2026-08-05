"""Advice storage and generation-data services."""

from datetime import UTC, date, datetime, timedelta
from math import isclose
from statistics import median
from typing import Any, Literal, cast

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.advice import Advice
from app.db.models.commitment_fact import CommitmentFact
from app.db.models.constraint_fact import ConstraintFact
from app.db.models.income_fact import IncomeFact
from app.db.models.month import Month
from app.db.models.observation_fact import ImportCoverageEvidence, PeriodCoverageFact
from app.db.models.transaction import Transaction
from app.repositories.advice import AdviceRepository
from app.repositories.commitment_fact import CommitmentFactRepository, CommitmentFactType
from app.repositories.constraint_fact import ConstraintFactRepository, ConstraintFactType
from app.repositories.income_fact import IncomeFactRepository, IncomeFactType
from app.repositories.observation_fact import ObservationFactRepository
from app.repositories.transaction import TransactionRepository
from app.services.advice.models import (
    ActionUnavailabilityCitation,
    ActionUnavailabilityContext,
    AdviceContext,
    AdviceResponse,
    ClarificationOutput,
    CommitmentFactContext,
    ConstraintFactContext,
    DecisionOutput,
    DecisionTrace,
    DecisionTraceDetails,
    FinancialLimitCitation,
    FinancialLimitContext,
    IncomeFactCitation,
    IncomeFactContext,
    MaterialContradiction,
    MonthData,
    ObservedFact,
    PeriodCoverageContext,
    PeriodCoverageSignal,
    TransactionNature,
    TransactionNatureContext,
    TransactionNatureSignal,
    TransactionSample,
    UnresolvedOutput,
)
from app.services.calculation.service import calculate_month_stats
from app.services.exceptions import AdviceParseError, AdviceQueryError, TransactionNotFoundError


def get_advice_by_month_id(advice_repo: AdviceRepository, month_id: int) -> Advice | None:
    """Retrieve stored advice.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Advice storage.
    month_id : int
        Month id.

    Returns
    -------
    Advice | None
        Stored record.

    Raises
    ------
    AdviceQueryError
        Query failed.
    """
    try:
        return advice_repo.get_by_month_id(month_id)
    except SQLAlchemyError as error:
        logger.exception("Database error retrieving advice for month_id={}", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def create_or_update_advice(advice_repo: AdviceRepository, month_id: int, advice_text: str) -> Advice:
    """Persist current monthly advice.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Advice storage.
    month_id : int
        Month id.
    advice_text : str
        Decision JSON.

    Returns
    -------
    Advice
        Persisted record.

    Raises
    ------
    AdviceQueryError
        Write failed.
    """
    try:
        result = advice_repo.upsert(month_id, advice_text)
        advice_repo.commit()
        advice_repo.refresh(result)
        return result
    except SQLAlchemyError as error:
        advice_repo.rollback()
        logger.exception("Database error saving advice for month_id={}", month_id)
        raise AdviceQueryError(month_id, str(error)) from error


def _extract_all_transactions(transactions: list[Transaction]) -> dict[str, list[TransactionSample]]:
    """Group observed transactions.

    Parameters
    ----------
    transactions : list[Transaction]
        Month transactions.

    Returns
    -------
    dict[str, list[TransactionSample]]
        Transactions grouped by Money Map category.
    """
    categories = {"INCOME", "CORE", "CHOICE", "COMPOUND"}
    grouped: dict[str, list[Transaction]] = {category: [] for category in categories}
    for transaction in transactions:
        if transaction.money_map_type in categories:
            grouped[transaction.money_map_type].append(transaction)

    return {
        category: [
            TransactionSample(
                transaction_id=transaction.id,
                description=transaction.description,
                amount=abs(transaction.amount),
                date=transaction.date,
                account=transaction.account,
                subcategory=transaction.money_map_subcategory,
            )
            for transaction in sorted(items, key=lambda item: abs(item.amount), reverse=True)
        ]
        for category, items in grouped.items()
    }


def month_to_month_data(month: Month) -> MonthData:
    """Convert persisted month to observed generation data.

    Parameters
    ----------
    month : Month
        Month with transactions loaded.

    Returns
    -------
    MonthData
        Generator input.
    """
    return MonthData(
        year=month.year,
        month=month.month,
        total_income=month.total_income,
        total_core=month.total_core,
        total_choice=month.total_choice,
        total_compound=month.total_compound,
        core_percentage=month.core_percentage,
        choice_percentage=month.choice_percentage,
        compound_percentage=month.compound_percentage,
        score=month.score,
        score_label=month.score_label,
        transactions=_extract_all_transactions(month.transactions),
    )


def advice_response_to_json(advice: AdviceResponse) -> str:
    """Serialize decision outputs.

    Parameters
    ----------
    advice : AdviceResponse
        Valid decision outputs.

    Returns
    -------
    str
        Storage JSON.
    """
    return advice.model_dump_json()


_COMMITMENT_FIELDS: dict[CommitmentFactType, tuple[str, ...]] = {
    "recurring_obligation": ("amount", "frequency", "end_date"),
    "one_off_obligation": ("amount", "due_date"),
    "debt_position": ("balance", "overdue_amount"),
    "debt_terms": ("minimum_payment", "annual_rate", "cost", "end_date"),
}


def commitment_fact_context(fact: CommitmentFact) -> CommitmentFactContext:
    """Map persistence to generation context.

    Parameters
    ----------
    fact : CommitmentFact
        Stored obligation or debt fact.

    Returns
    -------
    CommitmentFactContext
        Typed generation fact.
    """
    fact_type = cast(CommitmentFactType, fact.fact_type)
    data: dict[str, Any] = {
        "fact_id": fact.id,
        "fact_type": fact_type,
        "label": fact.label,
        "state": fact.state,
        "last_confirmed_at": fact.last_confirmed_at,
        "valid_until": fact.valid_until,
    }
    data.update({field: getattr(fact, field) for field in _COMMITMENT_FIELDS[fact_type]})
    return CommitmentFactContext.model_validate(data)


def load_commitment_context(
    fact_repo: CommitmentFactRepository,
    advice_repo: AdviceRepository,
) -> list[CommitmentFactContext]:
    """Load commitments and invalidate advice citing expired facts.

    Parameters
    ----------
    fact_repo : CommitmentFactRepository
        Commitment persistence.
    advice_repo : AdviceRepository
        Advice persistence.

    Returns
    -------
    list[CommitmentFactContext]
        Stored facts, including inactive values.
    """
    facts = fact_repo.get_all()
    for fact in facts:
        if fact.state == "to_confirm":
            advice_repo.delete_depending_on_commitment(fact.id, fact.fact_type)
    return [commitment_fact_context(fact) for fact in facts]


def create_commitment_fact(
    fact_repo: CommitmentFactRepository,
    advice_repo: AdviceRepository,
    values: dict[str, Any],
) -> CommitmentFact:
    """Create a commitment and invalidate cached advice.

    Parameters
    ----------
    fact_repo : CommitmentFactRepository
        Commitment persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    values : dict[str, Any]
        Validated fact fields.

    Returns
    -------
    CommitmentFact
        Stored fact.
    """
    fact = fact_repo.put(values)
    advice_repo.invalidate_all()
    return fact


def update_commitment_fact(
    fact_repo: CommitmentFactRepository,
    advice_repo: AdviceRepository,
    fact_id: int,
    values: dict[str, Any],
) -> CommitmentFact | None:
    """Update a commitment and invalidate dependent advice.

    Parameters
    ----------
    fact_repo : CommitmentFactRepository
        Commitment persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    fact_id : int
        Stored fact id.
    values : dict[str, Any]
        Validated replacement fields.

    Returns
    -------
    CommitmentFact | None
        Updated fact, or None when absent.
    """
    previous = fact_repo.get(fact_id)
    if previous is None:
        return None
    fact = fact_repo.put(values, fact_id)
    advice_repo.delete_depending_on_commitment(previous.id, previous.fact_type)
    return fact


def delete_commitment_fact(
    fact_repo: CommitmentFactRepository,
    advice_repo: AdviceRepository,
    fact_id: int,
) -> bool:
    """Delete a commitment and invalidate dependent advice.

    Parameters
    ----------
    fact_repo : CommitmentFactRepository
        Commitment persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    fact_id : int
        Stored fact id.

    Returns
    -------
    bool
        Whether a fact was deleted.
    """
    fact = fact_repo.get(fact_id)
    if fact is None:
        return False
    fact_repo.delete(fact_id)
    advice_repo.delete_depending_on_commitment(fact.id, fact.fact_type)
    return True


def prepare_commitment_context(
    fact_repo: CommitmentFactRepository,
    advice_repo: AdviceRepository,
    answer: CommitmentFactContext | None,
    remember: bool,
    target_fact_id: int | None = None,
) -> list[CommitmentFactContext]:
    """Apply an optional answer to stored commitment context.

    Parameters
    ----------
    fact_repo : CommitmentFactRepository
        Commitment persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    answer : CommitmentFactContext | None
        Request-scoped fact.
    remember : bool
        Persist the answer when true.
    target_fact_id : int | None
        Exact contradicted fact to replace.

    Returns
    -------
    list[CommitmentFactContext]
        Context for the current generation.
    """
    contexts = load_commitment_context(fact_repo, advice_repo)
    if answer is None:
        return contexts
    matching = next(
        (
            context
            for context in contexts
            if (
                context.fact_id == target_fact_id
                if target_fact_id is not None
                else context.fact_type == answer.fact_type and context.label == answer.label
            )
        ),
        None,
    )
    if target_fact_id is not None and matching is None:
        raise RuntimeError("contradicted commitment disappeared during update")
    matching_id = matching.fact_id if matching is not None else None
    contexts = [context for context in contexts if context is not matching]
    if remember:
        fields = {"fact_type", "label", *_COMMITMENT_FIELDS[answer.fact_type]}
        values = answer.model_dump(include=fields)
        fact = (
            create_commitment_fact(fact_repo, advice_repo, values)
            if matching_id is None
            else update_commitment_fact(fact_repo, advice_repo, matching_id, values)
        )
        if fact is None:
            raise RuntimeError("commitment disappeared during update")
        contexts.append(commitment_fact_context(fact))
    else:
        if matching_id is not None and matching is not None:
            fact_repo.mark_to_confirm(matching_id)
            advice_repo.delete_depending_on_commitment(matching_id, matching.fact_type)
        contexts.append(answer)
    return contexts


def income_fact_context(fact: IncomeFact) -> IncomeFactContext:
    """Map persisted income to generation context.

    Parameters
    ----------
    fact : IncomeFact
        Stored income.

    Returns
    -------
    IncomeFactContext
        Typed generation fact.
    """
    return IncomeFactContext.model_validate(
        {
            "fact_type": fact.fact_type,
            "amount": fact.amount,
            "frequency": fact.frequency,
            "label": fact.label,
            "expected_date": fact.expected_date,
            "state": fact.state,
            "last_confirmed_at": fact.last_confirmed_at.replace(tzinfo=UTC),
            "valid_until": fact.valid_until.replace(tzinfo=UTC),
        }
    )


def load_income_context(
    fact_repo: IncomeFactRepository,
    advice_repo: AdviceRepository,
) -> list[IncomeFactContext]:
    """Load income and invalidate advice citing stale facts.

    Parameters
    ----------
    fact_repo : IncomeFactRepository
        Income persistence.
    advice_repo : AdviceRepository
        Advice persistence.

    Returns
    -------
    list[IncomeFactContext]
        Stored facts, including inactive values.
    """
    facts = fact_repo.get_all()
    for fact in facts:
        if fact.state == "to_confirm":
            advice_repo.delete_depending_on_declared_fact(fact.fact_type)
    return [income_fact_context(fact) for fact in facts]


def put_income_fact(
    fact_repo: IncomeFactRepository,
    advice_repo: AdviceRepository,
    values: dict[str, Any],
) -> IncomeFact:
    """Store income and invalidate dependent advice.

    Parameters
    ----------
    fact_repo : IncomeFactRepository
        Income persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    values : dict[str, Any]
        Validated income fields.

    Returns
    -------
    IncomeFact
        Stored fact.
    """
    fact_type = cast(IncomeFactType, values["fact_type"])
    advice_repo.delete_depending_on_declared_fact(fact_type)
    return fact_repo.put(values)


def delete_income_fact(
    fact_repo: IncomeFactRepository,
    advice_repo: AdviceRepository,
    fact_type: IncomeFactType,
) -> None:
    """Delete income and invalidate dependent advice.

    Parameters
    ----------
    fact_repo : IncomeFactRepository
        Income persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    fact_type : IncomeFactType
        Fact key.
    """
    fact_repo.delete(fact_type)
    advice_repo.delete_depending_on_declared_fact(fact_type)


def prepare_income_context(
    fact_repo: IncomeFactRepository,
    advice_repo: AdviceRepository,
    answer: IncomeFactContext | None,
    remember: bool,
) -> list[IncomeFactContext]:
    """Apply optional answer to stored income context.

    Parameters
    ----------
    fact_repo : IncomeFactRepository
        Income persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    answer : IncomeFactContext | None
        Request-scoped income.
    remember : bool
        Persist answer when true.

    Returns
    -------
    list[IncomeFactContext]
        Current generation context.
    """
    contexts = load_income_context(fact_repo, advice_repo)
    if answer is None:
        return contexts
    contexts = [context for context in contexts if context.fact_type != answer.fact_type]
    if remember:
        fields = {"fact_type", "amount", "label", "frequency", "expected_date"}
        contexts.append(
            income_fact_context(
                put_income_fact(
                    fact_repo,
                    advice_repo,
                    answer.model_dump(include=fields),
                )
            )
        )
    else:
        fact_repo.mark_to_confirm(answer.fact_type)
        advice_repo.delete_depending_on_declared_fact(answer.fact_type)
        contexts.append(answer)
    return contexts


_CONSTRAINT_FIELDS: dict[ConstraintFactType, tuple[str, ...]] = {
    "financial_limit": ("scope_type", "scope", "limit_type", "amount"),
    "action_unavailability": ("action", "review_date"),
}


def constraint_fact_context(fact: ConstraintFact) -> ConstraintFactContext:
    """Map persistence to generation context.

    Parameters
    ----------
    fact : ConstraintFact
        Stored constraint.

    Returns
    -------
    ConstraintFactContext
        Generation constraint.
    """
    fact_type = cast(ConstraintFactType, fact.fact_type)
    values = {
        "fact_id": fact.id,
        "fact_type": fact_type,
        "state": fact.state,
        "last_confirmed_at": fact.last_confirmed_at,
        "valid_until": fact.valid_until,
    }
    values.update({field: getattr(fact, field) for field in _CONSTRAINT_FIELDS[fact_type]})
    model = FinancialLimitContext if fact_type == "financial_limit" else ActionUnavailabilityContext
    return model.model_validate(values)


def load_constraint_context(
    fact_repo: ConstraintFactRepository,
    advice_repo: AdviceRepository,
) -> list[ConstraintFactContext]:
    """Load constraints and invalidate advice citing expired facts.

    Parameters
    ----------
    fact_repo : ConstraintFactRepository
        Constraint persistence.
    advice_repo : AdviceRepository
        Advice persistence.

    Returns
    -------
    list[ConstraintFactContext]
        Current generation constraints.
    """
    facts = fact_repo.get_all()
    for fact in facts:
        if fact.state == "to_confirm":
            advice_repo.delete_depending_on_declared_fact(fact.fact_type)
    return [constraint_fact_context(fact) for fact in facts]


def _same_constraint(left: ConstraintFactContext, right: ConstraintFactContext) -> bool:
    """Match one scoped constraint.

    Parameters
    ----------
    left : ConstraintFactContext
        First constraint.
    right : ConstraintFactContext
        Second constraint.

    Returns
    -------
    bool
        Whether identities match.
    """
    if left.fact_type != right.fact_type:
        return False
    if isinstance(left, FinancialLimitContext) and isinstance(right, FinancialLimitContext):
        return (
            left.scope_type,
            left.scope,
            left.limit_type,
        ) == (
            right.scope_type,
            right.scope,
            right.limit_type,
        )
    return (
        isinstance(left, ActionUnavailabilityContext)
        and isinstance(right, ActionUnavailabilityContext)
        and left.action == right.action
    )


def prepare_constraint_context(
    fact_repo: ConstraintFactRepository,
    advice_repo: AdviceRepository,
    answer: ConstraintFactContext | None,
    remember: bool,
) -> list[ConstraintFactContext]:
    """Apply optional answer to stored constraints.

    Parameters
    ----------
    fact_repo : ConstraintFactRepository
        Constraint persistence.
    advice_repo : AdviceRepository
        Advice persistence.
    answer : ConstraintFactContext | None
        Request-scoped answer.
    remember : bool
        Persist answer when true.

    Returns
    -------
    list[ConstraintFactContext]
        Current generation constraints.
    """
    contexts = load_constraint_context(fact_repo, advice_repo)
    if answer is None:
        return contexts
    matching = next((context for context in contexts if _same_constraint(context, answer)), None)
    matching_id = matching.fact_id if matching is not None else None
    contexts = [context for context in contexts if context is not matching]
    if remember:
        values = answer.model_dump(include={"fact_type", *_CONSTRAINT_FIELDS[answer.fact_type]})
        fact = fact_repo.put(values, matching_id)
        advice_repo.delete_depending_on_declared_fact(answer.fact_type)
        contexts.append(constraint_fact_context(fact))
    else:
        if matching_id is not None:
            fact_repo.mark_to_confirm(matching_id)
            advice_repo.delete_depending_on_declared_fact(answer.fact_type)
        contexts.append(answer)
    return contexts


def deduplicate_expected_income(
    contexts: list[IncomeFactContext],
    months: list[MonthData],
) -> tuple[list[IncomeFactContext], list[MonthData]]:
    """Remove matched observation; declaration remains sole income input.

    Parameters
    ----------
    contexts : list[IncomeFactContext]
        Declared income.
    months : list[MonthData]
        Observed generation data.

    Returns
    -------
    tuple[list[IncomeFactContext], list[MonthData]]
        Match-marked context and neutralized observations.
    """
    updated_contexts: list[IncomeFactContext] = []
    updated_months = list(months)
    for context in contexts:
        matched = False
        if context.fact_type == "expected_one_off_income" and context.state != "to_confirm":
            for month_index, month in enumerate(updated_months):
                transactions = month.transactions or {}
                incomes = transactions.get("INCOME", [])
                matching = [
                    (index, transaction)
                    for index, transaction in enumerate(incomes)
                    if context.label is not None
                    and transaction.date == context.expected_date
                    and transaction.amount == context.amount
                    and " ".join(transaction.description.casefold().split())
                    == " ".join(context.label.casefold().split())
                ]
                match_index = min(matching, key=lambda item: item[1].transaction_id)[0] if matching else None
                if match_index is None:
                    continue
                matched = True
                updated_transactions = dict(transactions)
                updated_transactions["INCOME"] = [
                    transaction for index, transaction in enumerate(incomes) if index != match_index
                ]
                adjusted = calculate_month_stats(
                    max(0, month.total_income - context.amount),
                    month.total_core,
                    month.total_choice,
                )
                updated_months[month_index] = month.model_copy(
                    update={
                        **adjusted.model_dump(exclude={"score_label"}),
                        "score_label": adjusted.score_label.value,
                        "transactions": updated_transactions,
                    }
                )
                break
        updated_contexts.append(context.model_copy(update={"matched_transaction": matched}))
    return updated_contexts, updated_months


_RecurringFrequency = Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"]
_RecurringSignal = Literal[
    "recurring_income_lower",
    "recurring_income_higher",
    "recurring_obligation_higher",
    "recurring_obligation_lower",
]
_OneOffSignal = Literal["one_off_income_mismatch", "one_off_obligation_mismatch"]


def _cycle_start(value: date, frequency: _RecurringFrequency) -> date:
    """Return calendar start of a recurring cycle.

    Parameters
    ----------
    value : date
        Transaction date.
    frequency : _RecurringFrequency
        Declared cadence.

    Returns
    -------
    date
        Stable cycle start.
    """
    if frequency in {"weekly", "biweekly"}:
        week_start = value - timedelta(days=value.weekday())
        if frequency == "weekly":
            return week_start
        epoch = date(1970, 1, 5)
        return week_start - timedelta(weeks=((week_start - epoch).days // 7) % 2)
    if frequency == "monthly":
        return value.replace(day=1)
    if frequency == "quarterly":
        return date(value.year, (value.month - 1) // 3 * 3 + 1, 1)
    return date(value.year, 1, 1)


def _cycle_key(value: date, frequency: _RecurringFrequency) -> str:
    """Return stable recurring-cycle key.

    Parameters
    ----------
    value : date
        Transaction date.
    frequency : _RecurringFrequency
        Declared cadence.

    Returns
    -------
    str
        Cycle key.
    """
    start = _cycle_start(value, frequency)
    if frequency in {"weekly", "biweekly"}:
        return start.isoformat()
    if frequency == "monthly":
        return start.strftime("%Y-%m")
    if frequency == "quarterly":
        return f"{start.year:04d}-Q{(start.month - 1) // 3 + 1}"
    return f"{start.year:04d}"


def _cycle_key_start(key: str, frequency: _RecurringFrequency) -> date:
    """Recover a cycle start from its stable key.

    Parameters
    ----------
    key : str
        Stable cycle key.
    frequency : _RecurringFrequency
        Declared cadence.

    Returns
    -------
    date
        Cycle start.
    """
    if frequency in {"weekly", "biweekly"}:
        return date.fromisoformat(key)
    if frequency == "monthly":
        return date.fromisoformat(f"{key}-01")
    if frequency == "quarterly":
        year, quarter = key.split("-Q")
        return date(int(year), (int(quarter) - 1) * 3 + 1, 1)
    return date(int(key), 1, 1)


def _cycle_months(value: date, frequency: _RecurringFrequency) -> set[str]:
    """Return months requiring complete coverage for one cycle.

    Parameters
    ----------
    value : date
        Transaction date inside the cycle.
    frequency : _RecurringFrequency
        Declared cadence.

    Returns
    -------
    set[str]
        Covered calendar months.
    """
    start = _cycle_start(value, frequency)
    if frequency in {"weekly", "biweekly"}:
        end = start + timedelta(days=6 if frequency == "weekly" else 13)
        return {start.strftime("%Y-%m"), end.strftime("%Y-%m")}
    if frequency == "monthly":
        return {start.strftime("%Y-%m")}
    if frequency == "quarterly":
        return {f"{start.year:04d}-{month:02d}" for month in range(start.month, start.month + 3)}
    return {f"{start.year:04d}-{month:02d}" for month in range(1, 13)}


def _cycle_starts_are_consecutive(starts: list[date], frequency: _RecurringFrequency) -> bool:
    """Check starts occupy consecutive declared cycles.

    Parameters
    ----------
    starts : list[date]
        Selected cycle starts.
    frequency : _RecurringFrequency
        Declared cadence.

    Returns
    -------
    bool
        Whether every adjacent cycle is consecutive.
    """
    for left, right in zip(starts, starts[1:], strict=False):
        if frequency in {"weekly", "biweekly"}:
            expected_days = 7 if frequency == "weekly" else 14
            if (right - left).days != expected_days:
                return False
        else:
            left_month = left.year * 12 + left.month - 1
            right_month = right.year * 12 + right.month - 1
            step = {"monthly": 1, "quarterly": 3, "yearly": 12}[frequency]
            if right_month - left_month != step:
                return False
    return True


def _complete_cycle_starts(complete_months: set[str], frequency: _RecurringFrequency) -> list[date]:
    """Return declared cycles fully covered by imported months.

    Parameters
    ----------
    complete_months : set[str]
        Complete calendar months.
    frequency : _RecurringFrequency
        Declared cadence.

    Returns
    -------
    list[date]
        Ordered fully covered cycle starts.
    """
    if not complete_months:
        return []
    month_starts = sorted(date.fromisoformat(f"{month}-01") for month in complete_months)
    if frequency in {"weekly", "biweekly"}:
        cursor = _cycle_start(month_starts[0], frequency)
        next_month = (month_starts[-1].replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day = next_month - timedelta(days=1)
        step = timedelta(days=7 if frequency == "weekly" else 14)
        candidates: list[date] = []
        while cursor <= last_day:
            candidates.append(cursor)
            cursor += step
    else:
        candidates = sorted({_cycle_start(month, frequency) for month in month_starts})
    return [start for start in candidates if _cycle_months(start, frequency) <= complete_months]


def _select_adverse_series(
    samples: list[TransactionSample],
    frequency: _RecurringFrequency,
    declared_value: float,
    complete_months: set[str],
    checks: list[tuple[int, Literal["higher", "lower"], _RecurringSignal]],
) -> tuple[_RecurringSignal, float, list[TransactionSample], list[str]] | None:
    """Select the shortest complete adverse series.

    Parameters
    ----------
    samples : list[TransactionSample]
        Candidate observations.
    frequency : _RecurringFrequency
        Declared cadence.
    declared_value : float
        Confirmed amount.
    complete_months : set[str]
        Months with complete, gap-free coverage.
    checks : list[tuple[int, Literal["higher", "lower"], _RecurringSignal]]
        Threshold checks in priority order.

    Returns
    -------
    tuple[_RecurringSignal, float, list[TransactionSample], list[str]] | None
        Signal, median, samples, and cycle keys when admitted.
    """
    cycle_starts = _complete_cycle_starts(complete_months, frequency)
    grouped: dict[str, list[TransactionSample]] = {_cycle_key(start, frequency): [] for start in cycle_starts}
    for sample in sorted(samples, key=lambda item: item.date):
        key = _cycle_key(sample.date, frequency)
        if key in grouped:
            grouped[key].append(sample)
    cycles = [(start, grouped[_cycle_key(start, frequency)]) for start in cycle_starts]
    for count, direction, signal in checks:
        selected_cycles = cycles[-count:]
        starts = [start for start, _ in selected_cycles]
        if len(selected_cycles) != count or not _cycle_starts_are_consecutive(starts, frequency):
            continue
        observed_value = float(
            median(sum(abs(sample.amount) for sample in cycle_samples) for _, cycle_samples in selected_cycles)
        )
        if (
            direction == "higher"
            and observed_value > declared_value * 1.2
            or (direction == "lower" and observed_value < declared_value * 0.8)
        ):
            selected_samples = [sample for _, cycle_samples in selected_cycles for sample in cycle_samples]
            return (
                signal,
                observed_value,
                selected_samples,
                [_cycle_key(start, frequency) for start in starts],
            )
    return None


def _contradiction_from_series(
    *,
    fact_type: IncomeFactType | CommitmentFactType,
    fact_id: int | None,
    declared_value: float,
    last_confirmed_at: datetime,
    frequency: _RecurringFrequency,
    label: str | None,
    scope: str,
    series: tuple[_RecurringSignal, float, list[TransactionSample], list[str]],
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> MaterialContradiction | None:
    """Build contradiction from durable source transactions.

    Parameters
    ----------
    fact_type : IncomeFactType | CommitmentFactType
        Declared fact kind.
    fact_id : int | None
        Commitment identity when applicable.
    declared_value : float
        Confirmed amount.
    last_confirmed_at : datetime
        Last explicit confirmation.
    frequency : _RecurringFrequency
        Declared cadence.
    label : str | None
        Commitment label.
    scope : str
        Human-readable evidence scope.
    series : tuple[_RecurringSignal, float, list[TransactionSample], list[str]]
        Admitted adverse series.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Acknowledgement access.

    Returns
    -------
    MaterialContradiction | None
        New unacknowledged contradiction.
    """
    signal, observed_value, samples, cycle_keys = series
    transactions = [
        transaction
        for sample in samples
        if (transaction := transaction_repo.get_by_id(sample.transaction_id)) is not None
    ]
    if len(transactions) != len(samples):
        return None
    observed_cycles = {_cycle_key(sample.date, frequency) for sample in samples}
    observation_keys = [
        *[observation_repo.transaction_key(transaction) for transaction in transactions],
        *[
            f"missing-cycle:{fact_type}:{fact_id or ''}:{cycle_key}"
            for cycle_key in cycle_keys
            if cycle_key not in observed_cycles
        ],
    ]
    acknowledgement = observation_repo.get_contradiction_acknowledgement(f"{fact_type}:{fact_id or ''}")
    acknowledged = acknowledgement.observation_keys if acknowledgement is not None else []
    if acknowledgement is not None and (
        set(observation_keys) <= set(acknowledged)
        or any(
            _cycle_key_start(cycle_key, frequency) <= acknowledgement.confirmed_at.date() for cycle_key in cycle_keys
        )
    ):
        return None
    return MaterialContradiction(
        fact_id=fact_id,
        declared_value=declared_value,
        last_confirmed_at=last_confirmed_at,
        signal=signal,
        observed_value=observed_value,
        period=cycle_keys,
        scope=scope,
        affected_subject="Conseil dépendant du fait déclaré",
        label=label,
        frequency=frequency,
        transaction_ids=[transaction.id for transaction in transactions],
        observation_keys=observation_keys,
        acknowledged_observations=acknowledged,
    )


def _detect_income_contradiction(
    contexts: list[IncomeFactContext],
    months: list[MonthData],
    complete_months: set[str],
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> MaterialContradiction | None:
    """Detect an admitted recurring-income contradiction.

    Parameters
    ----------
    contexts : list[IncomeFactContext]
        Declared income facts.
    months : list[MonthData]
        Observed monthly data.
    complete_months : set[str]
        Months with complete, gap-free coverage.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Acknowledgement access.

    Returns
    -------
    MaterialContradiction | None
        First admitted income contradiction.
    """
    income = next(
        (
            fact
            for fact in contexts
            if fact.fact_type == "usual_disposable_income"
            and fact.frequency is not None
            and fact.state in {"active", "corrected"}
        ),
        None,
    )
    if income is None:
        return None
    frequency = cast(_RecurringFrequency, income.frequency)
    candidates = [sample for month in months for sample in (month.transactions or {}).get("INCOME", [])]
    observed_cycles: dict[str, set[str]] = {}
    for sample in candidates:
        label = " ".join(sample.description.casefold().split())
        observed_cycles.setdefault(label, set()).add(_cycle_key(sample.date, frequency))
    recurring_labels = {label for label, cycles in observed_cycles.items() if len(cycles) >= 2}
    samples = [sample for sample in candidates if " ".join(sample.description.casefold().split()) in recurring_labels]
    series = _select_adverse_series(
        samples,
        frequency,
        income.amount,
        complete_months,
        [(2, "lower", "recurring_income_lower"), (3, "higher", "recurring_income_higher")],
    )
    if series is None:
        return None
    frequency_label = {
        "weekly": "hebdomadaire",
        "biweekly": "bimensuel",
        "monthly": "mensuel",
        "quarterly": "trimestriel",
        "yearly": "annuel",
    }[frequency]
    return _contradiction_from_series(
        fact_type=income.fact_type,
        fact_id=None,
        declared_value=income.amount,
        last_confirmed_at=income.last_confirmed_at,
        frequency=frequency,
        label=None,
        scope=f"Revenu disponible habituel {frequency_label}",
        series=series,
        transaction_repo=transaction_repo,
        observation_repo=observation_repo,
    )


def _detect_commitment_contradiction(
    contexts: list[CommitmentFactContext],
    months: list[MonthData],
    complete_months: set[str],
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> MaterialContradiction | None:
    """Detect an admitted recurring-obligation contradiction.

    Parameters
    ----------
    contexts : list[CommitmentFactContext]
        Declared commitments.
    months : list[MonthData]
        Observed monthly data.
    complete_months : set[str]
        Months with complete, gap-free coverage.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Acknowledgement access.

    Returns
    -------
    MaterialContradiction | None
        First admitted commitment contradiction.
    """
    for commitment in contexts:
        if (
            commitment.fact_type != "recurring_obligation"
            or commitment.frequency is None
            or commitment.amount is None
            or commitment.state not in {"active", "corrected"}
        ):
            continue
        frequency = commitment.frequency
        normalized_label = " ".join(commitment.label.casefold().split())
        samples = [
            sample
            for month in months
            for category, month_samples in (month.transactions or {}).items()
            for sample in month_samples
            if category not in {"INCOME", "EXCLUDED"}
            and " ".join(sample.description.casefold().split()) == normalized_label
        ]
        series = _select_adverse_series(
            samples,
            frequency,
            commitment.amount,
            complete_months,
            [(2, "higher", "recurring_obligation_higher"), (3, "lower", "recurring_obligation_lower")],
        )
        if series is None:
            continue
        frequency_label = {
            "weekly": "hebdomadaire",
            "biweekly": "bimensuelle",
            "monthly": "mensuelle",
            "quarterly": "trimestrielle",
            "yearly": "annuelle",
        }[frequency]
        return _contradiction_from_series(
            fact_type=commitment.fact_type,
            fact_id=commitment.fact_id,
            declared_value=commitment.amount,
            last_confirmed_at=commitment.last_confirmed_at,
            frequency=frequency,
            label=commitment.label,
            scope=f"Obligation récurrente {frequency_label} : {commitment.label}",
            series=series,
            transaction_repo=transaction_repo,
            observation_repo=observation_repo,
        )
    return None


def _contradiction_from_event(
    *,
    fact_type: IncomeFactType | CommitmentFactType,
    fact_id: int | None,
    declared_value: float,
    last_confirmed_at: datetime,
    label: str | None,
    event_date: date,
    scope: str,
    signal: _OneOffSignal,
    sample: TransactionSample,
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> MaterialContradiction | None:
    """Build contradiction from one explicitly paired event.

    Parameters
    ----------
    fact_type : IncomeFactType | CommitmentFactType
        Declared fact kind.
    fact_id : int | None
        Commitment identity when applicable.
    declared_value : float
        Confirmed amount.
    last_confirmed_at : datetime
        Last explicit confirmation.
    label : str | None
        Commitment label when applicable.
    event_date : date
        Declared event date.
    scope : str
        Human-readable evidence scope.
    signal : _OneOffSignal
        Admitted event signal.
    sample : TransactionSample
        Paired observed event.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Acknowledgement access.

    Returns
    -------
    MaterialContradiction | None
        New unacknowledged contradiction.
    """
    transaction = transaction_repo.get_by_id(sample.transaction_id)
    if transaction is None:
        return None
    observation_key = observation_repo.transaction_key(transaction)
    acknowledgement = observation_repo.get_contradiction_acknowledgement(f"{fact_type}:{fact_id or ''}")
    acknowledged = acknowledgement.observation_keys if acknowledgement is not None else []
    if observation_key in acknowledged:
        return None
    return MaterialContradiction(
        fact_id=fact_id,
        declared_value=declared_value,
        last_confirmed_at=last_confirmed_at,
        signal=signal,
        observed_value=abs(sample.amount),
        period=[event_date.isoformat()],
        scope=scope,
        affected_subject="Conseil dépendant du fait déclaré",
        label=label,
        event_date=event_date,
        transaction_ids=[transaction.id],
        observation_keys=[observation_key],
        acknowledged_observations=acknowledged,
    )


def _detect_one_off_income_contradiction(
    contexts: list[IncomeFactContext],
    months: list[MonthData],
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> MaterialContradiction | None:
    """Detect an exactly paired one-off income mismatch.

    Parameters
    ----------
    contexts : list[IncomeFactContext]
        Declared income facts.
    months : list[MonthData]
        Observed monthly data.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Acknowledgement access.

    Returns
    -------
    MaterialContradiction | None
        Admitted one-off income contradiction.
    """
    income = next(
        (
            fact
            for fact in contexts
            if fact.fact_type == "expected_one_off_income"
            and fact.label is not None
            and fact.expected_date is not None
            and fact.state in {"active", "corrected"}
        ),
        None,
    )
    if income is None:
        return None
    label = income.label
    event_date = income.expected_date
    if label is None or event_date is None:
        return None
    normalized_label = " ".join(label.casefold().split())
    samples = [
        sample
        for month in months
        for sample in (month.transactions or {}).get("INCOME", [])
        if sample.date == event_date and " ".join(sample.description.casefold().split()) == normalized_label
    ]
    if len(samples) != 1 or abs(abs(samples[0].amount) - income.amount) <= income.amount * 0.2:
        return None
    return _contradiction_from_event(
        fact_type=income.fact_type,
        fact_id=None,
        declared_value=income.amount,
        last_confirmed_at=income.last_confirmed_at,
        label=label,
        event_date=event_date,
        scope=f"Entrée exceptionnelle attendue : {label}",
        signal="one_off_income_mismatch",
        sample=samples[0],
        transaction_repo=transaction_repo,
        observation_repo=observation_repo,
    )


def _detect_one_off_commitment_contradiction(
    contexts: list[CommitmentFactContext],
    months: list[MonthData],
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> MaterialContradiction | None:
    """Detect an exactly paired one-off obligation mismatch.

    Parameters
    ----------
    contexts : list[CommitmentFactContext]
        Declared commitments.
    months : list[MonthData]
        Observed monthly data.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Acknowledgement access.

    Returns
    -------
    MaterialContradiction | None
        Admitted one-off obligation contradiction.
    """
    for commitment in contexts:
        if (
            commitment.fact_type != "one_off_obligation"
            or commitment.amount is None
            or commitment.due_date is None
            or commitment.state not in {"active", "corrected"}
        ):
            continue
        normalized_label = " ".join(commitment.label.casefold().split())
        samples = [
            sample
            for month in months
            for category, month_samples in (month.transactions or {}).items()
            for sample in month_samples
            if category not in {"INCOME", "EXCLUDED"}
            and sample.date == commitment.due_date
            and " ".join(sample.description.casefold().split()) == normalized_label
        ]
        if len(samples) != 1 or abs(abs(samples[0].amount) - commitment.amount) <= commitment.amount * 0.2:
            continue
        return _contradiction_from_event(
            fact_type=commitment.fact_type,
            fact_id=commitment.fact_id,
            declared_value=commitment.amount,
            last_confirmed_at=commitment.last_confirmed_at,
            label=commitment.label,
            event_date=commitment.due_date,
            scope=f"Obligation ponctuelle à échéance : {commitment.label}",
            signal="one_off_obligation_mismatch",
            sample=samples[0],
            transaction_repo=transaction_repo,
            observation_repo=observation_repo,
        )
    return None


def apply_material_contradictions(
    advice: AdviceResponse,
    income_contexts: list[IncomeFactContext],
    commitment_contexts: list[CommitmentFactContext],
    months: list[MonthData],
    coverages: list[PeriodCoverageContext],
    transaction_repo: TransactionRepository,
    observation_repo: ObservationFactRepository,
) -> AdviceResponse:
    """Replace fact-dependent output when admitted evidence contradicts it.

    Parameters
    ----------
    advice : AdviceResponse
        Generated decision outputs.
    income_contexts : list[IncomeFactContext]
        Declared income facts.
    commitment_contexts : list[CommitmentFactContext]
        Declared obligations.
    months : list[MonthData]
        Observed monthly data.
    coverages : list[PeriodCoverageContext]
        Exact coverage facts.
    transaction_repo : TransactionRepository
        Source transaction access.
    observation_repo : ObservationFactRepository
        Evidence and acknowledgement access.

    Returns
    -------
    AdviceResponse
        Advice with at most one material clarification.
    """
    ordered = sorted(months, key=lambda item: (item.year, item.month))
    observed_accounts = {
        f"{month.year:04d}-{month.month:02d}": {
            sample.account
            for samples in (month.transactions or {}).values()
            for sample in samples
            if sample.account is not None
        }
        for month in ordered
    }
    complete_months = {
        month
        for coverage in coverages
        if coverage.complete and not coverage.missing_elements and not coverage.provenance_issues
        for month in coverage.coverage_months
        if not coverage.accounts or observed_accounts.get(month, set()) <= set(coverage.accounts)
    }
    family: Literal["income", "commitment"] = "income"
    contradiction = _detect_income_contradiction(
        income_contexts,
        ordered,
        complete_months,
        transaction_repo,
        observation_repo,
    )
    if contradiction is None:
        contradiction = _detect_one_off_income_contradiction(
            income_contexts,
            ordered,
            transaction_repo,
            observation_repo,
        )
    if contradiction is None:
        family = "commitment"
        contradiction = _detect_commitment_contradiction(
            commitment_contexts,
            ordered,
            complete_months,
            transaction_repo,
            observation_repo,
        )
    if contradiction is None:
        contradiction = _detect_one_off_commitment_contradiction(
            commitment_contexts,
            ordered,
            transaction_repo,
            observation_repo,
        )
    if contradiction is None:
        return advice
    fact_type: IncomeFactType | CommitmentFactType = (
        "expected_one_off_income"
        if contradiction.signal == "one_off_income_mismatch"
        else "one_off_obligation"
        if contradiction.signal == "one_off_obligation_mismatch"
        else "usual_disposable_income"
        if family == "income"
        else "recurring_obligation"
    )
    dependent_indexes = [
        index
        for index, output in enumerate(advice.outputs)
        if output.type != "clarification"
        and any(
            family == "income"
            and isinstance(fact, IncomeFactCitation)
            and fact.fact_type == fact_type
            or family == "commitment"
            and isinstance(fact, CommitmentFactContext)
            and fact.fact_id == contradiction.fact_id
            for fact in output.trace.details.declared_facts
        )
    ]
    if not dependent_indexes:
        return advice
    dependent_index = dependent_indexes[0]
    dependent = advice.outputs[dependent_index]
    affected_subject = getattr(dependent, "subject", None) or contradiction.affected_subject
    contradiction = contradiction.model_copy(update={"affected_subject": affected_subject})
    clarification = ClarificationOutput(
        type="clarification",
        priority=dependent.priority,
        subject=affected_subject,
        observation=(
            f"Une opération appariée montre {contradiction.observed_value:g} € "
            f"contre {contradiction.declared_value:g} € déclarés."
            if contradiction.signal.startswith("one_off_")
            else f"{len(contradiction.period)} cycles complets et consécutifs montrent "
            f"{contradiction.observed_value:g} € contre {contradiction.declared_value:g} € déclarés."
        ),
        possible_effect=f"{affected_subject} doit être recalculé si la valeur observée devient la référence.",
        question=(
            f"La valeur déclarée de {contradiction.declared_value:g} € est-elle toujours exacte "
            f"depuis sa confirmation du {contradiction.last_confirmed_at.date().isoformat()} ?"
        ),
        fact_type=fact_type,
        material_effects=[
            f"Conserver {contradiction.declared_value:,.0f} € pour le {affected_subject.lower()}.".replace(",", " "),
            f"Recalculer le {affected_subject.lower()} depuis {contradiction.observed_value:,.0f} €.".replace(
                ",", " "
            ),
        ],
        transaction_ids=contradiction.transaction_ids,
        contradiction=contradiction,
    )
    outputs = [
        clarification if index == dependent_index else output
        for index, output in enumerate(advice.outputs)
        if index not in dependent_indexes or index == dependent_index
    ]
    return AdviceResponse(outputs=outputs)


def record_advice_transition(advice: AdviceResponse, transition: str) -> AdviceResponse:
    """Append a lifecycle transition to surviving outputs.

    Parameters
    ----------
    advice : AdviceResponse
        Resolved decision outputs.
    transition : str
        User-visible transition.

    Returns
    -------
    AdviceResponse
        Outputs with transition trace.
    """
    outputs: list[DecisionOutput] = []
    for output in advice.outputs:
        if output.type == "clarification":
            outputs.append(output.model_copy(update={"transitions": [*output.transitions, transition]}))
            continue
        details = output.trace.details.model_copy(
            update={"transitions": [*output.trace.details.transitions, transition]}
        )
        outputs.append(output.model_copy(update={"trace": output.trace.model_copy(update={"details": details})}))
    return AdviceResponse(outputs=outputs)


def plan_contradiction_resolution(
    question: ClarificationOutput,
    answers: list[tuple[str, float | None]],
    remember: bool,
) -> tuple[str, tuple[str, list[str]] | None, int | None] | None:
    """Plan one valid contradiction answer.

    Parameters
    ----------
    question : ClarificationOutput
        Pending material contradiction.
    answers : list[tuple[str, float | None]]
        Submitted fact kinds and amounts.
    remember : bool
        Persist the resolution.

    Returns
    -------
    tuple[str, tuple[str, list[str]] | None, int | None] | None
        Transition, acknowledgement, target fact, or ``None`` when mismatched.
    """
    contradiction = question.contradiction
    answer_amount = next(
        (amount for fact_type, amount in answers if fact_type == question.fact_type),
        None,
    )
    if contradiction is None or answer_amount is None:
        return None
    if not remember:
        return (
            "Contradiction résolue pour cette session : ancien fait rendu à confirmer.",
            None,
            contradiction.fact_id,
        )
    acknowledgement = (
        f"{question.fact_type}:{contradiction.fact_id or ''}",
        contradiction.observation_keys,
    )
    transition = (
        "Contradiction confirmée : fait maintenu actif et observations acquittées."
        if answer_amount == contradiction.declared_value
        else "Contradiction corrigée : valeur remplacée et observations acquittées."
    )
    return transition, acknowledgement, contradiction.fact_id


def neutralize_contested_fact(
    question: ClarificationOutput,
    action: Literal["skip", "unknown", "delete"],
    income_repo: IncomeFactRepository,
    commitment_repo: CommitmentFactRepository,
    advice_repo: AdviceRepository,
) -> None:
    """Neutralize or delete a contested fact after abstention.

    Parameters
    ----------
    question : ClarificationOutput
        Pending material contradiction.
    action : Literal["skip", "unknown", "delete"]
        Requested lifecycle transition.
    income_repo : IncomeFactRepository
        Declared income persistence.
    commitment_repo : CommitmentFactRepository
        Declared commitment persistence.
    advice_repo : AdviceRepository
        Stored dependent advice.
    """
    contradiction = question.contradiction
    if contradiction is None:
        return
    if question.fact_type in {"usual_disposable_income", "expected_one_off_income"}:
        fact_type = cast(IncomeFactType, question.fact_type)
        if action == "delete":
            income_repo.delete(fact_type)
        else:
            income_repo.mark_to_confirm(fact_type)
        advice_repo.delete_depending_on_declared_fact(fact_type)
    elif question.fact_type in {"recurring_obligation", "one_off_obligation"} and contradiction.fact_id is not None:
        if action == "delete":
            commitment_repo.delete(contradiction.fact_id)
        else:
            commitment_repo.mark_to_confirm(contradiction.fact_id)
        advice_repo.delete_depending_on_commitment(contradiction.fact_id, question.fact_type)


def validate_income_usage(
    advice: AdviceResponse,
    contexts: list[IncomeFactContext],
    year: int,
    month: int,
) -> None:
    """Reject inactive, untraced, or inconsistent income use.

    Parameters
    ----------
    advice : AdviceResponse
        Parsed generator output.
    contexts : list[IncomeFactContext]
        Current declared income.
    year : int
        Advice year.
    month : int
        Advice month.

    Raises
    ------
    AdviceParseError
        Income dependency lacks active matching normalization.
    """
    active = {
        context.fact_type: context for context in contexts if context.state in {"active", "corrected", "session"}
    }
    rules = {
        "weekly": ("weekly_x_52_div_12", 52 / 12),
        "biweekly": ("biweekly_x_26_div_12", 26 / 12),
        "monthly": ("monthly", 1),
        "quarterly": ("quarterly_div_3", 1 / 3),
        "yearly": ("yearly_div_12", 1 / 12),
    }
    for output in advice.outputs:
        if output.type == "clarification":
            continue
        citations = [
            citation for citation in output.trace.details.declared_facts if isinstance(citation, IncomeFactCitation)
        ]
        normalizations = output.trace.details.income_normalizations
        if (
            output.type == "recommendation"
            and output.income_dependent != bool(citations)
            or len(normalizations) != len(citations)
        ):
            raise AdviceParseError(advice.model_dump_json())
        for citation in citations:
            source = active.get(citation.fact_type)
            normalization = next(
                (item for item in normalizations if item.fact_type == citation.fact_type),
                None,
            )
            if source is None or normalization is None:
                raise AdviceParseError(advice.model_dump_json())
            if citation.fact_type == "expected_one_off_income":
                expected_conversion = "one_off"
                expected_amount = citation.amount
                expected_period = citation.expected_date.isoformat() if citation.expected_date else ""
            else:
                rule = rules.get(citation.frequency or "")
                if rule is None:
                    raise AdviceParseError(advice.model_dump_json())
                expected_conversion, factor = rule
                expected_amount = citation.amount * factor
                expected_period = f"{year}-{month:02d}"
            if (
                citation.amount != source.amount
                or citation.frequency != source.frequency
                or citation.expected_date != source.expected_date
                or citation.matched_transaction != source.matched_transaction
                or normalization.source_amount != citation.amount
                or normalization.source_frequency != citation.frequency
                or normalization.conversion != expected_conversion
                or normalization.period != expected_period
                or not isclose(normalization.normalized_amount, expected_amount, rel_tol=0, abs_tol=0.005)
                or not output.trace.details.calculations
                or not output.trace.details.conventions
            ):
                raise AdviceParseError(advice.model_dump_json())


def validate_constraint_usage(
    advice: AdviceResponse,
    contexts: list[ConstraintFactContext],
) -> None:
    """Reject forged, unavailable, untraced, or out-of-bounds recommendations.

    Parameters
    ----------
    advice : AdviceResponse
        Parsed generator output.
    contexts : list[ConstraintFactContext]
        Current declared constraints.

    Raises
    ------
    AdviceParseError
        Constraint is forged, omitted, unavailable, or violated.
    """
    active = [context for context in contexts if context.state in {"active", "corrected", "session"}]
    financial_limits = [context for context in active if isinstance(context, FinancialLimitContext)]
    unavailable_actions = [context for context in active if isinstance(context, ActionUnavailabilityContext)]
    for output in advice.outputs:
        if output.type == "clarification":
            continue
        citations = [
            citation
            for citation in output.trace.details.declared_facts
            if isinstance(citation, (FinancialLimitCitation, ActionUnavailabilityCitation))
        ]
        for citation in citations:
            source = next((context for context in active if _same_constraint(context, citation)), None)
            if source is None or citation.model_dump(exclude={"can_correct", "can_delete"}) != source.model_dump():
                raise AdviceParseError(advice.model_dump_json())
            if output.type != "recommendation":
                continue
            if isinstance(citation, ActionUnavailabilityCitation):
                raise AdviceParseError(advice.model_dump_json())
            if output.subject is None or output.subject.strip().casefold() != citation.scope.strip().casefold():
                raise AdviceParseError(advice.model_dump_json())

        if output.type != "recommendation":
            continue
        if financial_limits and output.subject is None:
            raise AdviceParseError(advice.model_dump_json())
        if any(
            output.action.strip().casefold() == unavailable.action.strip().casefold()
            for unavailable in unavailable_actions
        ):
            raise AdviceParseError(advice.model_dump_json())
        for limit in financial_limits:
            if output.subject is None or output.subject.strip().casefold() != limit.scope.strip().casefold():
                continue
            if not any(
                isinstance(citation, FinancialLimitCitation) and _same_constraint(limit, citation)
                for citation in citations
            ):
                raise AdviceParseError(advice.model_dump_json())
            if output.amount is None:
                continue
            if (
                limit.limit_type in {"cap", "sustainable_amount"}
                and output.amount > limit.amount
                or limit.limit_type == "floor"
                and output.amount < limit.amount
            ):
                raise AdviceParseError(advice.model_dump_json())


_COUNTER_ENTRY_MARKERS = ("annulation", "remboursement", "rejet", "contre-écriture", "contre ecriture")


def _structural_transaction_links(
    transactions: list[Transaction],
    targets: list[Transaction],
) -> list[tuple[Transaction, Transaction, str]]:
    """Match opposite entries with structural evidence.

    Parameters
    ----------
    transactions : list[Transaction]
        Available source transactions.
    targets : list[Transaction]
        Explicitly confirmed transactions.

    Returns
    -------
    list[tuple[Transaction, Transaction, str]]
        Target, linked transaction, and link kind.
    """
    links: list[tuple[Transaction, Transaction, str]] = []
    seen: set[tuple[int, int]] = set()
    for target in targets:
        for candidate in transactions:
            pair = (min(target.id, candidate.id), max(target.id, candidate.id))
            if target.id == candidate.id or pair in seen:
                continue
            if abs((target.date - candidate.date).days) > 31 or round(target.amount + candidate.amount, 2) != 0:
                continue
            if target.account is not None and candidate.account is not None and target.account != candidate.account:
                signal_type = "paired_transfer"
            elif (
                target.account is not None
                and target.account == candidate.account
                and any(marker in candidate.description.casefold() for marker in _COUNTER_ENTRY_MARKERS)
            ):
                signal_type = "counter_entry"
            else:
                continue
            seen.add(pair)
            links.append((target, candidate, signal_type))
    return links


def save_period_coverage_answer(
    fact_repo: ObservationFactRepository,
    advice_repo: AdviceRepository,
    coverage_months: list[str],
    complete: bool,
    missing_elements: list[str],
) -> None:
    """Persist one exact-window coverage answer.

    Parameters
    ----------
    advice_repo : AdviceRepository
        Generated advice persistence.
    fact_repo : ObservationFactRepository
        Observation persistence.
    coverage_months : list[str]
        Exact confirmed months.
    complete : bool
        Complete and gap-free marker.
    missing_elements : list[str]
        Known omissions.
    """
    fact_repo.put_period_coverage(coverage_months, complete, missing_elements)
    advice_repo.delete_all()


def save_transaction_nature_answer(
    fact_repo: ObservationFactRepository,
    advice_repo: AdviceRepository,
    transaction_repo: TransactionRepository,
    transaction_ids: list[int],
    nature: TransactionNature,
    scope: Literal["occurrence", "series"],
) -> None:
    """Persist one occurrence or explicit-series meaning answer.

    Parameters
    ----------
    fact_repo : ObservationFactRepository
        Observation persistence.
    advice_repo : AdviceRepository
        Generated advice persistence.
    transaction_repo : TransactionRepository
        Source transaction persistence.
    transaction_ids : list[int]
        Explicitly confirmed occurrence IDs.
    nature : TransactionNature
        Confirmed financial nature.
    scope : Literal["occurrence", "series"]
        Narrow confirmation scope.

    Raises
    ------
    TransactionNotFoundError
        If an explicit occurrence no longer exists.
    """
    all_transactions = transaction_repo.get_all()
    by_id = {transaction.id: transaction for transaction in all_transactions}
    try:
        selected_transactions = [by_id[transaction_id] for transaction_id in transaction_ids]
    except KeyError as error:
        raise TransactionNotFoundError(int(error.args[0])) from error
    fact_repo.put_transaction_nature(
        selected_transactions,
        nature,
        scope,
        transaction_link_keys(fact_repo, all_transactions, selected_transactions),
    )
    advice_repo.delete_all()


def transaction_link_keys(
    fact_repo: ObservationFactRepository,
    transactions: list[Transaction],
    targets: list[Transaction],
) -> list[str]:
    """Return structural links acknowledged by current answer.

    Parameters
    ----------
    fact_repo : ObservationFactRepository
        Stable transaction-key provider.
    transactions : list[Transaction]
        Available source transactions.
    targets : list[Transaction]
        Explicitly confirmed transactions.

    Returns
    -------
    list[str]
        Stable linked-transaction keys.
    """
    return [fact_repo.transaction_key(linked) for _, linked, _ in _structural_transaction_links(transactions, targets)]


def prepare_transaction_nature_context(
    fact_repo: ObservationFactRepository,
    transactions: list[Transaction],
) -> tuple[list[TransactionNatureContext], list[TransactionNatureSignal]]:
    """Load durable occurrence facts and structural contradictions.

    Parameters
    ----------
    fact_repo : ObservationFactRepository
        Observation persistence.
    transactions : list[Transaction]
        Available source transactions.

    Returns
    -------
    tuple[list[TransactionNatureContext], list[TransactionNatureSignal]]
        Active facts and new contradictions.
    """
    by_key = {fact_repo.transaction_key(transaction): transaction for transaction in transactions}
    contexts: list[TransactionNatureContext] = []
    signals: list[TransactionNatureSignal] = []
    for fact in fact_repo.get_transaction_natures():
        targets = [by_key[key] for key in fact.transaction_keys if key in by_key]
        if not targets:
            continue
        new_links = [
            link
            for link in _structural_transaction_links(transactions, targets)
            if fact_repo.transaction_key(link[1]) not in fact.acknowledged_links
        ]
        state = "to_confirm" if new_links else fact.state
        contexts.append(
            TransactionNatureContext(
                fact_id=fact.id,
                transaction_ids=[transaction.id for transaction in targets],
                source_months=sorted({f"{transaction.date:%Y-%m}" for transaction in targets}),
                nature=cast(Any, fact.nature),
                scope=cast(Any, fact.scope),
                state=cast(Any, state),
                last_confirmed_at=fact.last_confirmed_at,
            )
        )
        signals.extend(
            TransactionNatureSignal(
                signal_type=cast(Any, signal_type),
                transaction_ids=[target.id],
                linked_transaction_ids=[linked.id],
                fact_id=fact.id,
            )
            for target, linked, signal_type in new_links
        )
    return contexts, signals


def _period_coverage_context(
    fact: PeriodCoverageFact,
    evidence: list[ImportCoverageEvidence],
) -> PeriodCoverageContext:
    """Map persisted coverage and newer provenance.

    Parameters
    ----------
    fact : PeriodCoverageFact
        Exact-window coverage fact.
    evidence : list[ImportCoverageEvidence]
        Current import provenance.

    Returns
    -------
    PeriodCoverageContext
        Coverage context, reopened after newer source limits.
    """
    stale_issue = any(
        item.issue is not None and item.revision > fact.source_revisions.get(f"{item.year:04d}-{item.month:02d}", 0)
        for item in evidence
    )
    state: Literal["active", "corrected", "to_confirm"] = (
        "to_confirm" if stale_issue else "corrected" if fact.state == "corrected" else "active"
    )
    return PeriodCoverageContext(
        coverage_months=fact.coverage_months,
        accounts=fact.accounts,
        complete=fact.complete,
        missing_elements=fact.missing_elements,
        state=state,
        last_confirmed_at=fact.last_confirmed_at,
        provenance_issues=sorted(
            {
                item.issue
                for item in evidence
                if item.issue is not None
                and item.revision > fact.source_revisions.get(f"{item.year:04d}-{item.month:02d}", 0)
            }
        ),
    )


def prepare_observation_context(
    fact_repo: ObservationFactRepository,
    transaction_repo: TransactionRepository,
    generation_months: list[MonthData],
) -> AdviceContext:
    """Build observation coverage and transaction-meaning context.

    Parameters
    ----------
    fact_repo : ObservationFactRepository
        Coverage and meaning persistence.
    transaction_repo : TransactionRepository
        Source transaction persistence.
    generation_months : list[MonthData]
        Exact analyzed months.

    Returns
    -------
    AdviceContext
        Observation fields for advice generation.
    """
    analysis_months = [f"{month.year:04d}-{month.month:02d}" for month in generation_months]
    period_coverage = fact_repo.get_period_coverage(analysis_months)
    coverage_evidence = fact_repo.get_import_evidence(analysis_months)
    new_coverage_evidence = (
        coverage_evidence
        if period_coverage is None
        else [
            item
            for item in coverage_evidence
            if item.revision > period_coverage.source_revisions.get(f"{item.year:04d}-{item.month:02d}", 0)
        ]
    )
    provenance_issues = sorted({item.issue for item in new_coverage_evidence if item.issue is not None})
    coverage_signals = (
        [
            PeriodCoverageSignal(
                coverage_months=analysis_months,
                provenance_issues=provenance_issues,
                details=[detail for item in new_coverage_evidence for detail in item.issue_details],
            )
        ]
        if provenance_issues
        else []
    )
    analysis_month_set = set(analysis_months)
    analysis_transactions = [
        transaction
        for transaction in transaction_repo.get_all()
        if f"{transaction.month.year:04d}-{transaction.month.month:02d}" in analysis_month_set
    ]
    transaction_natures, transaction_nature_signals = prepare_transaction_nature_context(
        fact_repo,
        analysis_transactions,
    )
    return AdviceContext(
        period_coverages=(
            [_period_coverage_context(period_coverage, coverage_evidence)] if period_coverage is not None else []
        ),
        coverage_signals=coverage_signals,
        transaction_natures=transaction_natures,
        transaction_nature_signals=transaction_nature_signals,
    )


def enforce_observation_coverage(
    advice: AdviceResponse,
    period_coverages: list[PeriodCoverageContext],
) -> AdviceResponse:
    """Reject nonlocal evidence without complete coverage.

    Parameters
    ----------
    advice : AdviceResponse
        Generated decision outputs.
    period_coverages : list[PeriodCoverageContext]
        Confirmed exact-window coverage.

    Returns
    -------
    AdviceResponse
        Outputs with unsupported conclusions unresolved.
    """
    complete_months = {
        month
        for coverage in period_coverages
        if coverage.state != "to_confirm" and coverage.complete
        for month in coverage.coverage_months
    }
    outputs: list[DecisionOutput] = []

    for output in advice.outputs:
        if output.type == "clarification":
            outputs.append(output)
            continue
        invalid = any(
            observation.evidence_type != "presence" and not set(observation.source_months).issubset(complete_months)
            for observation in output.trace.details.observations
        )
        if not invalid:
            outputs.append(output)
            continue
        details = output.trace.details.model_copy(
            update={
                "limits": [
                    *output.trace.details.limits,
                    "Périmètre incomplet : absence, agrégat ou comparaison non étayé.",
                ]
            }
        )
        outputs.append(
            UnresolvedOutput(
                type="unresolved",
                priority=output.priority,
                conclusion="La couverture incomplète ne permet pas cette conclusion.",
                trace=output.trace.model_copy(update={"details": details}),
            )
        )
    return AdviceResponse(outputs=outputs)


def resolve_clarification(
    advice: AdviceResponse,
    year: int,
    month: int,
    action: Literal["skip", "unknown", "delete"],
) -> AdviceResponse:
    """Replace declared-fact question with persisted abstention.

    Parameters
    ----------
    advice : AdviceResponse
        Advice containing blocked subject.
    year : int
        Advice year.
    month : int
        Advice month.
    action : Literal["skip", "unknown", "delete"]
        User abstention or deletion.

    Returns
    -------
    AdviceResponse
        Same outputs with question replaced in place.
    """
    outputs: list[DecisionOutput] = []
    transition: str | None = None
    for output in advice.outputs:
        if output.type != "clarification":
            outputs.append(output)
            continue
        if output.contradiction is not None:
            transition = {
                "skip": "Contradiction passée : fait rendu à confirmer et neutralisé.",
                "unknown": "Contradiction inconnue : fait rendu à confirmer et neutralisé.",
                "delete": "Contradiction supprimée : fait supprimé sans ancienne valeur réactivable.",
            }[action]
        label = {
            "active_priority": "priorité active",
            "liquid_reserve": "réserve liquide non affectée",
            "safety_floor": "plancher de sécurité",
            "priority_allocation": "montant déjà affecté",
            "recurring_obligation": "obligation récurrente",
            "one_off_obligation": "obligation ponctuelle",
            "debt_position": "position de dette",
            "debt_terms": "conditions de dette",
            "usual_disposable_income": "revenu disponible habituel",
            "expected_one_off_income": "entrée exceptionnelle attendue",
            "financial_limit": "limite financière",
            "action_unavailability": "indisponibilité d'action",
        }[output.fact_type]
        limit = (
            f"Information non fournie ({label}) : question passée."
            if action == "skip"
            else f"Information inconnue ({label}) selon la réponse explicite."
        )
        evidence_periods = output.contradiction.period if output.contradiction is not None else [f"{year}-{month:02d}"]
        outputs.append(
            UnresolvedOutput(
                type="unresolved",
                priority=output.priority,
                conclusion=f"{output.subject} : aucune action robuste sans {label}.",
                trace=DecisionTrace(
                    summary=output.possible_effect,
                    details=DecisionTraceDetails(
                        observations=[
                            ObservedFact(
                                fact=output.observation,
                                period=" à ".join(evidence_periods),
                                scope=output.subject,
                                source="observed_data",
                                evidence_type="presence",
                                source_months=evidence_periods,
                                transaction_ids=output.transaction_ids or [],
                            )
                        ],
                        limits=[limit],
                    ),
                ),
            )
        )
    resolved = AdviceResponse(outputs=outputs)
    return record_advice_transition(resolved, transition) if transition is not None else resolved
