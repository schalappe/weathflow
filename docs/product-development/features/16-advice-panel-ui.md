# Feature 16: Advice Panel UI

## Overview

Build the advice display component showing analysis, problem areas, recommendations, and encouragement with a regenerate button. This component consumes the Advice API (Feature 15) to display personalized financial advice to the user.

**Size:** M (Medium)
**Dependencies:** Feature #15 (Advice API and Storage), Feature #13 (History Page UI)

## User Story

From UC4 - Conseils personnalises:

```txt
En tant qu'utilisateur,
Je veux recevoir des conseils bases sur mes 3 derniers mois,
Afin d'ameliorer mon score Money Map.
```

### Acceptance Criteria (from PRD)

- [ ] Analyse des tendances sur 3 mois
- [ ] Identification des postes de depenses en hausse
- [ ] Suggestions concretes d'amelioration
- [ ] Conseils generes via API Claude
- [ ] Bouton pour regenerer de nouveaux conseils

## Technical Specifications

### Component Location

```txt
frontend/
  components/
    history/
      advice-panel.tsx    # Main advice display component
```

### Integration

The AdvicePanel component is displayed on the History page below the charts section.

### Data Source

Uses the Advice API endpoints:

```txt
GET  /api/advice/{year}/{month}     # Retrieve existing advice
POST /api/advice/generate           # Generate new advice
```

Response structure (from Feature #15):

```json
{
  "success": true,
  "advice": {
    "analysis": "Tes depenses Choice ont augmente de 15%...",
    "problem_areas": [
      {"category": "Subscription services", "amount": 85.0, "trend": "+20%"},
      {"category": "Dining out", "amount": 120.0, "trend": "+10%"}
    ],
    "recommendations": [
      "Audite tes abonnements...",
      "Meal prep le dimanche...",
      "Continue ainsi!"
    ],
    "encouragement": "Tu es proche du score Great!"
  },
  "generated_at": "2025-10-15T14:30:00Z",
  "was_cached": boolean
}
```

## UI Specifications

### Visual Design

From PRD wireframe (section 7.1.3):

```txt
+---------------------------------------------------------------+
|  CONSEILS PERSONNALISES                                       |
+---------------------------------------------------------------+
|                                                               |
|  Analyse des tendances                                        |
|  Tes depenses "Choice" ont augmente de 15% sur les            |
|  3 derniers mois, principalement dans les abonnements.        |
|                                                               |
|  Points d'attention                                           |
|  1. Subscription services: 85 euros/mois (+20%)               |
|  2. Dining out: 120 euros/mois (+10%)                         |
|                                                               |
|  Recommandations                                              |
|  1. Audite tes abonnements: Perplexity + Claude API           |
|     representent 25 euros/mois. Un seul suffirait?            |
|  2. Meal prep le dimanche pour reduire les fast-foods         |
|  3. Tu es proche du score "Great"! Continue ainsi.            |
|                                                               |
|  [Generer de nouveaux conseils]                               |
|                                                               |
+---------------------------------------------------------------+
```

### Component States

| State        | Description                            | Visual                          |
| ------------ | -------------------------------------- | ------------------------------- |
| Loading      | Fetching advice from API               | Skeleton loader                 |
| Loaded       | Advice successfully retrieved          | Full advice display             |
| Empty        | No advice exists for current month     | Prompt to generate              |
| Error        | API call failed                        | Error message with retry button |
| Regenerating | Generating new advice (button clicked) | Button shows loading spinner    |

### Section Icons

| Section         | Icon | Purpose                            |
| --------------- | ---- | ---------------------------------- |
| Analysis        | 📊   | Trend analysis overview            |
| Problem Areas   | ⚠️   | Categories exceeding targets       |
| Recommendations | ✅   | Actionable improvement suggestions |
| Encouragement   | 💪   | Positive reinforcement             |

### Color Coding for Trends

| Trend    | Color | Example     |
| -------- | ----- | ----------- |
| Positive | Red   | +20% (bad)  |
| Negative | Green | -15% (good) |
| Neutral  | Gray  | 0%          |

## Component API

### Props Interface

```typescript
interface AdvicePanelProps {
  year: number;
  month: number;
  className?: string;
}
```

### Internal Types

```typescript
interface ProblemArea {
  category: string;
  amount: number;
  trend: string;
}

interface AdviceData {
  analysis: string;
  problem_areas: ProblemArea[];
  recommendations: string[];
  encouragement: string;
}

interface AdviceState {
  advice: AdviceData | null;
  generatedAt: string | null;
  isLoading: boolean;
  isRegenerating: boolean;
  error: string | null;
}
```

### API Client Functions

Add to `lib/api-client.ts`:

```typescript
export async function getAdvice(year: number, month: number): Promise<GetAdviceResponse> {
  const response = await fetch(`${API_URL}/api/advice/${year}/${month}`);
  if (!response.ok) throw new Error('Failed to fetch advice');
  return response.json();
}

export async function generateAdvice(
  year: number,
  month: number,
  regenerate: boolean = false
): Promise<GenerateAdviceResponse> {
  const response = await fetch(`${API_URL}/api/advice/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ year, month, regenerate }),
  });
  if (!response.ok) throw new Error('Failed to generate advice');
  return response.json();
}
```

## Implementation Notes

### Data Fetching Strategy

1. On component mount, fetch existing advice via `GET /api/advice/{year}/{month}`
2. If no advice exists (`exists: false`), show empty state with generate button
3. When user clicks "Generer", call `POST /api/advice/generate`
4. When user clicks "Regenerer", call `POST /api/advice/generate` with `regenerate: true`

### Loading States

```txt
Initial Load:
  - Show skeleton for entire panel

