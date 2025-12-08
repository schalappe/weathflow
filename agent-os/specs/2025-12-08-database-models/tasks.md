# Task Breakdown: Database Models

## Overview

Total Tasks: 15
Estimated Complexity: Low
Primary Stack: Python + SQLAlchemy 2.0 + SQLite

## Task List

### Project Setup

#### Task Group 1: Directory Structure and Package Setup

**Dependencies:** None

- [x] 1.0 Complete project setup
  - [x] 1.1 Create backend directory structure
    - Create `backend/` directory
    - Create `backend/app/` directory
    - Create `backend/app/db/` directory
    - Create `backend/tests/` directory
  - [x] 1.2 Create package marker files
    - Create `backend/app/__init__.py` (empty)
    - Create `backend/app/db/__init__.py` (placeholder with TODO)
    - Create `backend/tests/__init__.py` (empty)
  - [x] 1.3 Verify directory structure exists
    - Run `ls -la backend/app/db/` to confirm

**Acceptance Criteria:**

- All directories created
- Package files exist and are valid Python

---

### Database Layer

#### Task Group 2: Database Configuration

**Dependencies:** Task Group 1

- [x] 2.0 Complete database configuration
  - [x] 2.1 Write 4 focused tests for database configuration
    - Test `DATABASE_PATH` resolves to correct location
    - Test `engine` can connect to SQLite
    - Test `init_db()` creates data directory
    - Test `init_db()` is idempotent (safe to call twice)
  - [x] 2.2 Create database.py with engine and session
    - Define `DATABASE_PATH` relative to project root (`data/moneymap.db`)
    - Define `DATABASE_URL` as SQLite connection string
    - Create `engine` with `check_same_thread=False`
    - Create `SessionLocal` sessionmaker
    - Create `Base` declarative base
  - [x] 2.3 Implement get_db() dependency function
    - Generator function that yields session
    - Ensures session closure in finally block
    - Add NumPy-style docstring
  - [x] 2.4 Implement init_db() function
    - Create `data/` directory with `mkdir(parents=True, exist_ok=True)`
    - Call `Base.metadata.create_all(bind=engine)`
    - Add NumPy-style docstring
  - [x] 2.5 Ensure database configuration tests pass
    - Run ONLY the 4 tests from 2.1
    - Verify engine connects successfully

**Acceptance Criteria:**

- All 4 tests from 2.1 pass
- `init_db()` creates database file at correct path
- `get_db()` properly yields and closes sessions

---

#### Task Group 3: Enum Definitions

**Dependencies:** Task Group 2

- [x] 3.0 Complete enum definitions
  - [x] 3.1 Write 3 focused tests for enums
    - Test `MoneyMapType` values are correct strings
    - Test `ScoreLabel` values match expected labels
    - Test enums inherit from both `str` and `Enum`
  - [x] 3.2 Create MoneyMapType enum in models.py
    - Inherit from `str` and `Enum`
    - Values: INCOME, CORE, CHOICE, COMPOUND, EXCLUDED
    - Add docstring explaining budget categories
  - [x] 3.3 Create ScoreLabel enum in models.py
    - Inherit from `str` and `Enum`
    - Values: POOR="Poor", NEED_IMPROVEMENT="Need Improvement", OKAY="Okay", GREAT="Great"
    - Add docstring explaining score interpretation
  - [x] 3.4 Ensure enum tests pass
    - Run ONLY the 3 tests from 3.1

**Acceptance Criteria:**

- All 3 tests from 3.1 pass
- Enums are type-safe and store string values
- Enums work with SQLAlchemy column storage

---

#### Task Group 4: Month Model

**Dependencies:** Task Group 3

