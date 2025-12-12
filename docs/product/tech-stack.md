# Tech Stack

## Overview

Money Map Manager uses a decoupled frontend/backend architecture with Next.js for the UI and FastAPI for the API. All data is stored locally in SQLite for privacy.

## Frontend

| Category   | Technology           | Version | Purpose                                         |
| ---------- | -------------------- | ------- | ----------------------------------------------- |
| Framework  | Next.js (App Router) | 14+     | React framework with SSR and file-based routing |
| Language   | TypeScript           | 5.x     | Type safety and better DX                       |
| Styling    | Tailwind CSS         | 3.x     | Utility-first CSS framework                     |
| Components | shadcn/ui            | latest  | Pre-built accessible components                 |
| Charts     | Recharts             | 2.x     | React-native charting library                   |
| Runtime    | bun                  | latest  | Fast JS runtime and package manager             |

### Frontend Conventions

- Use App Router (`app/` directory) for all pages
- Client components only when necessary (`'use client'`)
- API calls via a centralized `lib/api-client.ts`
- Types defined in `types/index.ts`
- Components organized by feature: `components/{feature}/`

## Backend

| Category        | Technology | Version | Purpose                                  |
| --------------- | ---------- | ------- | ---------------------------------------- |
| Framework       | FastAPI    | 0.115+  | Modern async Python web framework        |
| Language        | Python     | 3.12+   | Primary backend language                 |
| Server          | Uvicorn    | 0.32+   | ASGI server for FastAPI                  |
| Validation      | Pydantic   | 2.10+   | Data validation and serialization        |
| Package Manager | uv         | latest  | Fast Python package manager (Rust-based) |

### Backend Conventions

- Line length: 119 characters
- Type annotations required on all functions
- NumPy-style docstrings for public functions
- Import organization: stdlib → third-party → local
- Modern union syntax: `str | None` (not `Union[str, None]`)

## Database

| Category     | Technology | Version | Purpose                       |
| ------------ | ---------- | ------- | ----------------------------- |
| Database     | SQLite     | 3.x     | Local file-based database     |
| ORM          | SQLAlchemy | 2.0+    | Python ORM with async support |
| Async Driver | aiosqlite  | 0.20+   | Async SQLite access           |

### Database Conventions

- Use `Base.metadata.create_all()` for table creation (no migrations for MVP)
- Index foreign keys and commonly queried fields
- Store database at `data/moneymap.db`
- Use repository pattern for data access

## AI Integration

| Category | Technology               | Version | Purpose                                   |
| -------- | ------------------------ | ------- | ----------------------------------------- |
| Provider | Anthropic Claude         | -       | LLM for categorization and advice         |
| SDK      | anthropic                | 0.39+   | Official Python SDK                       |
| Model    | claude-sonnet-4-20250514 | -       | Best cost/quality ratio for this use case |

### AI Conventions

- Batch transactions (50 per API call) to reduce costs
- Cache recurring transaction patterns when possible
- Return structured JSON from all Claude calls
- Include confidence scores in categorization responses

## Development Tools

| Category      | Technology     | Purpose                                     |
| ------------- | -------------- | ------------------------------------------- |
| Linting       | ruff           | Fast Python linter (replaces flake8, isort) |
| Formatting    | ruff format    | Python code formatting                      |
| Type Checking | mypy           | Static type analysis                        |
| Testing       | pytest         | Python test framework                       |
| Async Testing | pytest-asyncio | Async test support                          |
| HTTP Client   | httpx          | Async HTTP client for testing               |

## Architecture Patterns

### Clean Architecture Layers

```text
┌─────────────────────────────────────┐
│   Presentation (FastAPI Routers)    │
├─────────────────────────────────────┤
│   Application (Services)            │
├─────────────────────────────────────┤
│   Domain (Models, Business Logic)   │
├─────────────────────────────────────┤
│   Infrastructure (DB, External APIs)│
└─────────────────────────────────────┘
```

### Key Patterns

- **Repository Pattern**: All database operations through `db/crud.py`
- **Service Layer**: Business logic in `services/` (not in routers)
- **Dependency Injection**: FastAPI's `Depends()` for DB sessions

## Project Structure

```text
money-map-manager/
├── frontend/          # Next.js app (bun)
│   ├── app/           # Pages and API routes
│   ├── components/    # React components by feature
│   ├── lib/           # Utilities and API client
│   └── types/         # TypeScript types
├── backend/           # FastAPI app (uv)
│   └── app/
│       ├── routers/   # API endpoints
│       ├── services/  # Business logic
│       └── db/        # Models and CRUD
├── data/              # SQLite database
└── Makefile           # Unified commands
```

## Environment Variables

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Backend
DATABASE_URL=sqlite:///./data/moneymap.db
BACKEND_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Commands

```bash
# Installation
cd backend && uv sync
cd frontend && bun install

# Development
make dev              # Start both servers
make dev-backend      # Backend only (port 8000)
make dev-frontend     # Frontend only (port 3000)

# Quality
cd backend && uv run ruff check .
cd backend && uv run mypy .
cd backend && uv run pytest

# Database
make reset-db         # Delete and recreate database
```
