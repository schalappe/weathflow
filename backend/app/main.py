"""FastAPI application entry point for Money Map Manager API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.db.database import init_db
from app.routers import upload


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: initialize database on startup."""
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title="Money Map Manager API",
    description="API for uploading Bankin' CSV exports and categorizing transactions",
    version="1.0.0",
    lifespan=lifespan,
)

# ##>: Configure CORS for local development with Next.js frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
