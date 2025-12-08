"""FastAPI application entry point for Money Map Manager API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.routers import upload

app = FastAPI(
    title="Money Map Manager API",
    description="API for uploading Bankin' CSV exports and categorizing transactions",
    version="1.0.0",
)

# ##>: Configure CORS for local development with Next.js frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)


@app.on_event("startup")
def startup() -> None:
    """Initialize database tables on application startup."""
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