- [x] 4.0 Complete Month model
  - [x] 4.1 Write 4 focused tests for Month model
    - Test creating a Month record with required fields
    - Test unique constraint on (year, month) raises IntegrityError
    - Test default values for totals and percentages
    - Test `created_at` and `updated_at` are auto-set
  - [x] 4.2 Create Month model class
    - Table name: `months`
    - Primary key: `id` with `mapped_column(primary_key=True)`
    - Calendar fields: `year`, `month` (Integer, not null)
    - Use SQLAlchemy 2.0 `Mapped` syntax throughout
  - [x] 4.3 Add Month financial fields
    - Totals: `total_income`, `total_core`, `total_choice`, `total_compound` (Float, default 0.0)
    - Percentages: `core_percentage`, `choice_percentage`, `compound_percentage` (Float, default 0.0)
    - Score: `score` (Integer, default 0), `score_label` (String, nullable)
  - [x] 4.4 Add Month timestamps and constraints
    - `created_at`: DateTime with default `datetime.now(UTC)`
    - `updated_at`: DateTime with default and `onupdate`
    - `UniqueConstraint('year', 'month', name='uq_year_month')`
    - `Index('idx_months_year_month', 'year', 'month')`
  - [x] 4.5 Add Month `__repr__` method
    - Return `<Month(id=X, year=Y, month=Z, score=S)>`
  - [x] 4.6 Ensure Month model tests pass
    - Run ONLY the 4 tests from 4.1

**Acceptance Criteria:**

- All 4 tests from 4.1 pass
- Unique constraint prevents duplicate (year, month)
- Timestamps auto-populate correctly

---

#### Task Group 5: Transaction Model

**Dependencies:** Task Group 4

- [x] 5.0 Complete Transaction model
  - [x] 5.1 Write 4 focused tests for Transaction model
    - Test creating a Transaction linked to a Month
    - Test CHECK constraint rejects invalid `money_map_type`
    - Test foreign key relationship works correctly
    - Test `is_manually_corrected` defaults to False
  - [x] 5.2 Create Transaction model class
    - Table name: `transactions`
    - Primary key: `id`
    - Foreign key: `month_id` referencing `months.id`
    - Core fields: `date` (Date), `description` (String 500), `amount` (Float)
  - [x] 5.3 Add Transaction category fields
    - Optional: `account` (String 100, nullable)
    - Original: `bankin_category`, `bankin_subcategory` (String 100, nullable)
    - AI-assigned: `money_map_type`, `money_map_subcategory` (String, nullable)
    - Tracking: `is_manually_corrected` (Boolean, default False)
    - Timestamp: `created_at` (DateTime, auto-set)
  - [x] 5.4 Add Transaction constraints and indexes
    - `CheckConstraint` on `money_map_type` for valid enum values or NULL
    - `Index('idx_transactions_month', 'month_id')`
    - `Index('idx_transactions_date', 'date')`
  - [x] 5.5 Add Transaction `__repr__` method
    - Return `<Transaction(id=X, date=Y, amount=Z)>`
  - [x] 5.6 Ensure Transaction model tests pass
    - Run ONLY the 4 tests from 5.1

**Acceptance Criteria:**

- All 4 tests from 5.1 pass
- CHECK constraint enforces valid `money_map_type` values
- Foreign key relationship to Month works

---

#### Task Group 6: Advice Model

**Dependencies:** Task Group 4

- [x] 6.0 Complete Advice model
  - [x] 6.1 Write 3 focused tests for Advice model
    - Test creating an Advice record linked to a Month
    - Test `advice_text` is required (not nullable)
    - Test `generated_at` auto-sets on creation
  - [x] 6.2 Create Advice model class
    - Table name: `advice`
    - Primary key: `id`
    - Foreign key: `month_id` referencing `months.id`
    - Content: `advice_text` (String 5000, not null)
    - Timestamp: `generated_at` (DateTime, auto-set)
  - [x] 6.3 Add Advice `__repr__` method
    - Return `<Advice(id=X, month_id=Y)>`
  - [x] 6.4 Ensure Advice model tests pass
    - Run ONLY the 3 tests from 6.1

