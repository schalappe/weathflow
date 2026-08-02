"""FastAPI router for Advice API endpoints."""

from datetime import UTC

from fastapi import HTTPException, Path, Response, status
from loguru import logger

from app.api.deps import ActivePriorityRepo, AdviceGen, AdviceRepo, MonthRepo, create_router
from app.db.models.active_priority import ActivePriority
from app.db.models.base import utc_now
from app.responses.advice import (
    ActivePriorityData,
    ActivePriorityInput,
    ActivePriorityResponse,
    AdviceData,
    EligibilityInfo,
    GenerateAdviceRequest,
    GenerateAdviceResponse,
    GetAdviceResponse,
)
from app.services.advice import service as advice_service
from app.services.advice.eligibility import check_eligibility
from app.services.advice.models import ActivePriorityContext
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
        if request.clarification_action is not None:
            if request.active_priority is not None:
                raise HTTPException(
                    status_code=422,
                    detail="A clarification cannot be answered and skipped together.",
                )
            existing_advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)
            if existing_advice is None:
                raise HTTPException(status_code=409, detail="No priority clarification to resolve.")
            current_advice = AdviceData.model_validate_json(existing_advice.advice_text)
            resolved_advice = advice_service.resolve_priority_clarification(
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

        if not request.regenerate and request.active_priority is None:
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

        advice_response = generator.generate_advice(current_data, history_data, priority_context)
        advice_response = AdviceData.model_validate(advice_response)
        if request.active_priority is not None:
            still_blocked = any(output.type == "clarification" for output in advice_response.outputs)
            cites_answer = any(
                fact.fact_type == "active_priority"
                for output in advice_response.outputs
                if output.type != "clarification"
                for fact in output.trace.details.declared_facts
            )
            if still_blocked or not cites_answer:
                raise AdviceParseError(advice_response.model_dump_json())

        if request.active_priority is not None and not request.remember_priority:
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


@router.get("/{year}/{month}", response_model=GetAdviceResponse)
def get_advice(
    month_repo: MonthRepo,
    advice_repo: AdviceRepo,
    priority_repo: ActivePriorityRepo,
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
