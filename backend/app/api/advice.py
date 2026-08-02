"""FastAPI router for Advice API endpoints."""

from datetime import UTC

from fastapi import HTTPException, Path, Response, status
from loguru import logger

from app.api.deps import (
    ActivePriorityRepo,
    AdviceGen,
    AdviceRepo,
    EmergencyFundRepo,
    MonthRepo,
    create_router,
)
from app.db.models.active_priority import ActivePriority
from app.db.models.base import utc_now
from app.db.models.emergency_fund_fact import EmergencyFundFact, EmergencyFundFactType
from app.responses.advice import (
    ActivePriorityData,
    ActivePriorityInput,
    ActivePriorityResponse,
    AdviceData,
    EligibilityInfo,
    EmergencyFundContextResponse,
    EmergencyFundFactAnswer,
    EmergencyFundFactData,
    EmergencyFundFactInput,
    EmergencyFundFactResponse,
    GenerateAdviceRequest,
    GenerateAdviceResponse,
    GetAdviceResponse,
)
from app.services.advice import service as advice_service
from app.services.advice.eligibility import check_eligibility
from app.services.advice.models import (
    ActivePriorityContext,
    AdviceContext,
    DecisionOutput,
    DecisionTrace,
    DecisionTraceDetails,
    EmergencyFundFactContext,
    ObservedFact,
    UnresolvedOutput,
)
from app.services.data import months as months_service
from app.services.exceptions import (
    AdviceAPIError,
    AdviceGenerationError,
    AdviceParseError,
    AdviceQueryError,
    InsufficientDataError,
    MonthDataError,
)

router = create_router("advice")


def _http_detail_for_advice_error(error: AdviceGenerationError) -> str:
    """
    Map advice error to user-friendly HTTP error message.

    Parameters
    ----------
    error : AdviceGenerationError
        Advice-related error from service layer.

    Returns
    -------
    str
        User-friendly error message for HTTP response.
    """
    if isinstance(error, InsufficientDataError):
        return "Not enough historical data. Please upload at least 2 months of transactions."
    if isinstance(error, AdviceAPIError):
        return "AI service temporarily unavailable. Please try again in a moment."
    if isinstance(error, AdviceParseError):
        return "AI service returned an invalid response. Please try again."
    return "An error occurred while generating advice. Please try again."


