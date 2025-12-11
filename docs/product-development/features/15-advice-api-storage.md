# Feature 15: Advice API and Storage

## Overview

Create endpoints to generate and retrieve personalized financial advice, storing generated advice in the database for each month. This feature exposes the Advice Generation Service (Feature 14) via REST API and persists advice for future retrieval.

**Size**: S (Small)
**Dependencies**: Features 1 (Database Models), 14 (Advice Generation Service)

## User Story

```txt
En tant qu'utilisateur,
Je veux pouvoir generer et consulter des conseils personnalises pour un mois donne,
Afin de suivre les recommandations et ameliorer mon score Money Map au fil du temps.
```

## Acceptance Criteria

- [ ] `POST /api/advice/generate` endpoint generates advice for a given month
- [ ] `GET /api/advice/{year}/{month}` endpoint retrieves stored advice
- [ ] Generated advice is persisted in the `advice` table
- [ ] Endpoint returns existing advice if already generated for the month
- [ ] Endpoint supports optional `regenerate` flag to force new advice generation
- [ ] Returns 404 if month data does not exist
- [ ] Returns appropriate error if insufficient historical data (< 2 months)

## Technical Specification

### Router Location

```txt
backend/app/routers/advice.py
```

### Database Model

The advice table stores generated advice for each month:

```python
# backend/app/db/models.py

class Advice(Base):
    """
    Stores generated financial advice for a specific month.

    Each month can have one advice record. Regenerating advice
    replaces the existing record.
    """

    __tablename__ = "advice"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id"), nullable=False)
    advice_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship
    month: Mapped["Month"] = relationship(back_populates="advice")
```

### API Endpoints

#### POST /api/advice/generate

Generate personalized advice for a specific month.

**Request Body:**

```python
class GenerateAdviceRequest(BaseModel):
    year: int
    month: int
    regenerate: bool = False  # Force regeneration if advice exists
```

**Response:**

```python
class ProblemArea(BaseModel):
    category: str
    amount: float
    trend: str

class AdviceData(BaseModel):
    analysis: str
    problem_areas: list[ProblemArea]
    recommendations: list[str]
    encouragement: str

class GenerateAdviceResponse(BaseModel):
    success: bool
    advice: AdviceData
    generated_at: datetime
    was_cached: bool  # True if returned existing advice
```

**Example Request:**

```json
{
  "year": 2025,
  "month": 10,
  "regenerate": false
}
```

**Example Response:**

```json
{
  "success": true,
  "advice": {
    "analysis": "Tes depenses Choice ont augmente de 15% sur les 3 derniers mois...",
    "problem_areas": [
      {"category": "Subscription services", "amount": 85.0, "trend": "+20%"},
      {"category": "Dining out", "amount": 120.0, "trend": "+10%"}
    ],
    "recommendations": [
      "Audite tes abonnements: Perplexity + Claude API representent 25 euros/mois.",
      "Meal prep le dimanche pour reduire les fast-foods de 30%",
      "Fixe-toi un budget Entertainment de 40 euros/mois"
    ],
    "encouragement": "Tu es proche du score Great! Continue ainsi."
  },
  "generated_at": "2025-10-15T14:30:00Z",
  "was_cached": false
}
```

#### GET /api/advice/{year}/{month}

Retrieve stored advice for a specific month.

**Response:**

```python
class GetAdviceResponse(BaseModel):
    success: bool
    advice: AdviceData | None
    generated_at: datetime | None
    exists: bool
```

**Example Response (advice exists):**

```json
{
  "success": true,
  "advice": {
    "analysis": "...",
    "problem_areas": [...],
    "recommendations": [...],
    "encouragement": "..."
  },
  "generated_at": "2025-10-15T14:30:00Z",
  "exists": true
}
```

**Example Response (no advice):**

```json
{
  "success": true,
  "advice": null,
  "generated_at": null,
  "exists": false
}
```

### Router Implementation

