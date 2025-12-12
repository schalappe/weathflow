# Product Requirements Document (PRD)

---

## 1. Executive Summary

### 1.1 Vision

Money Map Manager est une application web personnelle permettant d'automatiser la catégorisation des transactions bancaires exportées depuis Bankin' vers le framework Money Map (50/30/20), de calculer automatiquement le score budgétaire mensuel, et de fournir des conseils personnalisés basés sur l'historique des dépenses.

### 1.2 Problème à résoudre

La gestion manuelle du Money Map est chronophage :

- Export des transactions depuis Bankin' (CSV)
- Catégorisation manuelle de chaque transaction en Core/Choice
- Calcul manuel des totaux et pourcentages
- Pas de suivi historique du score
- Pas de conseils personnalisés basés sur les tendances

### 1.3 Solution proposée

Une application web locale (localhost) qui :

1. Importe les fichiers CSV de Bankin'
2. Utilise l'API Claude pour catégoriser automatiquement les transactions
3. Calcule le Compound et le score Money Map
4. Stocke l'historique dans une base de données locale
5. Génère des conseils personnalisés basés sur les 3 derniers mois

---

## 2. Objectifs et Métriques de Succès

### 2.1 Objectifs

| Objectif       | Description                                          | Priorité |
| -------------- | ---------------------------------------------------- | -------- |
| Automatisation | Réduire le temps de catégorisation de 30min à < 5min | P0       |
| Précision      | Atteindre 90%+ de précision dans la catégorisation   | P0       |
| Suivi          | Permettre le suivi historique du score sur 12+ mois  | P1       |
| Conseils       | Fournir des recommandations actionnables             | P1       |

### 2.2 Métriques de succès

- Temps moyen de traitement d'un mois : < 2 minutes
- Taux de corrections manuelles : < 10%
- Adoption : Utilisation mensuelle régulière

---

## 3. Périmètre Fonctionnel

### 3.1 In Scope (MVP)

- Import de fichiers CSV Bankin'
- Catégorisation automatique via API Claude
- Calcul du score Money Map
- Stockage local des données
- Dashboard de visualisation mensuel
- Historique et évolution du score
- Conseils basés sur les 3 derniers mois

### 3.2 Out of Scope (v1)

- Synchronisation directe avec Bankin' (API)
- Export vers Excel au format Money Map original
- Multi-utilisateurs
- Application mobile native
- Objectifs budgétaires personnalisés

---

## 4. Personas et Use Cases

### 4.1 Persona principal

**Abdallah** - Professionnel soucieux de sa gestion financière

- Utilise Bankin' pour centraliser ses comptes
- Souhaite suivre la règle 50/30/20
- Veut optimiser son taux d'épargne pour investir
- Cherche à automatiser les tâches répétitives

### 4.2 Use Cases principaux

#### UC1 : Import et catégorisation (mono ou multi-mois)

```txt
En tant qu'utilisateur,
Je veux importer mon export Bankin' (qui peut contenir plusieurs mois),
Afin que mes transactions soient automatiquement catégorisées et regroupées par mois.
```

**Critères d'acceptation :**

- [ ] L'utilisateur peut uploader un fichier CSV
- [ ] Le système détecte automatiquement le format Bankin'
- [ ] Le système détecte automatiquement tous les mois présents dans le fichier
- [ ] Les transactions sont groupées par mois (année + mois)
- [ ] Les transactions sont catégorisées via l'API Claude (par batch)
- [ ] Les virements internes sont automatiquement exclus
- [ ] Un résumé par mois est affiché avant validation
- [ ] L'utilisateur peut corriger les catégorisations si nécessaire
- [ ] Les données existantes d'un mois peuvent être écrasées ou fusionnées

#### UC2 : Consultation du score mensuel

```txt
En tant qu'utilisateur,
Je veux voir mon score Money Map du mois,
Afin de savoir si je respecte mes objectifs budgétaires.
```

**Critères d'acceptation :**

- [ ] Affichage des totaux Core, Choice, Compound
- [ ] Affichage des pourcentages vs revenus
- [ ] Calcul et affichage du score (0-3)
- [ ] Affichage du label (Great/Okay/Need Improvement/Poor)

#### UC3 : Suivi de l'évolution

```txt
En tant qu'utilisateur,
Je veux voir l'évolution de mon score sur plusieurs mois,
Afin d'identifier mes tendances et progrès.
```

**Critères d'acceptation :**

- [ ] Graphique d'évolution du score
- [ ] Graphique d'évolution Core/Choice/Compound
- [ ] Comparaison mois par mois

#### UC4 : Conseils personnalisés

```txt
En tant qu'utilisateur,
Je veux recevoir des conseils basés sur mes 3 derniers mois,
Afin d'améliorer mon score Money Map.
```

**Critères d'acceptation :**

- [ ] Analyse des tendances sur 3 mois
- [ ] Identification des postes de dépenses en hausse
- [ ] Suggestions concrètes d'amélioration
- [ ] Conseils générés via API Claude

---

## 5. Spécifications Fonctionnelles Détaillées

### 5.1 Modèle de données

#### 5.1.1 Structure des catégories Money Map

