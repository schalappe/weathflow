# Transaction Categorization Service Specification

## Overview

The Transaction Categorization Service integrates with the Claude API to automatically categorize bank transactions into Money Map categories (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED). It uses batch processing to optimize API costs and provides confidence scores for each categorization.

## Objectives

| Objective       | Description                                      | Priority |
| --------------- | ------------------------------------------------ | -------- |
| Automation      | Reduce categorization time from 30min to < 5min  | P0       |
| Precision       | Achieve 90%+ accuracy in categorization          | P0       |
| Cost Efficiency | Batch transactions to minimize API calls         | P0       |

## Money Map Categories

```text
INCOME - Revenus
├── Job : Salaires, primes

CORE - Nécessités (objectif ≤ 50% des revenus)
├── Housing : Loyer, charges de copropriété
├── Groceries : Courses alimentaires (supermarché, épicerie)
├── Utilities : Électricité, gaz, eau
├── Healthcare : Médecin, pharmacie, mutuelle
├── Transportation : Transport en commun, essence, entretien véhicule
├── Basic clothing : Vêtements de nécessité
├── Phone and internet : Forfaits téléphone/internet
├── Insurance : Assurances (habitation, auto, etc.)
└── Debt payments : Remboursements de crédits

CHOICE - Envies (objectif ≤ 30% des revenus)
├── Dining out : Restaurants, fast-food, cafés, bars
├── Entertainment : Cinéma, concerts, sorties
├── Travel and vacations : Voyages, hôtels, vacations
├── Electronics and gadgets : High-tech, gadgets
├── Hobby supplies : Équipement pour hobbies
├── Fancy clothing : Vêtements de marque/luxe
├── Subscription services : Netflix, Spotify, abonnements divers
├── Home decor : Décoration, ameublement non essentiel
└── Gifts : Cadeaux

COMPOUND - Épargne/Investissement (objectif ≥ 20% des revenus)
├── Emergency Fund : Épargne de précaution
├── Education Fund : Formation, livres éducatifs
├── Investments : Investissements, placements
└── Other : Autres formes d'épargne

EXCLUDED - À exclure du calcul
├── Virements internes entre comptes
└── Transferts d'épargne (déjà comptés ailleurs)
```

## Bankin' to Money Map Mapping

This mapping serves as context for the Claude API to guide categorization:

| Catégorie Bankin'      | Sous-catégorie Bankin' | Catégorie Money Map | Sous-catégorie Money Map |
| ---------------------- | ---------------------- | ------------------- | ------------------------ |
| Entrées d'argent       | Salaires               | INCOME              | Job                      |
| Entrées d'argent       | Virements internes     | EXCLUDED            | -                        |
| Entrées d'argent       | Economies              | EXCLUDED            | -                        |
| Alimentation & Restau. | Supermarché / Epicerie | CORE                | Groceries                |
| Alimentation & Restau. | Fast foods             | CHOICE              | Dining out               |
| Alimentation & Restau. | Sortie au restaurant   | CHOICE              | Dining out               |
| Alimentation & Restau. | Café                   | CHOICE              | Dining out               |
| Abonnements            | Câble / Satellite      | CHOICE              | Subscription services    |
| Abonnements            | Abonnements - Autres   | CHOICE              | Subscription services    |
| Transport              | Transports en commun   | CORE                | Transportation           |
| Transport              | Essence                | CORE                | Transportation           |
| Logement               | Loyer                  | CORE                | Housing                  |
| Logement               | Charges                | CORE                | Utilities                |
| Santé                  | Pharmacie              | CORE                | Healthcare               |
| Santé                  | Médecin                | CORE                | Healthcare               |
| Loisirs & Sorties      | Bars / Clubs           | CHOICE              | Entertainment            |
| Loisirs & Sorties      | Sortie au restaurant   | CHOICE              | Dining out               |
| Shopping               | Vêtements              | CHOICE              | Fancy clothing           |
| Shopping               | High-Tech              | CHOICE              | Electronics and gadgets  |
| Retraits, Chq. et Vir. | Virements internes     | EXCLUDED            | -                        |
| Banque                 | Epargne                | COMPOUND            | Investments              |
| Dépenses pro           | Services en ligne      | CHOICE              | Subscription services    |

> **Note**: This mapping provides initial guidance. The Claude API refines categorization based on each transaction's description.

## Categorization Prompt