@router.post("/generate", response_model=GenerateAdviceResponse)
def generate_advice(
    request: GenerateAdviceRequest,
    month_repo: MonthRepo,
    advice_repo: AdviceRepo,
    priority_repo: ActivePriorityRepo,
    fact_repo: EmergencyFundRepo,
    generator: AdviceGen,
) -> GenerateAdviceResponse:
    """
    Generate or retrieve cached advice for a month.

    Returns cached advice if available and regenerate=False.
    Generates new advice if no cache exists or regenerate=True.

    Parameters
    ----------
    request : GenerateAdviceRequest
        Year, month, and regenerate flag.

    Returns
    -------
    GenerateAdviceResponse
        Advice with generation timestamp and cache status.

    Raises
    ------
    HTTPException 403
        If month is not eligible for advice generation.
    HTTPException 404
        If month not found.
    HTTPException 400
        If insufficient data for advice generation.
    HTTPException 500
        If stored advice data is corrupted or unexpected error.
    HTTPException 503
        If AI service or database unavailable (AdviceQueryError, MonthDataError).
    """
    try:
        # ##>: Use eager loading to fetch month with transactions in single query.
        month_record = months_service.get_month_with_transactions(month_repo, request.year, request.month)
        if month_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {request.year}-{request.month:02d}. Upload transactions first.",
            )

        # ##>: Check eligibility before proceeding.
        eligibility = check_eligibility(request.year, request.month, month_record.id, month_repo, advice_repo)
        if not eligibility.is_eligible:
            raise HTTPException(
                status_code=403,
                detail=eligibility.reason or "This month is not eligible for advice generation.",
            )
        previous_question_count = 0
        if request.active_priority is not None or request.emergency_fund_fact is not None:
            previous_advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)
            if previous_advice is not None:
                previous_data = AdviceData.model_validate_json(previous_advice.advice_text)
                previous_question = next(
                    (output for output in previous_data.outputs if output.type == "clarification"),
                    None,
                )
                if previous_question is not None:
                    previous_question_count = previous_question.question_number
        if request.active_priority is not None and request.emergency_fund_fact is not None:
            raise HTTPException(status_code=422, detail="Answer one clarification at a time.")
        if request.clarification_action is not None:
            if request.active_priority is not None or request.emergency_fund_fact is not None:
                raise HTTPException(
                    status_code=422,
                    detail="A clarification cannot be answered and skipped together.",
                )
            existing_advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)
            if existing_advice is None:
                raise HTTPException(status_code=409, detail="No clarification to resolve.")
            current_advice = AdviceData.model_validate_json(existing_advice.advice_text)
            resolved_advice = advice_service.resolve_clarification(
                current_advice,
                request.year,
                request.month,
                request.clarification_action,
            )
            advice_json = advice_service.advice_response_to_json(resolved_advice)
            stored_advice = advice_service.create_or_update_advice(
                advice_repo,
                month_record.id,
                advice_json,
            )
            return GenerateAdviceResponse(
                success=True,
                advice=resolved_advice,
                generated_at=stored_advice.generated_at,
                is_valid=True,
                was_cached=False,
            )

        stored_priority = priority_repo.get()
        if stored_priority is not None and stored_priority.state == "to_confirm" and request.active_priority is None:
            advice_repo.delete_depending_on_active_priority()

        priority_context: ActivePriorityContext | None
        if request.active_priority is not None:
            if request.remember_priority:
                advice_repo.delete_depending_on_active_priority()
                stored_priority = priority_repo.put(
                    request.active_priority.goal,
                    request.active_priority.target,
                    request.active_priority.deadline,
                )
                priority_context = _priority_context(stored_priority)
            else:
                priority_context = _session_priority_context(request.active_priority)
                if stored_priority is not None:
                    priority_repo.mark_to_confirm()
        else:
            priority_context = _priority_context(stored_priority) if stored_priority is not None else None

        emergency_fund_contexts = _prepare_emergency_fund_context(
            request,
            fact_repo,
            advice_repo,
        )

        if not request.regenerate and request.active_priority is None and request.emergency_fund_fact is None:
            existing_advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)
            if existing_advice:
                return GenerateAdviceResponse(
                    success=True,
                    advice=AdviceData.model_validate_json(existing_advice.advice_text),
                    generated_at=existing_advice.generated_at,
                    is_valid=True,
                    was_cached=True,
                )

        # ##>: Fetch history with transactions eager-loaded to avoid N+1 queries.
        # ##>: Use dynamic history limit based on eligibility (12 for first advice, 3 otherwise).
        history_months = months_service.get_months_history_with_transactions(
            month_repo, limit=eligibility.history_limit
        )

        filtered_history = [m for m in history_months if (m.year, m.month) < (request.year, request.month)]
        history_data = [advice_service.month_to_month_data(month) for month in filtered_history]
        current_data = advice_service.month_to_month_data(month_record)

        generation_context = AdviceContext(
            active_priority=priority_context,
            emergency_fund_facts=emergency_fund_contexts,
            clarifications_remaining=max(0, 3 - previous_question_count),
        )
        advice_response = generator.generate_advice(current_data, history_data, generation_context)
        advice_response = AdviceData.model_validate(advice_response)
        answered_fact_type = (
            "active_priority"
            if request.active_priority is not None
            else request.emergency_fund_fact.fact_type
            if request.emergency_fund_fact is not None
            else None
        )
        if answered_fact_type is not None:
            repeats_answered_question = any(
                output.type == "clarification" and output.fact_type == answered_fact_type
                for output in advice_response.outputs
            )
            has_next_question = any(output.type == "clarification" for output in advice_response.outputs)
            cites_answer = any(
                fact.fact_type == answered_fact_type
                for output in advice_response.outputs
                if output.type != "clarification"
                for fact in output.trace.details.declared_facts
            )
            if repeats_answered_question or (not has_next_question and not cites_answer):
                raise AdviceParseError(advice_response.model_dump_json())
        advice_response = _apply_clarification_limit(
            advice_response,
            previous_question_count,
            request.year,
            request.month,
        )

        session_only_answer = (
            request.active_priority is not None
            and not request.remember_priority
            or request.emergency_fund_fact is not None
            and not request.remember_fact
        )
        if session_only_answer:
            return GenerateAdviceResponse(
                success=True,
                advice=advice_response,
                generated_at=utc_now(),
                is_valid=True,
                was_cached=False,
            )

        advice_json = advice_service.advice_response_to_json(advice_response)
        stored_advice = advice_service.create_or_update_advice(advice_repo, month_record.id, advice_json)

        return GenerateAdviceResponse(
            success=True,
            advice=advice_response,
            generated_at=stored_advice.generated_at,
            is_valid=True,
            was_cached=False,
        )

    except HTTPException:
        raise
    except ValueError as error:
        # ##>: Catches corrupted JSON from AdviceData.from_json() when loading cached advice.
        logger.exception("Corrupted advice data for {}-{:02d}", request.year, request.month)
        raise HTTPException(
            status_code=500,
            detail="Stored advice data is corrupted. Please regenerate advice with regenerate=true.",
        ) from error
    except InsufficientDataError as error:
        logger.info("Insufficient data for advice generation: {}", error)
        raise HTTPException(status_code=400, detail=_http_detail_for_advice_error(error)) from error
    except (AdviceQueryError, MonthDataError) as error:
        logger.exception("Database error in generate_advice")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.") from error
    except AdviceGenerationError as error:
        logger.exception("Advice generation error for {}-{:02d}", request.year, request.month)
        raise HTTPException(status_code=503, detail=_http_detail_for_advice_error(error)) from error
    except Exception as error:
        logger.exception("Unexpected error in generate_advice: error_type={}", type(error).__name__)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from error


