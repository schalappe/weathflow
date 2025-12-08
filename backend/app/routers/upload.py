"""FastAPI router for CSV upload and categorization endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.upload import CategorizeResponse, ImportMode, UploadResponse
from app.services.exceptions import (
    CategorizationError,
    CSVParseError,
    InvalidMonthFormatError,
    NoTransactionsFoundError,
)
from app.services.upload import UploadService

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
        "replace" deletes existing month data; "merge" skips duplicates.

    Returns
    -------
    CategorizeResponse
        Results with month scores and API call count.

    Raises
    ------
    HTTPException 400
        If CSV format is invalid or month format is incorrect.
    HTTPException 502
        If Claude API is unavailable.
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
            db=db,
        )
        return CategorizeResponse(**result)
    except (CSVParseError, NoTransactionsFoundError, InvalidMonthFormatError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except CategorizationError as e:
        raise HTTPException(status_code=502, detail="Categorization service unavailable") from e
