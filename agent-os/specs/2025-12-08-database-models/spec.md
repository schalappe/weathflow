# Specification: Database Models

## Goal

Establish the data foundation for Money Map Manager by creating SQLAlchemy 2.0+ models for months, transactions, and advice tables with proper relationships, constraints, and indexes.

## User Stories

- As a developer, I want well-defined database models so that I can build CRUD operations and services on a solid foundation.
- As a developer, I want proper type annotations and relationships so that my IDE provides accurate autocompletion and type checking.

## Specific Requirements

**MoneyMapType Enum:**

- Define as `str` enum inheriting from both `str` and `Enum`
- Values: INCOME, CORE, CHOICE, COMPOUND, EXCLUDED
- Stores string values directly in SQLite for human-readable queries

**ScoreLabel Enum:**

- Define as `str` enum inheriting from both `str` and `Enum`
- Values: Poor (score 0), Need Improvement (score 1), Okay (score 2), Great (score 3)
- Used for human-readable score interpretation

**Month Model:**

- Table name: `months`
- Primary key: `id` (auto-increment integer)
- Calendar fields: `year` (int, not null), `month` (int, not null)
- Totals: `total_income`, `total_core`, `total_choice`, `total_compound` (float, default 0.0)
- Percentages: `core_percentage`, `choice_percentage`, `compound_percentage` (float, default 0.0)
- Score: `score` (int 0-3, default 0), `score_label` (string, nullable)
- Timestamps: `created_at`, `updated_at` with auto-update on `updated_at`
- Constraints: `UniqueConstraint('year', 'month')`, `Index('idx_months_year_month', 'year', 'month')`

**Transaction Model:**

- Table name: `transactions`
- Primary key: `id` (auto-increment integer)
- Foreign key: `month_id` referencing `months.id`
- Core fields: `date` (Date, not null), `description` (String 500, not null), `amount` (float, not null)
- Optional: `account` (String 100, nullable)
- Original categories: `bankin_category`, `bankin_subcategory` (String 100, nullable)
- AI categories: `money_map_type`, `money_map_subcategory` (String, nullable)
- Correction tracking: `is_manually_corrected` (bool, default false)
- Constraints: `CheckConstraint` on `money_map_type` for valid enum values
- Indexes: `idx_transactions_month` on `month_id`, `idx_transactions_date` on `date`

**Advice Model:**

- Table name: `advice`
- Primary key: `id` (auto-increment integer)
- Foreign key: `month_id` referencing `months.id`
- Content: `advice_text` (String 5000, not null)
- Timestamp: `generated_at` (DateTime, auto-set on creation)

**Bidirectional Relationships:**

- Month has `transactions` relationship with `cascade='all, delete-orphan'`
- Month has `advice_records` relationship with `cascade='all, delete-orphan'`
- Transaction has `month` back-reference via `back_populates`
- Advice has `month` back-reference via `back_populates`

**Database Configuration (database.py):**

- Calculate `DATABASE_PATH` relative to project root: `data/moneymap.db`
- Create sync engine with `check_same_thread=False` for FastAPI compatibility
- Create `SessionLocal` sessionmaker with `autocommit=False`, `autoflush=False`
- Implement `get_db()` generator for FastAPI dependency injection
- Implement `init_db()` that creates data directory and all tables

**Package Exports (`db/__init__.py`):**

- Export: `Base`, `engine`, `SessionLocal`, `get_db`, `init_db`
- Export: `MoneyMapType`, `ScoreLabel`, `Month`, `Transaction`, `Advice`

## Visual Design

No UI visuals required - this is a backend-only feature.

**ERD from PRD:**

```text
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   months    │───────│  transactions   │       │   advice    │
│             │ 1   n │                 │       │             │
│  id (PK)    │◄──────│  month_id (FK)  │       │  id (PK)    │
│  year       │       │  id (PK)        │       │  month_id   │───┐
│  month      │       │  date           │       │  advice_text│   │
│  totals...  │       │  description    │       │  generated  │   │
│  score      │       │  amount         │       └─────────────┘   │
└─────────────┘       │  categories...  │                         │
       ▲              └─────────────────┘                         │
       └──────────────────────────────────────────────────────────┘
```

## Existing Code to Leverage

**No Existing Code - Greenfield Project:**

- The `backend/` directory does not exist yet
- This is the foundation feature for all other backend work
- Found by: code-explorer analysis of backend structure

**Patterns from Documentation - `CLAUDE.md`**

- Line length: 119 characters
- Type annotations: Required on all functions
- Union syntax: `str | None` (modern Python 3.10+)
- Docstrings: NumPy-style for public functions
- Found by: code-explorer analysis of project conventions

**Test Patterns - Recommended Approach:**

- Use in-memory SQLite (`sqlite:///:memory:`) for unit tests
- Use `pytest` fixtures with session rollback for isolation
- Create `tests/conftest.py` with shared database fixtures
- Found by: code-explorer analysis of test patterns

## Architecture Approach

**Component Design:**

| File                         | Responsibility                                   |
| ---------------------------- | ------------------------------------------------ |
| `backend/app/__init__.py`    | Empty package marker                             |
| `backend/app/db/__init__.py` | Re-export all public symbols                     |
| `backend/app/db/database.py` | Engine, session factory, `get_db()`, `init_db()` |
| `backend/app/db/models.py`   | Enums + Month, Transaction, Advice models        |

**Data Flow - Database Initialization:**

```sql
init_db() called
    ├── Create data/ directory (mkdir with parents)
    └── Base.metadata.create_all(bind=engine)
        ├── Creates 'months' table
        ├── Creates 'transactions' table
        └── Creates 'advice' table
```

**Data Flow - Session Lifecycle:**

```text
FastAPI Request → get_db() dependency
    ├── SessionLocal() creates session
    ├── yield session → Route handler
    └── finally: session.close()
```

**Key Architectural Decisions:**

- Synchronous SQLAlchemy (not async) - simpler for local SQLite MVP
- String enums stored directly in SQLite for human-readable queries
- `create_all()` instead of migrations for MVP simplicity
- Request-scoped sessions via FastAPI `Depends()`

## Out of Scope

- CRUD operations and repository layer (roadmap item #2+)
- CSV parsing logic (roadmap item #2)
- API endpoints and routers (roadmap item #5+)
- Score calculation logic (roadmap item #4)
- Advice generation logic (roadmap item #14)
- Database migration system (using `create_all()` for MVP)
- User authentication tables (not in MVP)
- Async database driver (aiosqlite) - using sync for simplicity
- Test implementation (will be added alongside models)
- pyproject.toml creation (may already exist or be separate task)