Regenerating:
  - Keep existing advice visible
  - Show loading spinner on button
  - Disable button during regeneration
```

### Empty State

When no advice exists for the selected month:

```txt
+---------------------------------------------------------------+
|  CONSEILS PERSONNALISES                                       |
+---------------------------------------------------------------+
|                                                               |
|              Aucun conseil disponible                         |
|                                                               |
|   Generez des conseils personnalises bases sur vos            |
|   3 derniers mois de transactions.                            |
|                                                               |
|              [Generer des conseils]                           |
|                                                               |
+---------------------------------------------------------------+
```

### Error States

| Error Type        | Message                                                        | Action              |
| ----------------- | -------------------------------------------------------------- | ------------------- |
| Month not found   | "Aucune donnee pour ce mois"                                   | Link to Import page |
| Insufficient data | "Il faut au moins 2 mois de donnees pour generer des conseils" | Link to Import page |
| API failure       | "Erreur lors de la generation. Reessayez."                     | Retry button        |
| Network error     | "Probleme de connexion"                                        | Retry button        |

### Timestamp Display

Show when advice was generated:

```txt
Conseils generes le 15 octobre 2025 a 14h30
```

Use relative time for recent advice:

```txt
Conseils generes il y a 2 heures
```

## Responsive Design

### Desktop (>= 1024px)

- Full width within the history page container
- All sections visible

### Tablet (768px - 1023px)

- Full width
- Slightly reduced padding

### Mobile (< 768px)

- Full width with reduced padding
- Problem areas stack vertically
- Recommendations display as numbered list

## Technology Stack

| Technology | Purpose                    |
| ---------- | -------------------------- |
| React      | Component framework        |
| shadcn/ui  | Card, Button, Skeleton     |
| TypeScript | Type safety                |
| date-fns   | Date formatting (optional) |

## shadcn/ui Components Used

- `Card`, `CardHeader`, `CardTitle`, `CardContent` - Container structure
- `Button` - Regenerate action
- `Skeleton` - Loading state
- `Alert` - Error display

## Testing Requirements

### Unit Tests

```typescript
// tests/components/history/advice-panel.test.tsx

describe('AdvicePanel', () => {
  it('shows skeleton while loading', () => {});
  it('displays advice data correctly', () => {});
  it('shows empty state when no advice exists', () => {});
  it('shows error state on API failure', () => {});
  it('calls generate API when button clicked', () => {});
  it('calls regenerate API with regenerate=true', () => {});
  it('disables button while regenerating', () => {});
  it('displays problem areas with correct trend colors', () => {});
  it('formats generated_at timestamp correctly', () => {});
});
```

### Integration Tests

```typescript
describe('AdvicePanel Integration', () => {
  it('fetches advice on mount', () => {});
  it('updates display after successful regeneration', () => {});
  it('handles insufficient data error gracefully', () => {});
});
```

## Implementation Steps

1. **Create types** in `types/index.ts` for advice data structures
2. **Add API functions** to `lib/api-client.ts`
3. **Build AdvicePanel component** with all states (loading, loaded, empty, error)
4. **Implement regenerate functionality** with loading state
5. **Add to History page** below the charts
6. **Style with Tailwind** following design specs
7. **Add unit tests** for all component states
8. **Add integration tests** for API interactions

## Out of Scope

- Advice history (viewing previous months' advice)
- Advice comparison across months
- Export advice to PDF/text
- Push notifications for new advice