def _priority_data(priority: ActivePriority) -> ActivePriorityData:
    """Map persistence to API data.

    Parameters
    ----------
    priority : ActivePriority
        Stored priority.

    Returns
    -------
    ActivePriorityData
        UTC lifecycle data.
    """
    return ActivePriorityData.model_validate(
        {
            "goal": priority.goal,
            "target": priority.target,
            "deadline": priority.deadline,
            "state": priority.state,
            "last_confirmed_at": priority.last_confirmed_at.replace(tzinfo=UTC),
            "valid_until": priority.valid_until.replace(tzinfo=UTC),
        }
    )


def _priority_context(priority: ActivePriority) -> ActivePriorityContext:
    """Map persistence to generation context.

    Parameters
    ----------
    priority : ActivePriority
        Stored priority.

    Returns
    -------
    ActivePriorityContext
        UTC generation fact.
    """
    return ActivePriorityContext.model_validate(
        {
            "goal": priority.goal,
            "target": priority.target,
            "deadline": priority.deadline,
            "state": priority.state,
            "last_confirmed_at": priority.last_confirmed_at.replace(tzinfo=UTC),
            "valid_until": priority.valid_until.replace(tzinfo=UTC),
        }
    )


def _session_priority_context(payload: ActivePriorityInput) -> ActivePriorityContext:
    """Build request-scoped priority.

    Parameters
    ----------
    payload : ActivePriorityInput
        Explicit answer.

    Returns
    -------
    ActivePriorityContext
        Session-only fact.
    """
    return ActivePriorityContext(
        goal=payload.goal,
        target=payload.target,
        deadline=payload.deadline,
        state="session",
        last_confirmed_at=utc_now(),
        valid_until=None,
    )


