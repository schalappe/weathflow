"""Advice storage and generation-data services."""

from datetime import UTC
from math import isclose
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
    CommitmentFactContext,
    ConstraintFactContext,
    DecisionOutput,
    DecisionTrace,
    DecisionTraceDetails,
    FinancialLimitCitation,
    FinancialLimitContext,
    IncomeFactCitation,
    IncomeFactContext,
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

    Returns
    -------
    list[CommitmentFactContext]
        Context for the current generation.
    """
    contexts = load_commitment_context(fact_repo, advice_repo)
    if answer is None:
        return contexts
    matching = next(
        (context for context in contexts if context.fact_type == answer.fact_type and context.label == answer.label),
        None,
    )
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
        fields = {"fact_type", "amount", "frequency", "expected_date"}
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
                    if transaction.date == context.expected_date and transaction.amount == context.amount
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
    provenance_issues = sorted({item.issue for item in coverage_evidence if item.issue is not None})
    coverage_signals = (
        [
            PeriodCoverageSignal(
                coverage_months=analysis_months,
                provenance_issues=provenance_issues,
                details=[detail for item in coverage_evidence for detail in item.issue_details],
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
    action: Literal["skip", "unknown"],
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
    action : Literal["skip", "unknown"]
        User abstention.

    Returns
    -------
    AdviceResponse
        Same outputs with question replaced in place.
    """
    outputs: list[DecisionOutput] = []
    for output in advice.outputs:
        if output.type != "clarification":
            outputs.append(output)
            continue
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
                                period=f"{year}-{month:02d}",
                                scope=output.subject,
                                source="observed_data",
                                evidence_type="presence",
                                source_months=[f"{year}-{month:02d}"],
                                transaction_ids=output.transaction_ids or [],
                            )
                        ],
                        limits=[limit],
                    ),
                ),
            )
        )
    return AdviceResponse(outputs=outputs)
