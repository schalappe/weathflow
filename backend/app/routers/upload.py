"""FastAPI router for CSV upload and categorization endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.month import MonthRepository
from app.repositories.transaction import TransactionRepository
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
)
from app.services.upload.service import UploadService

# ruff: noqa: B008

router = APIRouter(prefix="/api", tags=["upload"])


def _get_upload_service() -> UploadService:
    """Provide UploadService instance for dependency injection."""
    return UploadService()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    service: UploadService = Depends(_get_upload_service),
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
    except (CSVParseError, NoTransactionsFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize_file(
    file: UploadFile = File(...),
    months_to_process: str = Query(..., description="Comma-separated months (YYYY-MM) or 'all'"),
    import_mode: ImportMode = Query(..., description="Import mode: 'replace' or 'merge'"),
    db: Session = Depends(get_db),
    service: UploadService = Depends(_get_upload_service),
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
        # ##>: Create repositories and pass to service.
        month_repo = MonthRepository(db)
        transaction_repo = TransactionRepository(db)

        content = await file.read()
        result = service.process_categorization(
            file_content=content,
            months_to_process=months_list,
            import_mode=import_mode,
            month_repo=month_repo,
            transaction_repo=transaction_repo,
        )
        return CategorizeResponse(**result)
    except (CSVParseError, NoTransactionsFoundError, InvalidMonthFormatError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except APIConnectionError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Claude API unreachable after {e.retry_count} retries. Please try again later.",
        ) from e
    except InvalidResponseError as e:
        raise HTTPException(
            status_code=502, detail="Claude returned an invalid response. Please try again or contact support."
        ) from e
    except BatchCategorizationError as e:
        raise HTTPException(status_code=502, detail=f"Failed to categorize {len(e.failed_ids)} transactions.") from e
    except CategorizationError as e:
        # ##>: Generic CategorizationError (e.g., missing API key).
        raise HTTPException(status_code=502, detail=str(e)) from e
    except ScoreCalculationError as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate month score: {e}") from e
