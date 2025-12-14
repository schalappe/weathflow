# Money Map Manager

A personal finance web application that automates transaction categorization using the Money Map (50/30/20) framework.

## Features

- **CSV Import** - Upload Bankin' exports with automatic month detection
- **AI Categorization** - Claude-powered transaction categorization into Core, Choice, Compound
- **Score Tracking** - Automatic Money Map score (0-3) based on 50/30/20 targets
- **Historical Analysis** - Track spending trends and score evolution over time
- **Personalized Advice** - AI-generated recommendations based on spending patterns

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/your-org/money-map-manager.git
cd money-map-manager
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 2. Install dependencies
cd backend && uv sync
cd ../frontend && bun install

# 3. Start development servers
make dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Tech Stack

| Layer    | Technology               |
| -------- | ------------------------ |
| Frontend | Next.js 14+ (App Router) |
| Backend  | FastAPI + Python 3.12+   |
| Database | SQLite + SQLAlchemy 2.0  |
| AI       | Anthropic Claude API     |
| UI       | Tailwind CSS + shadcn/ui |

## Project Structure

```text
money-map-manager/
├── frontend/         # Next.js app (bun)
├── backend/          # FastAPI app (uv)
├── data/             # SQLite database
└── docs/             # Documentation
    ├── product/      # Product specs
    └── technical/    # Technical docs
```

## Commands

```bash
make dev              # Start both servers
make dev-backend      # Backend only (port 8000)
make dev-frontend     # Frontend only (port 3000)
make reset-db         # Reset database

# Backend quality
cd backend && uv run ruff check .
cd backend && uv run mypy .
cd backend && uv run pytest

# Frontend quality
cd frontend && bun run lint
cd frontend && bun test
```

## Documentation

- [Product Mission](docs/product/mission.md) - What we're building and why
- [Tech Stack](docs/product/tech-stack.md) - Technology choices
- [Backend Architecture](docs/technical/backend-architecture.md) - API and services
- [Frontend Architecture](docs/technical/frontend-architecture.md) - Components and state
- [API Reference](docs/technical/api-reference.md) - REST endpoints

## Money Map Framework

| Category     | Target | Description         |
| ------------ | ------ | ------------------- |
| **Core**     | ≤ 50%  | Necessities         |
| **Choice**   | ≤ 30%  | Wants/discretionary |
| **Compound** | ≥ 20%  | Savings/investments |

Score: 0-3 based on meeting each threshold.

## License

MIT License - see [LICENSE](LICENSE) for details.