def _emergency_fund_fact_data(fact: EmergencyFundFact) -> EmergencyFundFactData:
    """Map emergency-fund persistence to API data.

    Parameters
    ----------
    fact : EmergencyFundFact
        Stored lifecycle value.

    Returns
    -------
    EmergencyFundFactData
        UTC API value.
    """
    return EmergencyFundFactData.model_validate(
        {
            "fact_type": fact.fact_type,
            "amount": fact.amount,
            "state": fact.state,
            "last_confirmed_at": fact.last_confirmed_at.replace(tzinfo=UTC),
            "valid_until": fact.valid_until.replace(tzinfo=UTC),
        }
    )


def _emergency_fund_fact_context(fact: EmergencyFundFact) -> EmergencyFundFactContext:
    """Map emergency-fund persistence to generation context.

    Parameters
    ----------
    fact : EmergencyFundFact
        Stored lifecycle value.

    Returns
    -------
    EmergencyFundFactContext
        UTC generation fact.
    """
    return EmergencyFundFactContext.model_validate(
        {
            "fact_type": fact.fact_type,
            "amount": fact.amount,
            "state": fact.state,
            "last_confirmed_at": fact.last_confirmed_at.replace(tzinfo=UTC),
            "valid_until": fact.valid_until.replace(tzinfo=UTC),
        }
    )


def _session_emergency_fund_fact_context(
    payload: EmergencyFundFactAnswer,
) -> EmergencyFundFactContext:
    """Build request-scoped emergency-fund amount.

    Parameters
    ----------
    payload : EmergencyFundFactAnswer
        Explicit answer.

    Returns
    -------
    EmergencyFundFactContext
        Session-only fact.
    """
    return EmergencyFundFactContext(
        fact_type=payload.fact_type,
        amount=payload.amount,
        state="session",
        last_confirmed_at=utc_now(),
        valid_until=None,
    )


def _load_emergency_fund_facts(
    fact_repo: EmergencyFundRepo,
    advice_repo: AdviceRepo,
) -> list[EmergencyFundFact]:
    """Load facts and invalidate advice that cites expired values.

    Parameters
    ----------
    fact_repo : EmergencyFundRepo
        Declared-fact persistence.
    advice_repo : AdviceRepo
        Advice persistence.

    Returns
    -------
    list[EmergencyFundFact]
        Stored facts, including inactive expired values.
    """
    facts = fact_repo.get_all()
    for fact in facts:
        if fact.state == "to_confirm":
            advice_repo.delete_depending_on_declared_fact(fact.fact_type)
    return facts


def _prepare_emergency_fund_context(
    request: GenerateAdviceRequest,
    fact_repo: EmergencyFundRepo,
    advice_repo: AdviceRepo,
) -> list[EmergencyFundFactContext]:
    """Build generation facts from stored and request-scoped values.

    Parameters
    ----------
    request : GenerateAdviceRequest
        Current generation request.
    fact_repo : EmergencyFundRepo
        Declared-fact persistence.
    advice_repo : AdviceRepo
        Advice persistence.

    Returns
    -------
    list[EmergencyFundFactContext]
        Facts available to the current generation.
    """
    contexts = [_emergency_fund_fact_context(fact) for fact in _load_emergency_fund_facts(fact_repo, advice_repo)]
    answer = request.emergency_fund_fact
    if answer is None:
        return contexts
    contexts = [context for context in contexts if context.fact_type != answer.fact_type]
    if request.remember_fact:
        advice_repo.delete_depending_on_declared_fact(answer.fact_type)
        stored_fact = fact_repo.put(answer.fact_type, answer.amount)
        contexts.append(_emergency_fund_fact_context(stored_fact))
    else:
        fact_repo.mark_to_confirm(answer.fact_type)
        contexts.append(_session_emergency_fund_fact_context(answer))
    return contexts


