# Architecture Proposal: Repository Pattern for Backend Services

> **Status**: Proposal
> **Date**: 2025-12-13
> **Author**: Claude Code

## Executive Summary

The current architecture mixes **database operations directly into service functions**, violating the Clean Architecture principle of separating data access from business logic. This makes testing harder (requires mocking `Session`) and couples services to SQLAlchemy implementation details. This document proposes introducing a **lightweight repository layer** that centralizes all database operations.

---

## Current Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    ROUTERS (Presentation)                   │
│  upload.py │ months.py │ transactions.py │ advice.py        │
└──────────────────────────┬──────────────────────────────────┘
                           │ Depends(get_db)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICES (Business Logic + Data Access)  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ upload.py       │  │ months.py       │  │ advice.py   │  │
│  │ • db.query()    │  │ • db.query()    │  │ • db.query()│  │
│  │ • db.add_all()  │  │ • db.query()    │  │ • db.add()  │  │
│  │ • db.delete()   │  │ • .filter()     │  │ • db.commit │  │
│  │ • db.flush()    │  │ • func.count()  │  │ • db.refresh│  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ Direct SQLAlchemy
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (Models)                        │
│         Month │ Transaction │ Advice                        │
└─────────────────────────────────────────────────────────────┘
```

### Problems Identified

| Issue | Impact | Example Location |
|-------|--------|------------------|
| **Direct ORM in services** | Testing requires mocking Session | `months.py:99` |
| **Scattered query patterns** | Duplicated query logic | Multiple `db.query(Month).filter()` calls |
| **Mixed concerns** | Business logic + data access in same file | `upload.py:274-297` |
| **No abstraction** | Impossible to swap database impl | All services coupled to SQLAlchemy |

---

## Proposed Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    ROUTERS (Presentation)                   │
│  upload.py │ months.py │ transactions.py │ advice.py        │
└──────────────────────────┬──────────────────────────────────┘
                           │ Depends(get_db)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICES (Pure Business Logic)           │
│  • Orchestration & coordination                             │
│  • Score calculation, validation                            │
│  • NO db.query(), NO db.add(), NO db.commit()               │
└──────────────────────────┬──────────────────────────────────┘
                           │ Uses repositories
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 REPOSITORIES (Data Access)                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ MonthRepository  │  │TransactionRepo   │  │AdviceRepo  │ │
│  │ • get_by_id()    │  │• get_for_month() │  │• get()     │ │
│  │ • get_by_ym()    │  │• add_bulk()      │  │• upsert()  │ │
│  │ • get_all()      │  │• delete_month()  │  │            │ │
│  │ • create()       │  │• aggregate()     │  │            │ │
│  │ • update()       │  │                  │  │            │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ SQLAlchemy ORM
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (Models)                        │
│         Month │ Transaction │ Advice                        │
└─────────────────────────────────────────────────────────────┘
```

### Benefits

1. **Single Responsibility**: Repositories handle ONLY data access, services handle ONLY business logic
2. **Testability**: Mock repositories instead of SQLAlchemy sessions - much cleaner unit tests
3. **Encapsulation**: Query optimization and caching decisions stay in repository layer

---

## Recommended File Structure

```text
backend/app/
├── db/
│   ├── database.py           # Session management (keep as-is)
│   ├── enums.py              # Keep
│   └── models/               # Keep all models
│       ├── month.py
│       ├── transaction.py
│       └── advice.py
├── repositories/             # NEW FOLDER
│   ├── __init__.py
│   ├── month_repository.py
│   ├── transaction_repository.py
│   └── advice_repository.py
├── services/                 # REFACTORED
│   ├── upload.py             # Uses repositories, no db.query()
│   ├── months.py             # Uses repositories, no db.query()
│   ├── calculator.py         # Uses repositories, no db.query()
│   ├── advice.py             # Uses repositories, no db.query()
│   └── ...                   # Other services unchanged
└── routers/                  # Unchanged
```

---

## Repository Interface Design

### MonthRepository

```python
# backend/app/repositories/month_repository.py

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.month import Month
from app.db.models.transaction import Transaction

class MonthRepository:
    """Repository for Month data access operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, month_id: int) -> Month | None:
        """Get month by primary key."""
        return self._db.get(Month, month_id)

    def get_by_year_month(self, year: int, month: int) -> Month | None:
        """Get month by year and month number."""
        return self._db.query(Month).filter(
            Month.year == year, Month.month == month
        ).first()

    def get_all_with_transaction_counts(self) -> list[tuple[Month, int]]:
        """Get all months with transaction counts (optimized JOIN)."""
        return (
            self._db.query(Month, func.count(Transaction.id).label("tx_count"))
            .outerjoin(Transaction, Month.id == Transaction.month_id)
            .group_by(Month.id)
            .order_by(Month.year.desc(), Month.month.desc())
            .all()
        )

    def get_recent(self, limit: int) -> list[Month]:
        """Get most recent N months (chronological order)."""
        result = self._db.query(Month).order_by(
            Month.year.desc(), Month.month.desc()
        ).limit(limit).all()
        result.reverse()  # Oldest first
        return result

    def create(self, year: int, month: int) -> Month:
        """Create a new month record."""
        month_record = Month(year=year, month=month)
        self._db.add(month_record)
        self._db.flush()  # Get ID without committing
        return month_record

    def update(self, month: Month, **fields) -> Month:
        """Update month fields and commit."""
        for field, value in fields.items():
            setattr(month, field, value)
        self._db.commit()
        self._db.refresh(month)
        return month

    def delete(self, month: Month) -> None:
        """Delete a month (cascades to transactions and advice)."""
        self._db.delete(month)
        self._db.flush()
```

