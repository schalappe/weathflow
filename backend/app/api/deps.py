"""FastAPI dependency injection providers for repositories and services."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.database import get_db
from app.repositories.advice import AdviceRepository
from app.repositories.month import MonthRepository
from app.repositories.transaction import TransactionRepository
from app.services.advice.generator import AdviceGenerator
from app.services.upload.service import UploadService

# ─────────────────────────────────────────────────────────────────────────────
# Router Factory
# ─────────────────────────────────────────────────────────────────────────────


def create_router(resource: str, *, prefix: str | None = None) -> APIRouter:
    """
    Create an APIRouter with consistent configuration.

    Parameters
    ----------
    resource : str
        Resource name used for tags (e.g., "months", "transactions").
    prefix : str, optional
        URL prefix. Defaults to /api/{resource}.

    Returns
    -------
    APIRouter
        Configured router instance.
    """
    return APIRouter(
        prefix=prefix if prefix is not None else f"/api/{resource}",
        tags=[resource],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Type Aliases for Dependencies
# ─────────────────────────────────────────────────────────────────────────────

DbSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ─────────────────────────────────────────────────────────────────────────────
# Repository Providers
# ─────────────────────────────────────────────────────────────────────────────


def get_month_repository(db: DbSession) -> MonthRepository:
    """Provide MonthRepository instance."""
    return MonthRepository(db)


def get_transaction_repository(db: DbSession) -> TransactionRepository:
    """Provide TransactionRepository instance."""
    return TransactionRepository(db)


def get_advice_repository(db: DbSession) -> AdviceRepository:
    """Provide AdviceRepository instance."""
    return AdviceRepository(db)


# ─────────────────────────────────────────────────────────────────────────────
# Service Providers
# ─────────────────────────────────────────────────────────────────────────────


def get_upload_service() -> UploadService:
    """Provide UploadService instance."""
    return UploadService()


def get_advice_generator(settings: SettingsDep) -> AdviceGenerator:
    """Provide AdviceGenerator instance with API configuration."""
    return AdviceGenerator(
        api_key=settings.anthropic_api_key.get_secret_value(),
        base_url=settings.anthropic_base_url,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dependency Type Aliases for Route Handlers
# ─────────────────────────────────────────────────────────────────────────────

MonthRepo = Annotated[MonthRepository, Depends(get_month_repository)]
TransactionRepo = Annotated[TransactionRepository, Depends(get_transaction_repository)]
AdviceRepo = Annotated[AdviceRepository, Depends(get_advice_repository)]
UploadSvc = Annotated[UploadService, Depends(get_upload_service)]
AdviceGen = Annotated[AdviceGenerator, Depends(get_advice_generator)]
