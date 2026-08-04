"""FastAPI dependency injection providers for repositories and services."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.database import get_db
from app.repositories.active_priority import ActivePriorityRepository
from app.repositories.advice import AdviceRepository
from app.repositories.commitment_fact import CommitmentFactRepository
from app.repositories.constraint_fact import ConstraintFactRepository
from app.repositories.emergency_fund_fact import EmergencyFundFactRepository
from app.repositories.income_fact import IncomeFactRepository
from app.repositories.month import MonthRepository
from app.repositories.observation_fact import ObservationFactRepository
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


def get_active_priority_repository(db: DbSession) -> ActivePriorityRepository:
    """Provide active-priority repository."""
    return ActivePriorityRepository(db)


def get_emergency_fund_fact_repository(db: DbSession) -> EmergencyFundFactRepository:
    """Provide emergency-fund fact repository.

    Parameters
    ----------
    db : DbSession
        Request database transaction.

    Returns
    -------
    EmergencyFundFactRepository
        Declared-fact persistence.
    """
    return EmergencyFundFactRepository(db)


def get_commitment_fact_repository(db: DbSession) -> CommitmentFactRepository:
    """Provide obligation and debt fact repository.

    Parameters
    ----------
    db : DbSession
        Request database session.

    Returns
    -------
    CommitmentFactRepository
        Commitment persistence.
    """
    return CommitmentFactRepository(db)


def get_constraint_fact_repository(db: DbSession) -> ConstraintFactRepository:
    """Provide decision-constraint repository.

    Parameters
    ----------
    db : DbSession
        Request database session.

    Returns
    -------
    ConstraintFactRepository
        Constraint persistence.
    """
    return ConstraintFactRepository(db)


def get_income_fact_repository(db: DbSession) -> IncomeFactRepository:
    """Provide declared-income repository."""
    return IncomeFactRepository(db)


def get_observation_fact_repository(db: DbSession) -> ObservationFactRepository:
    """Provide observation validity repository.

    Parameters
    ----------
    db : DbSession
        Request database transaction.

    Returns
    -------
    ObservationFactRepository
        Observation persistence.
    """
    return ObservationFactRepository(db)


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
ActivePriorityRepo = Annotated[ActivePriorityRepository, Depends(get_active_priority_repository)]
EmergencyFundRepo = Annotated[EmergencyFundFactRepository, Depends(get_emergency_fund_fact_repository)]
CommitmentRepo = Annotated[CommitmentFactRepository, Depends(get_commitment_fact_repository)]
ConstraintRepo = Annotated[ConstraintFactRepository, Depends(get_constraint_fact_repository)]
IncomeFactRepo = Annotated[IncomeFactRepository, Depends(get_income_fact_repository)]
ObservationFactRepo = Annotated[ObservationFactRepository, Depends(get_observation_fact_repository)]
UploadSvc = Annotated[UploadService, Depends(get_upload_service)]
AdviceGen = Annotated[AdviceGenerator, Depends(get_advice_generator)]
