# PRD: Database Models

> **Roadmap Item**: #1 — Database Models
> **Size**: S (Small)
> **Dependencies**: None (foundation for all other features)

---

## 1. Overview

### 1.1 Objective

Create SQLAlchemy models for the Money Map Manager application, establishing the data foundation for storing monthly financial data, individual transactions, and AI-generated advice.

### 1.2 Success Criteria

- [ ] All three models (`Month`, `Transaction`, `Advice`) implemented with proper relationships
- [ ] Indexes created for frequently queried fields
- [ ] Database initialization via `create_all()` works on first startup
- [ ] Models support all CRUD operations needed by the application

---

## 2. Data Model

### 2.1 Entity Relationship

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

### 2.2 Money Map Categories

The `money_map_type` field must support these values:

| Type       | Description                          | Budget Target |
|------------|--------------------------------------|---------------|
| `INCOME`   | Revenue (salary, etc.)               | —             |
| `CORE`     | Necessities                          | ≤ 50%         |
| `CHOICE`   | Wants/discretionary                  | ≤ 30%         |
| `COMPOUND` | Savings/investments                  | ≥ 20%         |
| `EXCLUDED` | Internal transfers (not counted)     | —             |

### 2.3 Subcategories Reference

**CORE subcategories:**

- Housing, Groceries, Utilities, Healthcare, Transportation
- Basic clothing, Phone and internet, Insurance, Debt payments

**CHOICE subcategories:**

- Dining out, Entertainment, Travel and vacations
- Electronics and gadgets, Hobby supplies, Fancy clothing
- Subscription services, Home decor, Gifts

**COMPOUND subcategories:**

- Emergency Fund, Education Fund, Investments, Other

**INCOME subcategories:**

- Job

---

## 3. Technical Specification

### 3.1 Database Schema

#### 3.1.1 `months` Table

```sql
CREATE TABLE months (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_income REAL DEFAULT 0,
    total_core REAL DEFAULT 0,
    total_choice REAL DEFAULT 0,
    total_compound REAL DEFAULT 0,
    core_percentage REAL DEFAULT 0,
    choice_percentage REAL DEFAULT 0,
    compound_percentage REAL DEFAULT 0,
    score INTEGER DEFAULT 0,
    score_label TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month)
);

CREATE INDEX idx_months_year_month ON months(year, month);
```

**Field Notes:**

- `year` + `month` form a unique constraint (one record per calendar month)
- `score` is 0-3 based on Money Map rules
- `score_label` is one of: "Great", "Okay", "Need Improvement", "Poor"

#### 3.1.2 `transactions` Table

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_id INTEGER NOT NULL,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    account TEXT,
    amount REAL NOT NULL,
    bankin_category TEXT,
    bankin_subcategory TEXT,
    money_map_type TEXT CHECK(money_map_type IN ('INCOME', 'CORE', 'CHOICE', 'COMPOUND', 'EXCLUDED')),
    money_map_subcategory TEXT,
    is_manually_corrected BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (month_id) REFERENCES months(id)
);

CREATE INDEX idx_transactions_month ON transactions(month_id);
CREATE INDEX idx_transactions_date ON transactions(date);
```

**Field Notes:**

- `bankin_category` / `bankin_subcategory` preserve the original CSV categorization
- `money_map_type` / `money_map_subcategory` are the AI-assigned categories
- `is_manually_corrected` tracks user corrections for analytics

#### 3.1.3 `advice` Table

```sql
CREATE TABLE advice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_id INTEGER NOT NULL,
    advice_text TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (month_id) REFERENCES months(id)
);
```

**Field Notes:**

- One advice record per month (can be regenerated)
- `advice_text` contains the full AI-generated advice

### 3.2 SQLAlchemy Models

#### 3.2.1 Base Configuration

```python
# backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "moneymap.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Create all tables if they don't exist."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 3.2.2 Model Implementation Requirements

Each model must include:

1. **Proper type hints** for all columns
2. **Relationships** with `relationship()` and `back_populates`
3. **String representation** via `__repr__`
4. **Validation** via SQLAlchemy's `CheckConstraint` where appropriate

### 3.3 File Structure

```text
backend/
└── app/
    └── db/
        ├── __init__.py
        ├── database.py    # Engine, session, init_db()
        └── models.py      # Month, Transaction, Advice models
```

---

## 4. Acceptance Criteria

### 4.1 Functional Requirements

- [ ] `Month` model with all fields from schema
- [ ] `Transaction` model with foreign key to `Month`
- [ ] `Advice` model with foreign key to `Month`
- [ ] Bidirectional relationships (`month.transactions`, `transaction.month`, etc.)
- [ ] `money_map_type` constrained to valid enum values
- [ ] `init_db()` creates the database file and all tables

### 4.2 Technical Requirements

- [ ] Uses SQLAlchemy 2.0+ syntax
- [ ] All fields have explicit types
- [ ] Indexes on `month_id`, `date`, and `(year, month)`
- [ ] Unique constraint on `(year, month)` in `months` table
- [ ] Foreign key constraints enforced

### 4.3 Testing Requirements

- [ ] Unit test: Create a month record
- [ ] Unit test: Create a transaction linked to a month
- [ ] Unit test: Verify unique constraint on `(year, month)`
- [ ] Unit test: Verify `money_map_type` constraint rejects invalid values
- [ ] Integration test: `init_db()` creates tables in fresh database

---

## 5. Implementation Notes

### 5.1 SQLAlchemy 2.0 Patterns

Use the modern `Mapped` syntax:

```python
from sqlalchemy import ForeignKey, String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class Month(Base):
    __tablename__ = "months"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    # ... etc
```

### 5.2 Enum Consideration

Consider using a Python `Enum` for `money_map_type` to ensure type safety:

```python
from enum import Enum

class MoneyMapType(str, Enum):
    INCOME = "INCOME"
    CORE = "CORE"
    CHOICE = "CHOICE"
    COMPOUND = "COMPOUND"
    EXCLUDED = "EXCLUDED"
```

### 5.3 Score Label Enum

```python
class ScoreLabel(str, Enum):
    GREAT = "Great"
    OKAY = "Okay"
    NEED_IMPROVEMENT = "Need Improvement"
    POOR = "Poor"
```

---

## 6. Out of Scope

- CRUD operations (separate task)
- CSV parsing logic
- API endpoints
- Score calculation logic
- Advice generation

---

## 7. Dependencies

### 7.1 Required Packages

```toml
# In pyproject.toml
dependencies = [
    "sqlalchemy>=2.0.0",
]
```

### 7.2 Database Location

The SQLite database file should be created at:

```text
<project_root>/data/moneymap.db
```

The `init_db()` function must create the `data/` directory if it doesn't exist.
