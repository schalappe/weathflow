# Spec Requirements: Database Models

## Initial Description

Create SQLAlchemy models for months, transactions, and advice tables with proper relationships and indexes.

## Requirements Discussion

### Source Document

All requirements sourced from existing PRD: `docs/product-development/features/01-database-models.md`

### Key Decisions from PRD

**Q1:** Month identifier format?
**Answer:** Separate `year` (INTEGER) and `month` (INTEGER) columns with a unique constraint on `(year, month)`.

**Q2:** Transaction fields - store original Bankin' categories?
**Answer:** Yes. Store both `bankin_category`/`bankin_subcategory` (original CSV) and `money_map_type`/`money_map_subcategory` (AI-assigned).

**Q3:** Amount storage format?
**Answer:** Use `REAL` (float) type for amounts. Also includes `account` field for bank account name.

**Q4:** Advice table structure?
**Answer:** Single `advice_text` field containing full AI-generated advice. One record per month, can be regenerated.

**Q5:** SQLAlchemy syntax?
**Answer:** Use SQLAlchemy 2.0+ with `Mapped` syntax and type annotations.

**Q6:** Tracking user corrections?
**Answer:** Include `is_manually_corrected` boolean field on transactions.

### Existing Code to Reference

**Similar Features Identified:**

- No existing SQLAlchemy models in the codebase (this is the foundation feature)
- Tech stack defines patterns: `backend/app/db/` directory structure

**Patterns Defined in Tech Stack:**

- Repository pattern for data access via `db/crud.py`
- Use `Base.metadata.create_all()` for table creation (no migrations for MVP)
- Store database at `data/moneymap.db`

## Visual Assets

### Files Provided

No visual assets provided.

### Visual from PRD

ERD diagram included in PRD document:

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
       │                                                          │
       └──────────────────────────────────────────────────────────┘
                              1:n relationship
```

## Requirements Summary

### Functional Requirements

**Three Models Required:**

1. **Month Model**
   - `id`: Primary key (auto-increment)
   - `year`: Integer, not null
   - `month`: Integer, not null
   - `total_income`, `total_core`, `total_choice`, `total_compound`: REAL, default 0
   - `core_percentage`, `choice_percentage`, `compound_percentage`: REAL, default 0
   - `score`: Integer (0-3), default 0
   - `score_label`: Text ("Great", "Okay", "Need Improvement", "Poor")
   - `created_at`, `updated_at`: DateTime with defaults
   - Unique constraint on `(year, month)`

2. **Transaction Model**
   - `id`: Primary key (auto-increment)
   - `month_id`: Foreign key to months, not null
   - `date`: Date, not null
   - `description`: Text, not null
   - `account`: Text (nullable)
   - `amount`: REAL, not null
   - `bankin_category`, `bankin_subcategory`: Text (original CSV values)
   - `money_map_type`: Text with CHECK constraint (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED)
   - `money_map_subcategory`: Text
   - `is_manually_corrected`: Boolean, default false
   - `created_at`: DateTime with default

3. **Advice Model**
   - `id`: Primary key (auto-increment)
   - `month_id`: Foreign key to months, not null
   - `advice_text`: Text, not null
   - `generated_at`: DateTime with default

**Relationships:**

- Month → Transactions: One-to-many
- Month → Advice: One-to-many (though typically one per month)
- Bidirectional with `back_populates`

**Enums Required:**

- `MoneyMapType`: INCOME, CORE, CHOICE, COMPOUND, EXCLUDED
- `ScoreLabel`: Great, Okay, Need Improvement, Poor

### Technical Requirements

- SQLAlchemy 2.0+ with `Mapped` syntax
- All fields have explicit type annotations
- Indexes on: `month_id`, `date`, `(year, month)`
- Foreign key constraints enforced
- `init_db()` function creates database and all tables
- Database path: `data/moneymap.db`

### File Structure

```text
backend/
└── app/
    └── db/
        ├── __init__.py
        ├── database.py    # Engine, session, init_db()
        └── models.py      # Month, Transaction, Advice models
```

### Scope Boundaries

**In Scope:**

- Three SQLAlchemy models with relationships
- Database configuration (`database.py`)
- `init_db()` function
- Indexes and constraints
- Python enums for type safety

**Out of Scope:**

- CRUD operations (separate task)
- CSV parsing logic
- API endpoints
- Score calculation logic
- Advice generation
- Migration system (just `create_all()`)
- User/auth tables
- Async database driver (aiosqlite) - using sync for now

### Testing Requirements

- Unit test: Create a month record
- Unit test: Create a transaction linked to a month
- Unit test: Verify unique constraint on `(year, month)`
- Unit test: Verify `money_map_type` constraint rejects invalid values
- Integration test: `init_db()` creates tables in fresh database
