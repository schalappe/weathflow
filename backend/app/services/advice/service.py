"""Advice storage and generation-data services."""

from datetime import UTC
from math import isclose
from typing import Any, Literal, cast

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.advice import Advice
from app.db.models.commitment_fact import CommitmentFact
from app.db.models.income_fact import IncomeFact
from app.db.models.month import Month
from app.db.models.transaction import Transaction
from app.repositories.advice import AdviceRepository
from app.repositories.commitment_fact import CommitmentFactRepository, CommitmentFactType
from app.repositories.income_fact import IncomeFactRepository, IncomeFactType
from app.services.advice.models import (
    AdviceResponse,
    CommitmentFactContext,
    DecisionOutput,
    DecisionTrace,
    DecisionTraceDetails,
    IncomeFactCitation,
    IncomeFactContext,
    MonthData,
    ObservedFact,
    TransactionSample,
    UnresolvedOutput,
)
from app.services.calculation.service import calculate_month_stats
from app.services.exceptions import AdviceParseError, AdviceQueryError


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
                            )
                        ],
                        limits=[limit],
                    ),
                ),
            )
        )
    return AdviceResponse(outputs=outputs)