### TransactionRepository

```python
# backend/app/repositories/transaction_repository.py

from datetime import date

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.db.enums import MoneyMapType
from app.db.models.transaction import Transaction

class TransactionRepository:
    """Repository for Transaction data access operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Get transaction by primary key."""
        return self._db.get(Transaction, transaction_id)

    def get_filtered(
        self,
        month_id: int,
        *,
        category_types: list[str] | None = None,
        search: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Transaction], int]:
        """Get filtered, paginated transactions."""
        query = self._db.query(Transaction).filter(
            Transaction.month_id == month_id
        )

        if category_types:
            query = query.filter(Transaction.money_map_type.in_(category_types))

        if search:
            escaped = self._escape_like(search)
            query = query.filter(
                Transaction.description.ilike(f"%{escaped}%", escape="\\")
            )

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        total = query.count()
        transactions = (
            query.order_by(Transaction.date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return transactions, total

    def get_all_for_month(self, month_id: int) -> list[Transaction]:
        """Get all transactions for export (no pagination)."""
        return (
            self._db.query(Transaction)
            .filter(Transaction.month_id == month_id)
            .order_by(Transaction.date.desc())
            .all()
        )

    def aggregate_totals(self, month_id: int) -> tuple[float, float, float]:
        """Aggregate income, core, choice totals for a month."""
        result = self._db.query(
            func.coalesce(func.sum(
                case((and_(Transaction.money_map_type == MoneyMapType.INCOME.value,
                          Transaction.amount > 0), Transaction.amount), else_=0)
            ), 0).label("income"),
            func.coalesce(func.sum(
                case((and_(Transaction.money_map_type == MoneyMapType.CORE.value,
                          Transaction.amount < 0), func.abs(Transaction.amount)), else_=0)
            ), 0).label("core"),
            func.coalesce(func.sum(
                case((and_(Transaction.money_map_type == MoneyMapType.CHOICE.value,
                          Transaction.amount < 0), func.abs(Transaction.amount)), else_=0)
            ), 0).label("choice"),
        ).filter(Transaction.month_id == month_id).one()

        return float(result.income), float(result.core), float(result.choice)

    def add_bulk(self, transactions: list[Transaction]) -> None:
        """Add multiple transactions."""
        self._db.add_all(transactions)
        self._db.flush()

    def delete_for_month(self, month_id: int) -> int:
        """Delete all transactions for a month. Returns count."""
        count = self._db.query(Transaction).filter(
            Transaction.month_id == month_id
        ).delete()
        self._db.flush()
        return count

    def get_keys_for_month(self, month_id: int) -> set[str]:
        """Get transaction keys (date|description|amount) for deduplication."""
        transactions = self._db.query(
            Transaction.date, Transaction.description, Transaction.amount
        ).filter(Transaction.month_id == month_id).all()
        return {f"{t.date}|{t.description}|{t.amount}" for t in transactions}

    @staticmethod
    def _escape_like(search: str) -> str:
        return search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
```

### AdviceRepository

```python
# backend/app/repositories/advice_repository.py

from sqlalchemy.orm import Session

from app.db.models.advice import Advice
from app.db.models.base import utc_now

class AdviceRepository:
    """Repository for Advice data access operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_month_id(self, month_id: int) -> Advice | None:
        """Get advice for a specific month."""
        return self._db.query(Advice).filter(
            Advice.month_id == month_id
        ).first()

    def upsert(self, month_id: int, advice_text: str) -> Advice:
        """Create or update advice for a month."""
        existing = self.get_by_month_id(month_id)

        if existing:
            existing.advice_text = advice_text
            existing.generated_at = utc_now()
            self._db.commit()
            self._db.refresh(existing)
            return existing

        advice = Advice(month_id=month_id, advice_text=advice_text)
        self._db.add(advice)
        self._db.commit()
        self._db.refresh(advice)
        return advice
```

---

## Service Refactoring Example

### Before (months.py:75-107)