**Acceptance Criteria:**

- All 3 tests from 6.1 pass
- Foreign key relationship to Month works
- `generated_at` auto-populates

---

#### Task Group 7: Relationships and Exports

**Dependencies:** Task Groups 5, 6

- [x] 7.0 Complete relationships and exports
  - [x] 7.1 Write 4 focused tests for relationships
    - Test Month.transactions returns list of transactions
    - Test Month.advice_records returns list of advice
    - Test Transaction.month back-reference works
    - Test cascade delete removes transactions when Month deleted
  - [x] 7.2 Add relationships to Month model
    - `transactions: Mapped[list['Transaction']]` with `back_populates='month'`, `cascade='all, delete-orphan'`
    - `advice_records: Mapped[list['Advice']]` with `back_populates='month'`, `cascade='all, delete-orphan'`
  - [x] 7.3 Add relationships to Transaction and Advice
    - Transaction: `month: Mapped['Month']` with `back_populates='transactions'`
    - Advice: `month: Mapped['Month']` with `back_populates='advice_records'`
  - [x] 7.4 Update `db/__init__.py` with exports
    - Export from database.py: `Base`, `engine`, `SessionLocal`, `get_db`, `init_db`
    - Export from models.py: `MoneyMapType`, `ScoreLabel`, `Month`, `Transaction`, `Advice`
    - Add `__all__` list
  - [x] 7.5 Ensure relationship tests pass
    - Run ONLY the 4 tests from 7.1

**Acceptance Criteria:**

- All 4 tests from 7.1 pass
- Bidirectional relationships work correctly
- Cascade delete removes child records
- All public symbols exported from `app.db`

---

### Testing

#### Task Group 8: Test Setup and Verification

**Dependencies:** Task Group 7

- [x] 8.0 Complete test setup and final verification
  - [x] 8.1 Create tests/conftest.py with fixtures
    - Create `test_db_engine` fixture using in-memory SQLite
    - Create `test_db_session` fixture with transaction rollback
    - Use `StaticPool` to keep in-memory DB alive
  - [x] 8.2 Review all tests from Task Groups 2-7
    - Review 4 database config tests (Task 2.1)
    - Review 3 enum tests (Task 3.1)
    - Review 4 Month tests (Task 4.1)
    - Review 4 Transaction tests (Task 5.1)
    - Review 3 Advice tests (Task 6.1)
    - Review 4 relationship tests (Task 7.1)
    - Total: 22 tests
  - [x] 8.3 Run all feature tests
    - Run `cd backend && uv run pytest tests/ -v`
    - All 22 tests should pass
  - [x] 8.4 Verify init_db() creates working database
    - Run `cd backend && uv run python -c "from app.db import init_db; init_db()"`
    - Verify `data/moneymap.db` file exists

**Acceptance Criteria:**

- All 22 feature tests pass
- `tests/conftest.py` provides reusable fixtures
- Database file created successfully at correct path
- All models can be imported from `app.db`

---

## Execution Order

Recommended implementation sequence:

1. **Task Group 1** (Project Setup) - Create directory structure first
2. **Task Group 2** (Database Configuration) - Set up engine and session
3. **Task Group 3** (Enums) - Define enums before models that use them
4. **Task Group 4** (Month Model) - Parent model needed for foreign keys
5. **Task Group 5** (Transaction Model) - Can start after Month exists
6. **Task Group 6** (Advice Model) - Can run parallel with Task Group 5
7. **Task Group 7** (Relationships) - Add after all models defined
8. **Task Group 8** (Testing) - Final verification

**Parallel Opportunities:**

- Task Groups 5 and 6 can be done in parallel (both depend only on Month)

---

## Notes

- This is a greenfield project - no existing code to migrate
- Using synchronous SQLAlchemy for simplicity (not async)
- No database migrations - using `create_all()` for MVP
- All tests use in-memory SQLite for speed and isolation
