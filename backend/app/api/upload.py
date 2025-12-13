"""FastAPI router for CSV upload and categorization endpoints."""

# ruff: noqa: B008

from fastapi import File, HTTPException, Query, UploadFile
from loguru import logger

from app.api.deps import MonthRepo, TransactionRepo, UploadSvc, create_router
from app.responses.upload import CategorizeResponse, ImportMode, UploadResponse
from app.services.exceptions import (
    APIConnectionError,
    BatchCategorizationError,
    CategorizationError,
    CSVParseError,
    InvalidMonthFormatError,
    InvalidResponseError,
    NoTransactionsFoundError,
    ScoreCalculationError,
    UploadPersistenceError,
)

router = create_router("upload", prefix="/api")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    service: UploadSvc,
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    Upload a Bankin' CSV file and return a preview of detected months.

    Parameters
    ----------
    file : UploadFile
        CSV file in Bankin' export format.

    Returns
    -------
    UploadResponse
        Preview with month summaries and transaction lists.

    Raises
    ------
    HTTPException 400
        If CSV format is invalid, missing columns, or empty.
    """
    try:
        content = await file.read()
        result = service.get_upload_preview(content)
        return UploadResponse(**result)
    except (CSVParseError, NoTransactionsFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unexpected error in upload_file: error_type={}", type(error).__name__)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from error


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize_file(
    month_repo: MonthRepo,
    transaction_repo: TransactionRepo,
    service: UploadSvc,
    file: UploadFile = File(...),
    months_to_process: str = Query(..., description="Comma-separated months (YYYY-MM) or 'all'"),
    import_mode: ImportMode = Query(..., description="Import mode: 'replace' or 'merge'"),
) -> CategorizeResponse:
    """
    Categorize transactions from CSV and persist to database.

    Parameters
    ----------
    file : UploadFile
        CSV file in Bankin' export format.
    months_to_process : str
        Comma-separated list of months (YYYY-MM format) or "all".
    import_mode : ImportMode
        "replace" deletes existing month and all its transactions, creating fresh.
        "merge" preserves existing month and transactions, only adding new ones.

    Returns
    -------
    CategorizeResponse
        Results with month scores, months_not_found, and API call count.

    Raises
    ------
    HTTPException 400
        If CSV format is invalid, month format is incorrect, or no transactions found.
    HTTPException 500
        If score calculation fails.
    HTTPException 502
        If Claude API is unavailable, returns invalid response, or API key missing.
    """
    # ##>: Parse comma-separated months into list.
    if months_to_process.lower() == "all":
        months_list = ["all"]
    else:
        months_list = [m.strip() for m in months_to_process.split(",") if m.strip()]

    if not months_list:
        raise HTTPException(status_code=400, detail="No valid months provided")

    try:
        content = await file.read()
        result = service.process_categorization(
            file_content=content,
            months_to_process=months_list,
            import_mode=import_mode,
            month_repo=month_repo,
            transaction_repo=transaction_repo,
        )
        return CategorizeResponse(**result)
    except (CSVParseError, NoTransactionsFoundError, InvalidMonthFormatError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except APIConnectionError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Claude API unreachable after {error.retry_count} retries. Please try again later.",
        ) from error
    except InvalidResponseError as error:
        raise HTTPException(
            status_code=502, detail="Claude returned an invalid response. Please try again or contact support."
        ) from error
    except BatchCategorizationError as error:
        raise HTTPException(
            status_code=502, detail=f"Failed to categorize {len(error.failed_ids)} transactions."
        ) from error
    except CategorizationError as error:
        # ##>: Generic CategorizationError (e.g., missing API key).
        raise HTTPException(status_code=502, detail=str(error)) from error
    except UploadPersistenceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except ScoreCalculationError as error:
        raise HTTPException(status_code=500, detail=f"Failed to calculate month score: {error}") from error
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unexpected error in categorize_file: error_type={}", type(error).__name__)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from error