```txt
CORE (Nécessités - Objectif ≤ 50%)
├── Housing (Loyer, charges)
├── Groceries (Courses alimentaires)
├── Utilities (Électricité, gaz, eau)
├── Healthcare (Santé, pharmacie)
├── Transportation (Transport, essence)
├── Basic clothing (Vêtements basiques)
├── Phone and internet (Téléphone, internet)
├── Insurance (Assurances)
└── Debt payments (Remboursements de dettes)

CHOICE (Envies - Objectif ≤ 30%)
├── Dining out (Restaurants, fast-food)
├── Entertainment (Sorties, cinéma, concerts)
├── Travel and vacations (Voyages, vacances)
├── Electronics and gadgets (High-tech)
├── Hobby supplies (Hobbies, loisirs)
├── Fancy clothing (Vêtements de marque)
├── Subscription services (Abonnements streaming, etc.)
├── Home decor (Décoration)
└── Gifts (Cadeaux)

COMPOUND (Épargne/Investissement - Objectif ≥ 20%)
├── Emergency Fund (Fonds d'urgence)
├── Education Fund (Formation)
├── Investments (Investissements)
└── Other (Autres épargnes)

EXCLUDED (Non comptabilisé)
├── Virements internes
└── Transferts entre comptes
```

#### 5.1.2 Mapping Bankin' → Money Map

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

> **Note :** Ce mapping sera utilisé comme contexte initial pour l'API Claude, qui affinera la catégorisation en fonction de la description de chaque transaction.

#### 5.1.3 Schéma de base de données (SQLite)

```sql
-- Table des mois
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

-- Table des transactions
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

-- Table des conseils générés
CREATE TABLE advice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_id INTEGER NOT NULL,
    advice_text TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (month_id) REFERENCES months(id)
);

-- Index pour les performances
CREATE INDEX idx_transactions_month ON transactions(month_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_months_year_month ON months(year, month);
```

### 5.2 Calcul du Score Money Map

#### 5.2.1 Formules

```txt
Total Income = Σ transactions WHERE money_map_type = 'INCOME' AND amount > 0

Total Core = |Σ transactions WHERE money_map_type = 'CORE' AND amount < 0|

Total Choice = |Σ transactions WHERE money_map_type = 'CHOICE' AND amount < 0|

Total Compound = Total Income - Total Core - Total Choice

Core % = (Total Core / Total Income) × 100
Choice % = (Total Choice / Total Income) × 100
Compound % = (Total Compound / Total Income) × 100
```

#### 5.2.2 Calcul du Score

```python
# backend/app/services/calculator.py
from enum import Enum

class ScoreLabel(str, Enum):
    GREAT = "Great"
    OKAY = "Okay"
    NEED_IMPROVEMENT = "Need Improvement"
    POOR = "Poor"

def calculate_score(core_pct: float, choice_pct: float, compound_pct: float) -> tuple[int, ScoreLabel]:
    """
    Calcule le score Money Map basé sur les pourcentages.
    
    Returns:
        tuple: (score: int 0-3, label: ScoreLabel)
    """
    score = 0
    
    if core_pct <= 50:
        score += 1
    if choice_pct <= 30:
        score += 1
    if compound_pct >= 20:
        score += 1
    
    labels = {
        3: ScoreLabel.GREAT,
        2: ScoreLabel.OKAY,
        1: ScoreLabel.NEED_IMPROVEMENT,
        0: ScoreLabel.POOR
    }
    
    return score, labels[score]


def calculate_month_stats(income: float, core: float, choice: float) -> dict:
    """
    Calcule toutes les statistiques pour un mois.
    """
    compound = income - core - choice
    
    core_pct = (core / income * 100) if income > 0 else 0
    choice_pct = (choice / income * 100) if income > 0 else 0
    compound_pct = (compound / income * 100) if income > 0 else 0
    
    score, label = calculate_score(core_pct, choice_pct, compound_pct)
    
    return {
        "total_income": income,
        "total_core": core,
        "total_choice": choice,
        "total_compound": compound,
        "core_percentage": round(core_pct, 1),
        "choice_percentage": round(choice_pct, 1),
        "compound_percentage": round(compound_pct, 1),
        "score": score,
        "score_label": label.value
    }
```

### 5.3 Parsing CSV et Groupement par Mois

#### 5.3.1 Service CSV Parser

```python
# backend/app/services/csv_parser.py
import pandas as pd
from datetime import datetime
from collections import defaultdict

class BankinCSVParser:
    """
    Parse les fichiers CSV exportés depuis Bankin'.
    Gère automatiquement le groupement par mois.
    """
    
    EXPECTED_COLUMNS = [
        "Date", "Description", "Compte", "Montant", 
        "Catégorie", "Sous-Catégorie", "Note", "Pointée"
    ]
    
    def parse(self, file_content: bytes) -> dict:
        """
        Parse le CSV et groupe les transactions par mois.
        
        Returns:
            {
                "total_transactions": int,
                "months": {
                    "2025-01": {
                        "year": 2025,
                        "month": 1,
                        "transactions": [...],
                        "summary": {
                            "count": int,
                            "total_income": float,
                            "total_expenses": float
                        }
                    },
                    ...
                }
            }
        """
        # Lecture du CSV avec séparateur point-virgule
        df = pd.read_csv(
            file_content, 
            sep=';', 
            encoding='utf-8',
            parse_dates=['Date'],
            dayfirst=True  # Format DD/MM/YYYY
        )
        
        # Validation des colonnes
        self._validate_columns(df)
        
        # Nettoyage des montants (string -> float)
        df['Montant'] = df['Montant'].astype(float)
        
        # Extraction année/mois
        df['year'] = df['Date'].dt.year
        df['month'] = df['Date'].dt.month
        df['month_key'] = df['Date'].dt.strftime('%Y-%m')
        
        # Groupement par mois
        grouped = defaultdict(lambda: {"transactions": [], "summary": {}})
        
        for month_key, group in df.groupby('month_key'):
            year, month = map(int, month_key.split('-'))
            
            transactions = group.to_dict('records')
            income = group[group['Montant'] > 0]['Montant'].sum()
            expenses = abs(group[group['Montant'] < 0]['Montant'].sum())
            
            grouped[month_key] = {
                "year": year,
                "month": month,
                "transactions": transactions,
                "summary": {
                    "count": len(transactions),
                    "total_income": round(income, 2),
                    "total_expenses": round(expenses, 2)
                }
            }
        
        # Tri par date (plus ancien au plus récent)
        sorted_months = dict(sorted(grouped.items()))
        
        return {
            "total_transactions": len(df),
            "months": sorted_months
        }
    
    def _validate_columns(self, df: pd.DataFrame):
        """Vérifie que le CSV a le bon format Bankin'."""
        missing = set(self.EXPECTED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Colonnes manquantes: {missing}")
```