def _apply_clarification_limit(
    advice: AdviceData,
    previous_count: int,
    year: int,
    month: int,
) -> AdviceData:
    """Count questions and replace a fourth question with an unresolved output.

    Parameters
    ----------
    advice : AdviceData
        Newly generated decision outputs.
    previous_count : int
        Questions already shown in this flow.
    year : int
        Advice year.
    month : int
        Advice month.

    Returns
    -------
    AdviceData
        Advice with bounded clarification count.
    """
    clarification = next(
        (output for output in advice.outputs if output.type == "clarification"),
        None,
    )
    if clarification is None:
        return advice
    if previous_count < 3:
        next_question = clarification.model_copy(update={"question_number": previous_count + 1})
        outputs: list[DecisionOutput] = [
            next_question if output.type == "clarification" else output for output in advice.outputs
        ]
        return AdviceData(outputs=outputs)

    unresolved = UnresolvedOutput(
        type="unresolved",
        priority=clarification.priority,
        conclusion=f"{clarification.subject} : information manquante après trois clarifications.",
        trace=DecisionTrace(
            summary=clarification.possible_effect,
            details=DecisionTraceDetails(
                observations=[
                    ObservedFact(
                        fact=clarification.observation,
                        period=f"{year}-{month:02d}",
                        scope=clarification.subject,
                        source="observed_data",
                    )
                ],
                limits=["Plafond de trois questions atteint."],
            ),
        ),
    )
    outputs = [unresolved if output.type == "clarification" else output for output in advice.outputs]
    return AdviceData(outputs=outputs)


@router.get("/context/active-priority", response_model=ActivePriorityResponse)
def get_active_priority(
    priority_repo: ActivePriorityRepo,
    advice_repo: AdviceRepo,
) -> ActivePriorityResponse:
    """Return priority, expiring and invalidating when stale.

    Returns
    -------
    ActivePriorityResponse
        Stored value or null.
    """
    priority = priority_repo.get()
    if priority is not None and priority.state == "to_confirm":
        advice_repo.delete_depending_on_active_priority()
    return ActivePriorityResponse(priority=_priority_data(priority) if priority is not None else None)


@router.put("/context/active-priority", response_model=ActivePriorityResponse)
def put_active_priority(
    payload: ActivePriorityInput,
    priority_repo: ActivePriorityRepo,
    advice_repo: AdviceRepo,
) -> ActivePriorityResponse:
    """Create or correct priority and invalidate dependent advice.

    Parameters
    ----------
    payload : ActivePriorityInput
        Explicit value.

    Returns
    -------
    ActivePriorityResponse
        Stored lifecycle data.
    """
    priority = priority_repo.put(payload.goal, payload.target, payload.deadline)
    advice_repo.delete_depending_on_active_priority()
    return ActivePriorityResponse(priority=_priority_data(priority))


