# Agent Guideline

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Money Map Manager is a personal finance web application that automates transaction categorization using the Money Map (50/30/20) framework. It imports Bankin' CSV exports, uses Claude AI for categorization, calculates budget scores, and provides personalized advice.

Before each action read the key files @docs/product/mission.md and @docs/product/tech-stack.md

## Tech Stack

| Layer    | Technology               | Package Manager |
| -------- | ------------------------ | --------------- |
| Frontend | Next.js 14+ (App Router) | bun             |
| Backend  | FastAPI + Python 3.12+   | uv              |
| Database | SQLite + SQLAlchemy 2.0+ | -               |
| AI       | Anthropic Claude API     | -               |
| UI       | Tailwind CSS + shadcn/ui | -               |
| Charts   | Recharts                 | -               |


## Architecture

```text
weathflow/
├── frontend/                 # Next.js app
│   ├── app/                  # Pages (App Router)
│   ├── components/{feature}/ # React components by feature
│   ├── lib/api-client.ts     # Centralized API client
│   └── types/index.ts        # TypeScript types
├── backend/                  # FastAPI app
│   └── app/
│       ├── routers/          # API endpoints
│       ├── services/         # Business logic
│       └── db/               # Models and CRUD
├── data/                     # SQLite database (moneymap.db)
└── docs/                     # Product documentation
```

### Clean Architecture Layers

- **Presentation**: FastAPI routers (thin controllers)
- **Application**: Services (business logic)
- **Domain**: Models, enums, business rules
- **Infrastructure**: Database, external APIs (Claude)

### Key Patterns

- Repository pattern for all database operations
- Service layer for business logic (not in routers)
- FastAPI `Depends()` for dependency injection

## Money Map Categories

| Type       | Description         | Target |
| ---------- | ------------------- | ------ |
| `INCOME`   | Revenue (salary)    | -      |
| `CORE`     | Necessities         | ≤ 50%  |
| `CHOICE`   | Wants/discretionary | ≤ 30%  |
| `COMPOUND` | Savings/investments | ≥ 20%  |
| `EXCLUDED` | Internal transfers  | -      |

Score: 0-3 based on meeting each threshold (3 = Great, 2 = Okay, 1 = Need Improvement, 0 = Poor).

## Backend Conventions

- Line length: 119 characters
- Type annotations required on all functions
- NumPy-style docstrings for public functions
- Modern union syntax: `str | None` (not `Union[str, None]`)
- SQLAlchemy 2.0+ with `Mapped` syntax
- `__init__.py` should always be empty
- Batch Claude API calls (50 transactions per request)

## Frontend Conventions

- Use App Router (`app/` directory) for all pages
- Client components only when necessary (`'use client'`)
- API calls via centralized `lib/api-client.ts`
- Types defined in `types/index.ts`
- Components organized by feature: `components/{feature}/`

## Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
DATABASE_URL=sqlite:///./data/moneymap.db
BACKEND_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```