#### 5.3.2 Détection des doublons

```python
# backend/app/services/csv_parser.py

def detect_duplicates(
    self, 
    new_transactions: list[dict], 
    existing_transactions: list[dict]
) -> tuple[list[dict], list[dict]]:
    """
    Identifie les transactions déjà présentes en base.
    
    Returns:
        (new_only, duplicates)
    """
    existing_keys = {
        self._transaction_key(t) for t in existing_transactions
    }
    
    new_only = []
    duplicates = []
    
    for t in new_transactions:
        key = self._transaction_key(t)
        if key in existing_keys:
            duplicates.append(t)
        else:
            new_only.append(t)
    
    return new_only, duplicates

def _transaction_key(self, t: dict) -> str:
    """Génère une clé unique pour une transaction."""
    return f"{t['Date']}_{t['Description']}_{t['Montant']}_{t['Compte']}"
```

### 5.4 Intégration API Claude

#### 5.4.1 Prompt de catégorisation

```txt
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

#### 5.4.2 Service de catégorisation (Multi-mois / Batch)

```python
# backend/app/services/categorizer.py
import anthropic
from typing import List, Dict
import json

class TransactionCategorizer:
    """
    Catégorise les transactions via l'API Claude.
    Optimisé pour le traitement par batch multi-mois.
    """
    
    BATCH_SIZE = 50  # Nombre de transactions par appel API
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.system_prompt = CATEGORIZATION_PROMPT  # Prompt ci-dessus
    
    async def categorize_month(
        self, 
        transactions: List[Dict]
    ) -> List[Dict]:
        """
        Catégorise toutes les transactions d'un mois.
        Découpe en batches pour optimiser les appels API.
        """
        results = []
        
        for i in range(0, len(transactions), self.BATCH_SIZE):
            batch = transactions[i:i + self.BATCH_SIZE]
            batch_results = await self._categorize_batch(batch)
            results.extend(batch_results)
        
        return results
    
    async def categorize_all_months(
        self, 
        months_data: Dict[str, Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Catégorise les transactions de plusieurs mois.
        
        Args:
            months_data: {"2025-01": {"transactions": [...]}, ...}
        
        Returns:
            {"2025-01": [categorized_transactions], ...}
        """
        results = {}
        
        for month_key, data in months_data.items():
            transactions = data["transactions"]
            categorized = await self.categorize_month(transactions)
            results[month_key] = categorized
        
        return results
    
    async def _categorize_batch(
        self, 
        transactions: List[Dict]
    ) -> List[Dict]:
        """Catégorise un batch de transactions."""
        
        # Préparer les transactions pour le prompt
        transactions_text = json.dumps([
            {
                "id": i,
                "date": str(t["Date"]),
                "description": t["Description"],
                "amount": t["Montant"],
                "bankin_category": t["Catégorie"],
                "bankin_subcategory": t["Sous-Catégorie"]
            }
            for i, t in enumerate(transactions)
        ], ensure_ascii=False, indent=2)
        
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{
                "role": "user",
                "content": f"""Catégorise ces transactions selon le Money Map.
                
Transactions:
{transactions_text}

Retourne UNIQUEMENT un JSON array (sans markdown) avec pour chaque transaction:
[{{"id": number, "money_map_type": string, "money_map_subcategory": string, "confidence": number}}, ...]
"""
            }]
        )
        
        # Parser la réponse
        response_text = message.content[0].text
        categorizations = json.loads(response_text)
        
        # Merger avec les transactions originales
        for cat in categorizations:
            idx = cat["id"]
            transactions[idx]["money_map_type"] = cat["money_map_type"]
            transactions[idx]["money_map_subcategory"] = cat["money_map_subcategory"]
            transactions[idx]["confidence"] = cat.get("confidence", 1.0)
        
        return transactions
```

#### 5.4.3 Optimisation des coûts API

| Stratégie       | Description                                                                      |
| --------------- | -------------------------------------------------------------------------------- |
| Batching        | Grouper 50 transactions par appel (réduit le nombre d'appels)                    |
| Pré-filtrage    | Exclure automatiquement les virements internes évidents avant l'appel            |
| Cache           | Mémoriser les patterns récurrents (ex: "Netflix" → toujours CHOICE/Subscription) |
| Model selection | Utiliser claude-sonnet pour le meilleur ratio coût/qualité                       |

**Estimation des coûts par import :**

- ~1,350 transactions (10 mois) → ~27 appels API (50 tx/appel)
- Coût estimé : ~$0.50 - $1.00 par import complet

### 5.5 Génération de conseils

#### 5.5.1 Prompt pour les conseils

```txt
Tu es un conseiller en finances personnelles. Analyse les données financières des 3 derniers mois et fournis des conseils personnalisés pour améliorer le score Money Map.

DONNÉES DES 3 DERNIERS MOIS :
{données_json}

SCORE ACTUEL : {score} ({label})

RÈGLES :
- Core ≤ 50% du revenu
- Choice ≤ 30% du revenu  
- Compound ≥ 20% du revenu

Fournis :
1. Une analyse des tendances (2-3 phrases)
2. Les 3 postes de dépenses les plus problématiques
3. 3 conseils concrets et actionnables pour améliorer le score
4. Un encouragement personnalisé

Format ta réponse en sections claires.
```

---

## 6. Architecture Technique

### 6.1 Stack technologique

| Composant                        | Technologie                           | Justification                                       |
| -------------------------------- | ------------------------------------- | --------------------------------------------------- |
| Frontend                         | Next.js 14+ (App Router) + TypeScript | Full-stack React, SSR, API routes intégrées         |
| UI Framework                     | Tailwind CSS + shadcn/ui              | Design moderne, composants prêts                    |
| Backend                          | Python 3.12+ + FastAPI                | Performance, typage, async natif, excellent pour IA |
| Base de données                  | SQLite                                | Léger, pas de serveur, fichier local                |
| ORM Python                       | SQLAlchemy                            | ORM mature, `create_all()` pour init simple         |
| API IA                           | Anthropic Claude API (anthropic-sdk)  | Catégorisation intelligente                         |
| Charts                           | Recharts                              | Intégration React native                            |
| **Package Manager Python**       | **uv**                                | Ultra-rapide (Rust), remplace pip/venv/pip-tools    |
| **Runtime & Package Manager JS** | **bun**                               | Runtime JS ultra-rapide, remplace node/npm/yarn     |
| Communication                    | REST API (FastAPI ↔ Next.js)          | Simple, bien documenté                              |

### 6.2 Architecture applicative

```txt
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Upload    │  │  Dashboard  │  │     History &       │  │
│  │   Page      │  │    Page     │  │   Advice Page       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  Next.js API Routes (proxy optionnel)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (Python FastAPI)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  /upload    │  │  /months    │  │     /advice         │  │
│  │  /parse     │  │  /stats     │  │   /categorize       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  Services: CSVParser | Categorizer | Calculator | Advisor   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │   SQLite    │  │   Claude    │  │    File     │
     │   Database  │  │    API      │  │   System    │
     └─────────────┘  └─────────────┘  └─────────────┘
```

### 6.3 Structure des fichiers

```txt
money-map-manager/
├── frontend/                      # Next.js App (bun)
│   ├── app/
│   │   ├── layout.tsx            # Layout principal
│   │   ├── page.tsx              # Dashboard (page d'accueil)
│   │   ├── import/
│   │   │   └── page.tsx          # Page d'import CSV
│   │   ├── history/
│   │   │   └── page.tsx          # Historique et conseils
│   │   └── api/                   # API routes (proxy optionnel)
│   │       └── [...path]/route.ts
│   ├── components/
│   │   ├── ui/                   # Composants shadcn
│   │   ├── dashboard/
│   │   │   ├── score-card.tsx
│   │   │   ├── metric-card.tsx
│   │   │   └── transaction-table.tsx
│   │   ├── import/
│   │   │   ├── file-dropzone.tsx
│   │   │   └── preview-table.tsx
│   │   └── history/
│   │       ├── score-chart.tsx
│   │       ├── breakdown-chart.tsx
│   │       └── advice-panel.tsx
│   ├── lib/
│   │   ├── api-client.ts         # Client HTTP pour FastAPI
│   │   └── utils.ts
│   ├── types/
│   │   └── index.ts              # Types TypeScript
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── bun.lockb                  # Lock file bun
│
├── backend/                       # Python FastAPI (uv)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # Point d'entrée FastAPI
│   │   ├── config.py             # Configuration
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py
│   │   │   ├── months.py
│   │   │   ├── transactions.py
│   │   │   └── advice.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── csv_parser.py     # Parsing CSV Bankin'
│   │   │   ├── categorizer.py    # Intégration Claude
│   │   │   ├── calculator.py     # Calculs Money Map
│   │   │   └── advisor.py        # Génération conseils
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py       # Config SQLAlchemy + init_db()
│   │       ├── models.py         # Modèles SQLAlchemy
│   │       └── crud.py           # Opérations CRUD
│   ├── pyproject.toml             # Config uv + dépendances
│   └── uv.lock                    # Lock file uv
│
├── data/                          # Données locales
│   └── moneymap.db               # Base SQLite
│
├── .env                           # Variables d'environnement
├── .env.example
├── Makefile                       # Commandes unifiées
└── README.md
```

### 6.4 Variables d'environnement

```env
# .env (racine du projet)

# API Claude
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Backend Python
DATABASE_URL=sqlite:///./data/moneymap.db
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Frontend Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environnement
NODE_ENV=development
PYTHON_ENV=development
```

### 6.5 Dépendances Python (pyproject.toml)

```toml
# backend/pyproject.toml
[project]
name = "money-map-backend"
version = "0.1.0"
description = "Backend API for Money Map Manager"
requires-python = ">=3.12"
dependencies = [
    # Framework
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "python-multipart>=0.0.12",
    
    # Base de données
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
    
    # API Claude
    "anthropic>=0.39.0",
    
    # Parsing & Validation
    "pydantic>=2.10.0",
    "pandas>=2.2.0",
    "python-dateutil>=2.9.0",
    
    # Utilitaires
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0", 
    "httpx>=0.28.0",
    "ruff>=0.8.0",
]
```

### 6.6 Scripts de démarrage

```json
// frontend/package.json
{
  "name": "money-map-frontend",
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}
```

```bash
# ============================================
# INSTALLATION ET DÉMARRAGE
# ============================================

# Prérequis: installer uv et bun
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://bun.sh/install | bash

# ============================================
# BACKEND (Python + FastAPI)
# ============================================

cd backend

# Créer l'environnement et installer les dépendances
uv sync

# Lancer en développement (la DB est créée automatiquement au démarrage)
uv run uvicorn app.main:app --reload --port 8000

# ============================================
# FRONTEND (Next.js + bun)
# ============================================

cd frontend

# Installer les dépendances
bun install

# Lancer en développement
bun dev

# Ajouter shadcn/ui components
bunx --bun shadcn@latest init
bunx --bun shadcn@latest add button card table
```

### 6.7 Initialisation de la base de données

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
    """Crée toutes les tables si elles n'existent pas."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency pour FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# backend/app/main.py
from fastapi import FastAPI
from app.db.database import init_db

app = FastAPI(title="Money Map Manager API")

@app.on_event("startup")
def on_startup():
    init_db()  # Crée les tables au démarrage si nécessaire
```

### 6.8 Makefile (commandes unifiées)

```makefile
# Makefile (racine du projet)

.PHONY: install dev build clean reset-db

# Installation complète
install:
    cd backend && uv sync
    cd frontend && bun install

# Développement (lance les deux serveurs)
dev:
    @echo "Starting backend on http://localhost:8000"
    @echo "Starting frontend on http://localhost:3000"
    @make -j2 dev-backend dev-frontend

dev-backend:
    cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
    cd frontend && bun dev

# Build production
build:
    cd frontend && bun run build

# Reset la base de données (supprime et recrée)
reset-db:
    rm -f data/moneymap.db
    @echo "DB supprimée. Elle sera recréée au prochain démarrage."

# Nettoyage
clean:
    rm -rf backend/.venv
    rm -rf frontend/node_modules
    rm -rf frontend/.next
```

---

## 7. Interface Utilisateur

### 7.1 Pages principales

#### 7.1.1 Page d'accueil / Dashboard

```txt
┌────────────────────────────────────────────────────────────────┐
│  Money Map Manager                        [Import] [History]   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           OCTOBRE 2025 - SCORE: 2/3 (Okay)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │    INCOME     │ │     CORE      │ │    CHOICE     │         │
│  │   €2,823.29   │ │   €1,245.00   │ │    €678.50    │         │
│  │               │ │     44.1%     │ │     24.0%     │         │
│  │               │ │      ✓        │ │       ✓       │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                │
│  ┌───────────────┐                                             │
│  │   COMPOUND    │     ┌─────────────────────────────────┐     │
│  │    €899.79    │     │   [Graphique camembert]         │     │
│  │     31.9%     │     │   Core / Choice / Compound      │     │
│  │      ✓        │     └─────────────────────────────────┘     │
│  └───────────────┘                                             │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DÉTAIL DES TRANSACTIONS                    [Filtrer ▼]  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Date       Description          Montant    Catégorie    │   │
│  │ 29/10     CB Domoro             -2.50€     CHOICE 🍽️    │   │
│  │ 29/10     Virement Salaire    +2823.29€    INCOME 💰    │   │
│  │ ...                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### 7.1.2 Page d'import (Multi-mois)

```txt
┌───────────────────────────────────────────────────────────────┐
│  Money Map Manager                        [Import] [History]  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │         📁 Glissez votre fichier CSV ici                │  │
│  │              ou cliquez pour sélectionner               │  │
│  │                                                         │  │
│  │              Formats acceptés: .csv                     │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 📊 ANALYSE DU FICHIER                                   │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ ✓ 1,355 transactions détectées                          │  │
│  │ ✓ 10 mois détectés (Janvier → Octobre 2025)             │  │
│  │                                                         │  │
│  │ ┌─────────────────────────────────────────────────────┐ │  │
│  │ │ Mois        │ Trans. │ Revenus   │ Dépenses  │ [✓]  │ │  │
│  │ ├─────────────────────────────────────────────────────┤ │  │
│  │ │ Jan 2025    │   89   │ 1,429€    │   901€    │ [✓]  │ │  │
│  │ │ Fév 2025    │   76   │    0€     │   456€    │ [✓]  │ │  │
│  │ │ Mar 2025    │   45   │    0€     │   100€    │ [✓]  │ │  │
│  │ │ Avr 2025    │   52   │  120€     │   234€    │ [✓]  │ │  │
│  │ │ Mai 2025    │   68   │  250€     │   312€    │ [✓]  │ │  │
│  │ │ Juin 2025   │  145   │ 7,514€    │ 1,273€    │ [✓]  │ │  │
│  │ │ Juil 2025   │   98   │  978€     │   515€    │ [✓]  │ │  │
│  │ │ Août 2025   │   87   │  844€     │   240€    │ [✓]  │ │  │
│  │ │ Sept 2025   │  102   │  819€     │   401€    │ [✓]  │ │  │
│  │ │ Oct 2025    │  156   │ 2,878€    │ 1,245€    │ [✓]  │ │  │
│  │ └─────────────────────────────────────────────────────┘ │  │
│  │                                                         │  │
│  │ [Tout sélectionner] [Tout désélectionner]               │  │
│  │                                                         │  │
│  │ Mode d'import:                                          │  │
│  │ ○ Remplacer les données existantes                      │  │
│  │ ● Fusionner (éviter les doublons)                       │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│         [Annuler]    [Catégoriser les mois sélectionnés]      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ ⏳ PROGRESSION DE LA CATÉGORISATION                     │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │                                                         │  │
│  │ Janvier 2025    ████████████████████ 100% ✓             │  │
│  │ Février 2025    ████████████████████ 100% ✓             │  │
│  │ Mars 2025       ████████████░░░░░░░░  60%               │  │
│  │ Avril 2025      ░░░░░░░░░░░░░░░░░░░░   0%  En attente   │  │
│  │ ...                                                     │  │
│  │                                                         │  │
│  │ 🤖 Appels API Claude: 2/10                              │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ ✅ RÉSULTATS                                            │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │                                                         │  │
│  │ Mois        │ Score │ Core   │ Choice │ Compound        │  │
│  │ ────────────────────────────────────────────────────────│  │
│  │ Jan 2025    │ 2 😐  │ 48.2%  │ 32.1%  │ 19.7%           │  │
│  │ Juin 2025   │ 3 🎉  │ 45.0%  │ 25.3%  │ 29.7%           │  │
│  │ Oct 2025    │ 3 🎉  │ 44.1%  │ 24.0%  │ 31.9%           │  │
│  │ ...                                                     │  │
│  │                                                         │  │
│  │ ⚠️ 23 transactions nécessitent vérification             │  │
│  │                                                         │  │
│  │ [Voir les transactions à vérifier] [Terminer l'import]  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### 7.1.3 Page d'historique et conseils

```txt
┌────────────────────────────────────────────────────────────────┐
│  Money Map Manager                        [Import] [History]   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ÉVOLUTION DU SCORE (12 derniers mois)                  │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │  3 ─ ● ─ ─ ─ ● ─ ● ─ ─ ─ ─ ─ ● ─ ─ ─             │   │   │
│  │  │  2 ─ ─ ● ─ ─ ─ ─ ─ ● ─ ● ─ ─ ─ ─ ● ─ ●           │   │   │
│  │  │  1 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─           │   │   │
│  │  │  0 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─           │   │   │
│  │  │    J  F  M  A  M  J  J  A  S  O  N  D            │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RÉPARTITION PAR MOIS                                   │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │  [Graphique en barres empilées]                  │   │   │
│  │  │  Core | Choice | Compound                        │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  💡 CONSEILS PERSONNALISÉS                              │   │
│  │ ──────────────────────────────────────────────────────  │   │
│  │  📊 Analyse des tendances                               │   │
│  │  Tes dépenses "Choice" ont augmenté de 15% sur les      │   │
│  │  3 derniers mois, principalement dans les abonnements.  │   │
│  │                                                         │   │
│  │  ⚠️ Points d'attention                                  │   │
│  │  1. Subscription services: €85/mois (+20%)              │   │
│  │  2. Dining out: €120/mois (+10%)                        │   │
│  │                                                         │   │
│  │  ✅ Recommandations                                     │   │
│  │  1. Audite tes abonnements: Perplexity + Claude API     │   │
│  │     représentent €25/mois. Un seul suffirait?           │   │
│  │  2. Meal prep le dimanche pour réduire les fast-foods   │   │
│  │  3. Tu es proche du score "Great"! Continue ainsi.      │   │
│  │                                                         │   │
│  │  [Générer de nouveaux conseils]                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 Composants UI clés

| Composant      | Description                                 | États                                                               |
| -------------- | ------------------------------------------- | ------------------------------------------------------------------- |
| ScoreCard      | Affiche le score avec code couleur          | Great (vert), Okay (jaune), Need Improvement (orange), Poor (rouge) |
| MetricCard     | Affiche une métrique (Core/Choice/Compound) | Normal, Warning (>seuil), Success (≤seuil)                          |
| TransactionRow | Ligne de transaction éditable               | Default, Editing, Saving                                            |
| FileDropzone   | Zone de drop pour CSV                       | Empty, Dragging, Uploaded, Error                                    |
| MonthSelector  | Sélecteur de mois                           | -                                                                   |
| AdvicePanel    | Panel de conseils IA                        | Loading, Loaded, Error                                              |

---

## 8. API Endpoints (FastAPI)

### 8.1 Configuration FastAPI de base

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, months, transactions, advice

app = FastAPI(
    title="Money Map Manager API",
    description="API pour la gestion du budget Money Map",
    version="1.0.0"
)

# CORS pour Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(months.router, prefix="/api", tags=["months"])
app.include_router(transactions.router, prefix="/api", tags=["transactions"])
app.include_router(advice.router, prefix="/api", tags=["advice"])
```

### 8.2 Upload & Parsing (Multi-mois)

```python
# backend/app/routers/upload.py
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter()

class MonthSummary(BaseModel):
    year: int
    month: int
    transaction_count: int
    total_income: float
    total_expenses: float

class UploadResponse(BaseModel):
    success: bool
    total_transactions: int
    months_detected: list[MonthSummary]
    preview_by_month: dict[str, list[dict]]  # "2025-10": [transactions...]

@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload et parse un fichier CSV Bankin'.
    Détecte automatiquement tous les mois présents.
    """
    # 1. Parse le CSV
    # 2. Groupe les transactions par mois
    # 3. Retourne un résumé par mois
    pass
```

**Request:** `POST /api/upload` (multipart/form-data)

- `file`: Fichier CSV (peut contenir plusieurs mois)

**Response:**

```json
{
  "success": true,
  "total_transactions": 1355,
  "months_detected": [
    {"year": 2025, "month": 1, "transaction_count": 89, "total_income": 1429.12, "total_expenses": 901.25},
    {"year": 2025, "month": 2, "transaction_count": 76, "total_income": 0, "total_expenses": 456.0},
    {"year": 2025, "month": 3, "transaction_count": 45, "total_income": 0, "total_expenses": 100.0},
    {"year": 2025, "month": 10, "transaction_count": 156, "total_income": 2823.29, "total_expenses": 1245.50}
  ],
  "preview_by_month": {
    "2025-01": [
      {"date": "2025-01-30", "description": "Virement Salaire", "amount": 1100.0, ...},
      ...
    ],
    "2025-10": [...]
  }
}
```

### 8.3 Catégorisation (Multi-mois)

```python
# backend/app/routers/upload.py
class CategorizeRequest(BaseModel):
    months_to_process: list[str]  # ["2025-01", "2025-02", ...] ou ["all"]
    import_mode: str  # "replace" | "merge"

class MonthResult(BaseModel):
    year: int
    month: int
    transactions_categorized: int
    low_confidence_count: int
    score: int
    score_label: str

class CategorizeResponse(BaseModel):
    success: bool
    months_processed: list[MonthResult]
    total_api_calls: int

@router.post("/categorize", response_model=CategorizeResponse)
async def categorize_transactions(request: CategorizeRequest):
    """
    Catégorise les transactions via l'API Claude.
    Traite tous les mois sélectionnés et calcule le score de chacun.
    
    import_mode:
    - "replace": Écrase les données existantes du mois
    - "merge": Ajoute aux données existantes (évite les doublons)
    """
    pass
```

**Request:** `POST /api/categorize`

```json
{
  "months_to_process": ["all"],
  "import_mode": "replace"
}
```

**Response:**

```json
{
  "success": true,
  "months_processed": [
    {
      "year": 2025,
      "month": 1,
      "transactions_categorized": 89,
      "low_confidence_count": 5,
      "score": 2,
      "score_label": "Okay"
    },
    {
      "year": 2025,
      "month": 10,
      "transactions_categorized": 156,
      "low_confidence_count": 8,
      "score": 3,
      "score_label": "Great"
    }
  ],
  "total_api_calls": 3
}
```

### 8.4 Données mensuelles

```python
# backend/app/routers/months.py
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/months/{year}/{month}")
async def get_month_data(year: int, month: int):
    """
    Récupère les données d'un mois spécifique.
    """
    # ... implementation
```

**Request:** `GET /api/months/2025/10`

**Response:**

```json
{
  "month": {
    "year": 2025,
    "month": 10,
    "total_income": 2823.29,
    "total_core": 1245.00,
    "total_choice": 678.50,
    "total_compound": 899.79,
    "core_percentage": 44.1,
    "choice_percentage": 24.0,
    "compound_percentage": 31.9,
    "score": 3,
    "score_label": "Great"
  },
  "transactions": [...]
}
```

### 8.5 Historique

```python
@router.get("/months/history")
async def get_history(months: int = 12):
    """
    Récupère l'historique des N derniers mois.
    """
    # ... implementation
```

**Request:** `GET /api/months/history?months=12`

**Response:**

```json
{
  "months": [
    {
      "year": 2025,
      "month": 10,
      "score": 3,
      "core_percentage": 44.1,
      "choice_percentage": 24.0,
      "compound_percentage": 31.9
    }
  ]
}
```

### 8.6 Conseils

```python
# backend/app/routers/advice.py
router = APIRouter()

class GenerateAdviceRequest(BaseModel):
    year: int
    month: int

@router.post("/advice/generate")
async def generate_advice(request: GenerateAdviceRequest):
    """
    Génère des conseils personnalisés via Claude
    basés sur les 3 derniers mois.
    """
    # ... implementation
```

**Request:** `POST /api/advice/generate`

```json
{
  "year": 2025,
  "month": 10
}
```

**Response:**

```json
{
  "success": true,
  "advice": {
    "analysis": "Tes dépenses Choice ont augmenté de 15%...",
    "problem_areas": [
      {"category": "Subscription services", "amount": 85, "trend": "+20%"},
      {"category": "Dining out", "amount": 120, "trend": "+10%"}
    ],
    "recommendations": [
      "Audite tes abonnements : Perplexity + Claude API...",
      "Meal prep le dimanche pour réduire les fast-foods",
      "Tu es proche du score Great! Continue ainsi."
    ],
    "encouragement": "Ton score est stable depuis 2 mois..."
  }
}
```

### 8.7 Mise à jour transaction

```python
# backend/app/routers/transactions.py
router = APIRouter()

class UpdateTransactionRequest(BaseModel):
    money_map_type: str
    money_map_subcategory: str

@router.patch("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: int, 
    request: UpdateTransactionRequest
):
    """
    Met à jour la catégorisation d'une transaction.
    Recalcule automatiquement les stats du mois.
    """
    # ... implementation
```

**Request:** `PATCH /api/transactions/123`

```json
{
  "money_map_type": "CORE",
  "money_map_subcategory": "Groceries"
}
```

**Response:**

```json
{
  "success": true,
  "transaction": {...},
  "updated_month_stats": {...}
}
```

---

## 9. Roadmap & Phases de développement

### Phase 1 : MVP (2-3 semaines)

| Tâche                                                | Estimation | Priorité |
| ---------------------------------------------------- | ---------- | -------- |
| Setup projet (Next.js/bun + FastAPI/uv + SQLite)     | 3h         | P0       |
| Modèles SQLAlchemy + database.py (init_db)           | 2h         | P0       |
| Service parser CSV Bankin' (Python)                  | 4h         | P0       |
| Service catégorisation Claude (anthropic SDK)        | 6h         | P0       |
| Service calcul score Money Map                       | 2h         | P0       |
| API endpoints FastAPI (upload, months, transactions) | 4h         | P0       |
| UI Next.js : Page d'import                           | 4h         | P0       |
| UI Next.js : Dashboard mensuel                       | 6h         | P0       |
| Tests pytest + intégration                           | 4h         | P0       |

### Phase 2 : Historique & Visualisation (1-2 semaines)

| Tâche                              | Estimation | Priorité |
| ---------------------------------- | ---------- | -------- |
| API endpoint historique (FastAPI)  | 2h         | P1       |
| Client API Next.js (fetch wrapper) | 2h         | P1       |
| Graphiques d'évolution (Recharts)  | 6h         | P1       |
| Page historique Next.js            | 4h         | P1       |
| Sélecteur de période               | 2h         | P1       |

### Phase 3 : Conseils IA (1 semaine)

| Tâche                                   | Estimation | Priorité |
| --------------------------------------- | ---------- | -------- |
| Prompt engineering conseils             | 4h         | P1       |
| Service advisor.py (intégration Claude) | 3h         | P1       |
| API endpoint /advice                    | 1h         | P1       |
| UI panel conseils Next.js               | 3h         | P1       |

### Phase 4 : Polish & Améliorations (1 semaine)

| Tâche                                         | Estimation | Priorité |
| --------------------------------------------- | ---------- | -------- |
| Édition inline des catégories (React state)   | 4h         | P2       |
| Filtres et recherche transactions             | 3h         | P2       |
| Export données (JSON/CSV)                     | 2h         | P2       |
| Dark mode (Tailwind)                          | 2h         | P2       |
| Documentation README                          | 2h         | P2       |
| Makefile complet (dev, build, migrate, clean) | 1h         | P2       |

---

## 10. Risques et Mitigations

| Risque                                | Probabilité | Impact | Mitigation                                                 |
| ------------------------------------- | ----------- | ------ | ---------------------------------------------------------- |
| Coût API Claude élevé                 | Moyenne     | Moyen  | Batch les requêtes, cache les résultats, limite les appels |
| Précision catégorisation insuffisante | Moyenne     | Élevé  | UI de correction facile, amélioration continue du prompt   |
| Format CSV Bankin' change             | Faible      | Moyen  | Parser flexible avec détection automatique de colonnes     |
| Perte de données locales              | Faible      | Élevé  | Backup automatique de la DB SQLite, export JSON            |

---

## 11. Considérations Futures (v2+)

- **Objectifs personnalisés** : Permettre de modifier les seuils 50/30/20
- **Multi-devises** : Support des transactions en devises étrangères
- **Récurrence** : Détection et gestion des dépenses récurrentes
- **Budget prévisionnel** : Projection des dépenses futures
- **Notifications** : Alertes quand on dépasse un seuil
- **Export Money Map** : Génération du fichier Excel au format original
- **PWA** : Application installable sur mobile
- **Sync cloud optionnel** : Backup chiffré sur cloud personnel

---

## 12. Annexes

### A. Exemple de fichier CSV Bankin'

```csv
Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée
"31/10/2025";"Total Option System' Epargne";"Livret A";"4.67";"Entrées d'argent";"Economies";"";"Non"
"29/10/2025";"CB Domoro";"Compte De Dépôts";"-2.5";"Alimentation & Restau.";"Fast foods";"";"Non"
```

### B. Structure Money Map de référence

| Section  | Catégorie                                                                                                           | Objectif |
| -------- | ------------------------------------------------------------------------------------------------------------------- | -------- |
| CORE     | Housing, Groceries, Utilities, Healthcare, Transportation, Basic clothing, Phone/internet, Insurance, Debt payments | ≤ 50%    |
| CHOICE   | Dining out, Entertainment, Travel, Electronics, Hobbies, Fancy clothing, Subscriptions, Home decor, Gifts           | ≤ 30%    |
| COMPOUND | Emergency Fund, Education Fund, Investments, Other                                                                  | ≥ 20%    |

### C. Codes couleur UI

```css
/* Score Labels */
--score-great: #22c55e;      /* Green */
--score-okay: #eab308;       /* Yellow */
--score-improvement: #f97316; /* Orange */
--score-poor: #ef4444;       /* Red */

/* Categories */
--category-income: #3b82f6;  /* Blue */
--category-core: #8b5cf6;    /* Purple */
--category-choice: #f59e0b;  /* Amber */
--category-compound: #10b981; /* Emerald */
--category-excluded: #6b7280; /* Gray */
```

---
