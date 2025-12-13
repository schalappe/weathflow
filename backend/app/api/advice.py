"""FastAPI router for Advice API endpoints."""

import logging

from fastapi import HTTPException, Path

from app.api.deps import AdviceGen, AdviceRepo, MonthRepo, create_router
from app.responses.advice import (
    AdviceData,
    GenerateAdviceRequest,
    GenerateAdviceResponse,
    GetAdviceResponse,
)
from app.services.advice import service as advice_service
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
logger = logging.getLogger(__name__)


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
        month_record = months_service.get_month_by_year_month(month_repo, request.year, request.month)
        if month_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {request.year}-{request.month:02d}. Upload transactions first.",
            )

        if not request.regenerate:
            existing_advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)
            if existing_advice:
                logger.info("Returning cached advice for %d-%02d", request.year, request.month)
                return GenerateAdviceResponse(
                    success=True,
                    advice=AdviceData.from_json(existing_advice.advice_text),
                    generated_at=existing_advice.generated_at,
                    was_cached=True,
                )

        # ##>: Fetch history and prepare data for advice generation.
        history_months = months_service.get_months_history(month_repo, limit=3)

        current_data = advice_service.month_to_month_data(month_record)
        history_data = [
            advice_service.month_to_month_data(m)
            for m in history_months
            if not (m.year == request.year and m.month == request.month)
        ]

        advice_response = generator.generate_advice(current_data, history_data)

        advice_json = advice_service.advice_response_to_json(advice_response)
        stored_advice = advice_service.create_or_update_advice(advice_repo, month_record.id, advice_json)

        logger.info("Generated new advice for %d-%02d", request.year, request.month)
        return GenerateAdviceResponse(
            success=True,
            advice=AdviceData.from_service_response(advice_response),
            generated_at=stored_advice.generated_at,
            was_cached=False,
        )

    except HTTPException:
        raise
    except ValueError as error:
        # ##>: Catches corrupted JSON from AdviceData.from_json() when loading cached advice.
        logger.exception("Corrupted advice data for %d-%02d", request.year, request.month)
        raise HTTPException(
            status_code=500,
            detail="Stored advice data is corrupted. Please regenerate advice with regenerate=true.",
        ) from error
    except InsufficientDataError as error:
        logger.info("Insufficient data for advice generation: %s", error)
        raise HTTPException(status_code=400, detail=_http_detail_for_advice_error(error)) from error
    except (AdviceQueryError, MonthDataError) as error:
        logger.exception("Database error in generate_advice")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.") from error
    except AdviceGenerationError as error:
        logger.exception("Advice generation error for %d-%02d", request.year, request.month)
        raise HTTPException(status_code=503, detail=_http_detail_for_advice_error(error)) from error
    except Exception as error:
        logger.exception("Unexpected error in generate_advice: error_type=%s", type(error).__name__)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from error


@router.get("/{year}/{month}", response_model=GetAdviceResponse)
def get_advice(
    month_repo: MonthRepo,
    advice_repo: AdviceRepo,
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

        advice = advice_service.get_advice_by_month_id(advice_repo, month_record.id)

        if advice is None:
            return GetAdviceResponse(
                success=True,
                advice=None,
                generated_at=None,
                exists=False,
            )

        return GetAdviceResponse(
            success=True,
            advice=AdviceData.from_json(advice.advice_text),
            generated_at=advice.generated_at,
            exists=True,
        )

    except HTTPException:
        raise
    except ValueError as error:
        # ##>: Catches corrupted JSON from AdviceData.from_json() when loading stored advice.
        logger.exception("Corrupted advice data for %d-%02d", year, month)
        raise HTTPException(
            status_code=500,
            detail="Stored advice data is corrupted. Please regenerate advice.",
        ) from error
    except (AdviceQueryError, MonthDataError) as error:
        logger.exception("Database error in get_advice for %d-%02d", year, month)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.") from error
    except Exception as error:
        logger.exception("Unexpected error in get_advice for %d-%02d", year, month)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from error