```python
# backend/app/routers/advice.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.advisor import AdviceGenerator, InsufficientDataError

router = APIRouter()

@router.post("/advice/generate", response_model=GenerateAdviceResponse)
async def generate_advice(
    request: GenerateAdviceRequest,
    db: Session = Depends(get_db)
):
    """
    Generate personalized advice for a specific month.

    Uses the last 3 months of data to analyze trends and provide
    actionable recommendations via Claude API.

    If advice already exists for the month and regenerate=False,
    returns the cached advice.
    """
    # 1. Check if month exists
    # 2. Check if advice already exists (return if regenerate=False)
    # 3. Fetch last 3 months of data
    # 4. Call AdviceGenerator service
    # 5. Store advice in database
    # 6. Return response
    pass

@router.get("/advice/{year}/{month}", response_model=GetAdviceResponse)
async def get_advice(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored advice for a specific month.

    Returns the most recently generated advice for the month,
    or indicates that no advice exists yet.
    """
    pass
```

### CRUD Operations

```python
# backend/app/db/crud.py

def get_advice_by_month(db: Session, month_id: int) -> Advice | None:
    """Get advice for a specific month."""
    return db.query(Advice).filter(Advice.month_id == month_id).first()

def create_or_update_advice(
    db: Session,
    month_id: int,
    advice_text: str
) -> Advice:
    """
    Create new advice or update existing advice for a month.

    Each month can only have one advice record.
    """
    existing = get_advice_by_month(db, month_id)

    if existing:
        existing.advice_text = advice_text
        existing.generated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    advice = Advice(
        month_id=month_id,
        advice_text=advice_text,
        generated_at=datetime.utcnow()
    )
    db.add(advice)
    db.commit()
    db.refresh(advice)
    return advice

def delete_advice(db: Session, advice_id: int) -> bool:
    """Delete advice by ID."""
    advice = db.query(Advice).filter(Advice.id == advice_id).first()
    if advice:
        db.delete(advice)
        db.commit()
        return True
    return False
```

### Storage Format

Advice is stored as JSON text in the `advice_text` column:

```json
{
  "analysis": "string",
  "problem_areas": [
    {"category": "string", "amount": 0.0, "trend": "string"}
  ],
  "recommendations": ["string"],
  "encouragement": "string"
}
```

### Error Handling

```python
class AdviceNotFoundError(Exception):
    """Raised when advice is requested but doesn't exist."""
    pass

class MonthNotFoundError(Exception):
    """Raised when the requested month doesn't exist."""
    pass
```

**HTTP Error Responses:**

| Status | Condition                        | Response                                          |
| ------ | -------------------------------- | ------------------------------------------------- |
| 404    | Month not found                  | `{"detail": "Month 2025-10 not found"}`           |
| 400    | Insufficient historical data     | `{"detail": "Need at least 2 months of data"}`    |
| 500    | Claude API failure               | `{"detail": "Failed to generate advice"}`         |

### Implementation Steps

1. **Add Advice model** to `models.py` with relationship to Month
2. **Create CRUD functions** for advice operations
3. **Implement POST endpoint** with caching logic
4. **Implement GET endpoint** for retrieval
5. **Add error handling** for all edge cases
6. **Write unit tests** for CRUD and endpoints
7. **Write integration tests** for full flow

## Testing Requirements

### Unit Tests

```python
# tests/unit/routers/test_advice.py

async def test_generate_advice_new():
    """Test generating advice for a month without existing advice."""
    pass

async def test_generate_advice_cached():
    """Test that existing advice is returned when regenerate=False."""
    pass

async def test_generate_advice_regenerate():
    """Test that new advice is generated when regenerate=True."""
    pass

async def test_generate_advice_month_not_found():
    """Test 404 when month doesn't exist."""
    pass

async def test_generate_advice_insufficient_data():
    """Test 400 when less than 2 months of history."""
    pass

async def test_get_advice_exists():
    """Test retrieving existing advice."""
    pass

async def test_get_advice_not_exists():
    """Test response when no advice exists for month."""
    pass
```

### Integration Tests

```python
# tests/integration/routers/test_advice.py

async def test_generate_and_retrieve_advice():
    """Test full flow: generate advice then retrieve it."""
    pass

async def test_advice_persisted_to_database():
    """Test that generated advice is correctly stored in DB."""
    pass
```

## Notes

- Advice is stored as JSON text for flexibility in schema changes
- Each month can have only one advice record (replaced on regeneration)
- The `was_cached` flag helps the frontend know if this is fresh advice
- Consider adding a rate limit to prevent excessive Claude API calls
- The generated_at timestamp helps users know how recent the advice is
