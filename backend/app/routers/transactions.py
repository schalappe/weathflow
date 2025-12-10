"""FastAPI router for Transaction API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.transaction import Transaction
from app.responses.months import MonthSummary, TransactionResponse
from app.responses.transactions import UpdateTransactionRequest, UpdateTransactionResponse
from app.services import transactions as transactions_service
from app.services.exceptions import InvalidSubcategoryError, TransactionNotFoundError

# ruff: noqa: B008

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)


@router.patch("/{transaction_id}", response_model=UpdateTransactionResponse)
def update_transaction(
    request: UpdateTransactionRequest,
    transaction_id: int = Path(..., ge=1, description="Transaction ID"),
    db: Session = Depends(get_db),
) -> UpdateTransactionResponse:
    """
    Update a transaction's Money Map category and subcategory.

    Updates the transaction, sets is_manually_corrected to true,
    and recalculates the month's statistics.

    Parameters
    ----------
    transaction_id : int
        ID of the transaction to update.
    request : UpdateTransactionRequest
        New category and subcategory values.

    Returns
    -------
    UpdateTransactionResponse
        Updated transaction and recalculated month statistics.

    Raises
    ------
    HTTPException 400
        If subcategory is invalid for the given type.
    HTTPException 404
        If transaction not found.
    HTTPException 500
        If an unexpected error occurs.
    """
    try:
        transaction, month = transactions_service.update_transaction_category(
            db=db,
            transaction_id=transaction_id,
            money_map_type=request.money_map_type,
            money_map_subcategory=request.money_map_subcategory,
        )

        # ##>: Get transaction count via explicit query to avoid lazy load.
        transaction_count = db.query(func.count(Transaction.id)).filter(Transaction.month_id == month.id).scalar()

        return UpdateTransactionResponse(
            success=True,
            transaction=TransactionResponse.from_model(transaction),
            updated_month_stats=MonthSummary.from_model(month, transaction_count),
        )
    except TransactionNotFoundError as error:
        logger.warning("Transaction not found: transaction_id=%d", transaction_id)
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with id={transaction_id} not found.",
        ) from error
    except InvalidSubcategoryError as error:
        logger.warning(
            "Invalid subcategory: type=%s, subcategory=%s",
            error.money_map_type,
            error.subcategory,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subcategory '{error.subcategory}' for type {error.money_map_type}.",
        ) from error
    except Exception as error:
        logger.exception(
            "Unexpected error updating transaction %d: error_type=%s",
            transaction_id,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        ) from error