@router.delete(
    "/context/active-priority",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_active_priority(
    priority_repo: ActivePriorityRepo,
    advice_repo: AdviceRepo,
) -> Response:
    """Delete priority and dependent advice.

    Returns
    -------
    Response
        Empty 204 response.
    """
    priority_repo.delete()
    advice_repo.delete_depending_on_active_priority()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/context/emergency-fund", response_model=EmergencyFundContextResponse)
def get_emergency_fund_context(
    fact_repo: EmergencyFundRepo,
    advice_repo: AdviceRepo,
) -> EmergencyFundContextResponse:
    """Return emergency-fund facts, visible after expiry.

    Parameters
    ----------
    fact_repo : EmergencyFundRepo
        Declared-fact persistence.
    advice_repo : AdviceRepo
        Advice persistence.

    Returns
    -------
    EmergencyFundContextResponse
        Stored values, including expired facts.
    """
    facts = _load_emergency_fund_facts(fact_repo, advice_repo)
    return EmergencyFundContextResponse(facts=[_emergency_fund_fact_data(fact) for fact in facts])


@router.put(
    "/context/emergency-fund/{fact_type}",
    response_model=EmergencyFundFactResponse,
)
def put_emergency_fund_fact(
    payload: EmergencyFundFactInput,
    fact_repo: EmergencyFundRepo,
    advice_repo: AdviceRepo,
    fact_type: EmergencyFundFactType,
) -> EmergencyFundFactResponse:
    """Create, correct, or reconfirm emergency-fund fact.

    Parameters
    ----------
    payload : EmergencyFundFactInput
        Declared euro amount.
    fact_repo : EmergencyFundRepo
        Declared-fact persistence.
    advice_repo : AdviceRepo
        Advice persistence.
    fact_type : EmergencyFundFactType
        Closed-catalog fact key.

    Returns
    -------
    EmergencyFundFactResponse
        Stored lifecycle value.
    """
    fact = fact_repo.put(fact_type, payload.amount)
    advice_repo.delete_depending_on_declared_fact(fact_type)
    return EmergencyFundFactResponse(fact=_emergency_fund_fact_data(fact))


@router.delete(
    "/context/emergency-fund/{fact_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_emergency_fund_fact(
    fact_repo: EmergencyFundRepo,
    advice_repo: AdviceRepo,
    fact_type: EmergencyFundFactType,
) -> Response:
    """Delete emergency-fund fact and dependent advice.

    Parameters
    ----------
    fact_repo : EmergencyFundRepo
        Declared-fact persistence.
    advice_repo : AdviceRepo
        Advice persistence.
    fact_type : EmergencyFundFactType
        Closed-catalog fact key.

    Returns
    -------
    Response
        Empty 204 response.
    """
    fact_repo.delete(fact_type)
    advice_repo.delete_depending_on_declared_fact(fact_type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{year}/{month}", response_model=GetAdviceResponse)
def get_advice(
    month_repo: MonthRepo,
    advice_repo: AdviceRepo,
    priority_repo: ActivePriorityRepo,
    fact_repo: EmergencyFundRepo,
    year: int = Path(..., ge=2000, le=2100, description="Year (e.g., 2025)"),
    month: int = Path(..., ge=1, le=12, description="Month number (1-12)"),
) -> GetAdviceResponse:
    """
    Retrieve stored advice for a specific month.

    Parameters
    ----------
    year : int
        Year (e.g., 2025).
    month : int
        Month number (1-12).

    Returns
    -------
    GetAdviceResponse
        Advice if exists, or exists=False if not found.

    Raises
    ------
    HTTPException 404
        If month not found in database.
    HTTPException 503
        If database unavailable.
    """
    try:
        month_record = months_service.get_month_by_year_month(month_repo, year, month)
        if month_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {year}-{month:02d}. Upload transactions first.",
            )
        priority = priority_repo.get()
        if priority is not None and priority.state == "to_confirm":
            advice_repo.delete_depending_on_active_priority()
        _load_emergency_fund_facts(fact_repo, advice_repo)

        # ##>: Check eligibility for this month.
        eligibility = check_eligibility(year, month, month_record.id, month_repo, advice_repo)
        eligibility_info = EligibilityInfo(
            can_generate=eligibility.is_eligible,
            is_first_advice=eligibility.is_first_advice,
            reason=eligibility.reason,
        )

        advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)

        if advice is None:
            return GetAdviceResponse(
                success=True,
                advice=None,
                generated_at=None,
                is_valid=False,
                exists=False,
                eligibility=eligibility_info,
            )

        return GetAdviceResponse(
            success=True,
            advice=AdviceData.model_validate_json(advice.advice_text),
            generated_at=advice.generated_at,
            is_valid=True,
            exists=True,
            eligibility=eligibility_info,
        )

    except HTTPException:
        raise
    except ValueError as error:
        # ##>: Catches corrupted JSON from AdviceData.from_json() when loading stored advice.
        logger.exception("Corrupted advice data for {}-{:02d}", year, month)
        raise HTTPException(
            status_code=500,
            detail="Stored advice data is corrupted. Please regenerate advice.",
        ) from error
    except (AdviceQueryError, MonthDataError) as error:
        logger.exception("Database error in get_advice for {}-{:02d}", year, month)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.") from error
    except Exception as error:
        logger.exception("Unexpected error in get_advice for {}-{:02d}", year, month)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from error