```text
Tu es un assistant spécialisé dans la catégorisation de transactions bancaires selon le framework Money Map (règle 50/30/20).

CATÉGORIES MONEY MAP :

INCOME - Revenus
- Job : Salaires, primes

CORE - Nécessités (objectif ≤ 50% des revenus)
- Housing : Loyer, charges de copropriété
- Groceries : Courses alimentaires (supermarché, épicerie)
- Utilities : Électricité, gaz, eau
- Healthcare : Médecin, pharmacie, mutuelle
- Transportation : Transport en commun, essence, entretien véhicule
- Basic clothing : Vêtements de nécessité
- Phone and internet : Forfaits téléphone/internet
- Insurance : Assurances (habitation, auto, etc.)
- Debt payments : Remboursements de crédits

CHOICE - Envies (objectif ≤ 30% des revenus)
- Dining out : Restaurants, fast-food, cafés, bars
- Entertainment : Cinéma, concerts, sorties
- Travel and vacations : Voyages, hôtels, vacations
- Electronics and gadgets : High-tech, gadgets
- Hobby supplies : Équipement pour hobbies
- Fancy clothing : Vêtements de marque/luxe
- Subscription services : Netflix, Spotify, abonnements divers
- Home decor : Décoration, ameublement non essentiel
- Gifts : Cadeaux

COMPOUND - Épargne/Investissement (objectif ≥ 20% des revenus)
- Emergency Fund : Épargne de précaution
- Education Fund : Formation, livres éducatifs
- Investments : Investissements, placements
- Other : Autres formes d'épargne

EXCLUDED - À exclure du calcul
- Virements internes entre comptes
- Transferts d'épargne (déjà comptés ailleurs)

RÈGLES DE CATÉGORISATION :
1. Les virements entre tes propres comptes = EXCLUDED
2. Les abonnements professionnels (Anthropic, Cloud, etc.) = CHOICE > Subscription services
3. Les courses en supermarché = CORE > Groceries
4. Les restaurants/fast-food = CHOICE > Dining out
5. Les cafés (consommation) = CHOICE > Dining out
6. Netflix, Spotify = CHOICE > Subscription services

Pour chaque transaction, retourne un JSON avec :
{
  "money_map_type": "CORE|CHOICE|INCOME|COMPOUND|EXCLUDED",
  "money_map_subcategory": "sous-catégorie correspondante"
}
```

## Service Interface

### Input

```python
from pydantic import BaseModel, Field

class TransactionInput(BaseModel):
    """Transaction data to be categorized."""

    id: int
    date: str
    description: str
    amount: float
    bankin_category: str
    bankin_subcategory: str
```

### Output

```python
from enum import Enum

from pydantic import BaseModel, Field

class MoneyMapType(str, Enum):
    """Money Map category types."""

    INCOME = "INCOME"
    CORE = "CORE"
    CHOICE = "CHOICE"
    COMPOUND = "COMPOUND"
    EXCLUDED = "EXCLUDED"

class CategorizationResult(BaseModel):
    """Result of categorizing a single transaction."""

    id: int
    money_map_type: MoneyMapType
    money_map_subcategory: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
```

## Batch Processing

### Configuration

| Parameter  | Value | Description                          |
| ---------- | ----- | ------------------------------------ |
| BATCH_SIZE | 50    | Number of transactions per API call  |
| MODEL      | claude-sonnet-4-20250514 | Model for categorization  |
| MAX_TOKENS | 4096  | Maximum response tokens              |

### Cost Estimation

- ~1,350 transactions (10 months) → ~27 API calls (50 tx/call)
- Estimated cost: ~$0.50 - $1.00 per complete import

### Optimization Strategies

| Strategy        | Description                                                                      |
| --------------- | -------------------------------------------------------------------------------- |
| Batching        | Group 50 transactions per call (reduces total API calls)                         |
| Pre-filtering   | Auto-exclude obvious internal transfers before API call                          |
| Cache           | Memorize recurring patterns (e.g., "Netflix" → always CHOICE/Subscription)       |
| Model selection | Use claude-sonnet for best cost/quality ratio                                    |

## API Response Format

The Claude API must return a JSON array (no markdown):

```json
[
  {
    "id": 0,
    "money_map_type": "CHOICE",
    "money_map_subcategory": "Dining out",
    "confidence": 0.95
  },
  {
    "id": 1,
    "money_map_type": "CORE",
    "money_map_subcategory": "Groceries",
    "confidence": 0.98
  }
]
```

## Error Handling

| Error Type           | Handling Strategy                                      |
| -------------------- | ------------------------------------------------------ |
| API Rate Limit       | Exponential backoff with retry                         |
| Invalid JSON         | Log error, mark batch for manual review                |
| Missing confidence   | Default to 1.0                                         |
| Unknown category     | Log warning, mark transaction for manual review        |
| Partial batch fail   | Retry failed items only                                |

## Database Schema (Reference)

The service updates the following fields in the `transactions` table:

```sql
money_map_type TEXT CHECK(money_map_type IN ('INCOME', 'CORE', 'CHOICE', 'COMPOUND', 'EXCLUDED')),
money_map_subcategory TEXT,
is_manually_corrected BOOLEAN DEFAULT FALSE,
```

## Dependencies

- **Internal**: CSV Parser Service (provides parsed transactions)
- **External**: Anthropic Claude API (`anthropic` SDK)

## Success Metrics

| Metric                        | Target     |
| ----------------------------- | ---------- |
| Categorization accuracy       | ≥ 90%      |
| Low confidence rate           | < 10%      |
| Processing time (100 tx)      | < 30 sec   |
| API cost per transaction      | < $0.001   |

## File Structure

```text
backend/app/services/
├── categorizer.py           # Main categorization service
├── categorization_prompt.py # System prompt constant
└── category_mapping.py      # Bankin' to Money Map mapping
```
