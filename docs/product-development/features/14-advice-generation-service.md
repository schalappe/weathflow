# Feature 14: Advice Generation Service

## Overview

Implement Claude API integration that analyzes the last 3 months of financial data and generates personalized recommendations with trend analysis.

**Size**: M (Medium)
**Dependencies**: Features 1-4 (Database, CSV Parser, Categorization, Score Calculation)

## User Story

```txt
En tant qu'utilisateur,
Je veux recevoir des conseils basés sur mes 3 derniers mois,
Afin d'ameliorer mon score Money Map.
```

## Acceptance Criteria

- [ ] Service analyzes trends over the last 3 months
- [ ] Identifies spending categories that are increasing
- [ ] Generates concrete, actionable improvement suggestions
- [ ] Advice is generated via Claude API
- [ ] Returns structured response with analysis, problem areas, recommendations, and encouragement

## Technical Specification

### Service Location

```txt
backend/app/services/advisor.py
```

### Service Interface

```python
class AdviceGenerator:
    """
    Generates personalized financial advice via Claude API.
    Analyzes the last 3 months of data to identify trends and provide recommendations.
    """

    async def generate_advice(
        self,
        current_month: MonthData,
        history: list[MonthData]
    ) -> AdviceResponse:
        """
        Generate personalized advice based on financial history.

        Parameters
        ----------
        current_month : MonthData
            The current month's financial data.
        history : list[MonthData]
            The last 2-3 months of financial data for trend analysis.

        Returns
        -------
        AdviceResponse
            Structured advice including analysis, problem areas,
            recommendations, and encouragement.
        """
        pass
```

### Data Models

```python
from pydantic import BaseModel

class ProblemArea(BaseModel):
    category: str
    amount: float
    trend: str  # e.g., "+20%", "-5%"

class AdviceResponse(BaseModel):
    analysis: str  # 2-3 sentence trend analysis
    problem_areas: list[ProblemArea]  # Top 3 spending concerns
    recommendations: list[str]  # 3 actionable suggestions
    encouragement: str  # Personalized encouragement message
```

### Claude API Prompt

```txt
Tu es un conseiller en finances personnelles. Analyse les donnees financieres des 3 derniers mois et fournis des conseils personnalises pour ameliorer le score Money Map.

DONNEES DES 3 DERNIERS MOIS :
{donnees_json}

SCORE ACTUEL : {score} ({label})

REGLES :
- Core <= 50% du revenu
- Choice <= 30% du revenu
- Compound >= 20% du revenu

Fournis :
1. Une analyse des tendances (2-3 phrases)
2. Les 3 postes de depenses les plus problematiques
3. 3 conseils concrets et actionnables pour ameliorer le score
4. Un encouragement personnalise

Format ta reponse en JSON avec cette structure exacte:
{
  "analysis": "string",
  "problem_areas": [
    {"category": "string", "amount": number, "trend": "string"}
  ],
  "recommendations": ["string", "string", "string"],
  "encouragement": "string"
}
```

### Input Data Structure

The service receives monthly data in this format:

```python
class MonthData:
    year: int
    month: int
    total_income: float
    total_core: float
    total_choice: float
    total_compound: float
    core_percentage: float
    choice_percentage: float
    compound_percentage: float
    score: int
    score_label: str
    # Optional: breakdown by subcategory for detailed analysis
    category_breakdown: dict[str, float] | None = None
```

### Trend Calculation

```python
def calculate_trend(current: float, previous: float) -> str:
    """
    Calculate percentage change between two values.

    Returns formatted string like "+15%" or "-8%".
    """
    if previous == 0:
        return "N/A"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.0f}%"
```

### Implementation Steps

1. **Create Pydantic models** for request/response structures
2. **Implement trend analysis** - Calculate month-over-month changes
3. **Build prompt constructor** - Format financial data for Claude
4. **Implement API call** - Send prompt to Claude, parse JSON response
5. **Add error handling** - Handle API failures, invalid responses
6. **Add response validation** - Ensure Claude returns expected structure

### Error Handling

```python
class AdviceGenerationError(Exception):
    """Raised when advice generation fails."""
    pass

class InsufficientDataError(AdviceGenerationError):
    """Raised when there is not enough historical data."""
    pass
```

### Configuration

```python
# Minimum months required for trend analysis
MIN_MONTHS_FOR_ADVICE = 2

# Claude model for advice generation
ADVICE_MODEL = "claude-sonnet-4-20250514"

# Max tokens for advice response
ADVICE_MAX_TOKENS = 1024
```

## Example Response

```json
{
  "analysis": "Tes depenses Choice ont augmente de 15% sur les 3 derniers mois, principalement dans les abonnements. Ton score est stable a 2/3 depuis 2 mois.",
  "problem_areas": [
    {"category": "Subscription services", "amount": 85.0, "trend": "+20%"},
    {"category": "Dining out", "amount": 120.0, "trend": "+10%"},
    {"category": "Entertainment", "amount": 45.0, "trend": "+5%"}
  ],
  "recommendations": [
    "Audite tes abonnements: Perplexity + Claude API representent 25 euros/mois. Un seul suffirait?",
    "Meal prep le dimanche pour reduire les fast-foods de 30%",
    "Fixe-toi un budget Entertainment de 40 euros/mois"
  ],
  "encouragement": "Tu es proche du score Great! Continue ainsi et tu y seras le mois prochain."
}
```

## Testing Requirements

### Unit Tests

```python
# tests/unit/services/test_advisor.py

async def test_generate_advice_with_valid_data():
    """Test advice generation with 3 months of data."""
    pass

async def test_generate_advice_insufficient_data():
    """Test that InsufficientDataError is raised with < 2 months."""
    pass

async def test_calculate_trend_positive():
    """Test trend calculation for increasing values."""
    pass

async def test_calculate_trend_negative():
    """Test trend calculation for decreasing values."""
    pass

async def test_calculate_trend_zero_previous():
    """Test trend calculation when previous value is zero."""
    pass
```

### Integration Tests

```python
# tests/integration/services/test_advisor.py

async def test_advice_generation_api_call():
    """Test actual Claude API call (requires API key)."""
    pass
```

## Notes

- The advice should be in French to match the application's target user
- Batch this with other Claude calls if possible to reduce API costs
- Consider caching advice for the same month to avoid regeneration
- The service should gracefully handle months with no income (division by zero)