```python
def get_month_by_year_month(db: Session, year: int, month: int) -> Month | None:
    try:
        result = db.query(Month).filter(Month.year == year, Month.month == month).first()
        # ... logging ...
        return result
    except SQLAlchemyError as error:
        raise MonthQueryError(str(error)) from error
```

### After

```python
def get_month_by_year_month(
    month_repo: MonthRepository, year: int, month: int
) -> Month | None:
    try:
        result = month_repo.get_by_year_month(year, month)
        # ... logging ...
        return result
    except SQLAlchemyError as error:
        raise MonthQueryError(str(error)) from error
```

---

## Dependency Injection Pattern

Repositories are instantiated in routers and passed to services:

```python
# backend/app/routers/months.py

from app.repositories.month_repository import MonthRepository
from app.repositories.transaction_repository import TransactionRepository

@router.get("/months/{year}/{month}")
def get_month_detail(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> MonthDetailResponse:
    # Create repositories
    month_repo = MonthRepository(db)
    transaction_repo = TransactionRepository(db)

    # Pass to services
    month_record = months_service.get_month_by_year_month(month_repo, year, month)
    transactions, total = months_service.get_transactions_filtered(
        transaction_repo,
        month_id=month_record.id,
        ...
    )
```

### Dependency Injection Options

- **Option A (Simple)**: Instantiate in routers, pass to services (shown above)
- **Option B (FastAPI native)**: Use `Depends()` to inject repositories directly

Option A is simpler and more explicit. Option B reduces boilerplate but adds complexity.

---

## Testing Benefits

### Before (Hard to test)

```python
def test_get_all_months():
    # Need to mock Session, query(), filter(), all() - tedious!
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.all.return_value = []
    result = get_all_months_with_counts(mock_db)
```

### After (Clean mocking)

```python
def test_get_all_months():
    mock_repo = MagicMock(spec=MonthRepository)
    mock_repo.get_all_with_transaction_counts.return_value = [(mock_month, 5)]

    result = months_service.get_all_months_with_counts(mock_repo)
    assert len(result) == 1
```

---

## YAGNI Validation

| Criteria | Assessment |
|----------|------------|
| **Solves current problem?** | ✅ Yes - testing is currently painful, DB ops are scattered |
| **Reduces complexity?** | ✅ Yes - clearer separation, less mocking required |
| **Improves clarity?** | ✅ Yes - services focus on logic, repos focus on data |
| **NOT future-proofing?** | ✅ Yes - solves real pain today, not hypothetical needs |

---

## Implementation Roadmap

### Phase 1: Create Repositories (Low Risk)

1. Create `backend/app/repositories/` directory
2. Implement `MonthRepository` with existing query logic
3. Implement `TransactionRepository` with existing query logic
4. Implement `AdviceRepository` with existing query logic
5. Add unit tests for repositories

### Phase 2: Refactor Services (Incremental)

1. Start with `months.py` - simplest, read-only operations
2. Refactor `advice.py` - small, isolated
3. Refactor `calculator.py` - depends on transaction aggregation
4. Refactor `upload.py` - most complex, do last
5. Update routers to inject repositories

### Phase 3: Cleanup

1. Remove direct `db.query()` from services
2. Update tests to use repository mocks
3. Document the repository pattern in CLAUDE.md

---

## Key Recommendations

| Recommendation | Rationale |
|----------------|-----------|
| **Keep repositories simple** | No base classes, no generics - just concrete implementations |
| **One repository per aggregate root** | Month, Transaction, Advice - not per table |
| **Services receive repos, not Session** | Makes dependency explicit and testable |
| **Error handling stays in services** | Repositories bubble up SQLAlchemyError, services transform to domain errors |
| **Flush vs Commit in repos** | `flush()` for visibility within transaction, `commit()` only in services |

---

## What NOT to Do

- ❌ Don't create abstract base repository classes
- ❌ Don't use generic `Repository[T]` patterns
- ❌ Don't add caching layer yet (no evidence of need)
- ❌ Don't create separate interfaces (no need for swappable implementations)
- ❌ Don't refactor everything at once - do it incrementally

### YAGNI Traps to Avoid

- A common over-engineering trap is creating `BaseRepository[T]` with generic CRUD. For 3 entities, this adds complexity without benefit.
- Another trap is creating `IMonthRepository` interfaces - you don't need them unless you're actually swapping implementations (you're not).

---

## Summary

The proposed repository pattern:

1. **Extracts** all `db.query()`, `db.add()`, `db.commit()` operations from services into dedicated repository classes
2. **Simplifies** testing by allowing repository mocking instead of Session mocking
3. **Centralizes** query logic for each entity (Month, Transaction, Advice)
4. **Maintains** the existing clean architecture layers while adding proper separation
5. **Avoids** over-engineering with generic base classes or interfaces

The implementation can be done **incrementally** starting with read-only operations (`months.py`), then moving to write operations (`advice.py`, `calculator.py`), and finally the complex upload flow.
