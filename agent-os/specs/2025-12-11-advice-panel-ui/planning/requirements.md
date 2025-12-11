# Spec Requirements: Advice Panel UI

## Initial Description

Build the advice display component showing analysis, problem areas, recommendations, and encouragement with a regenerate button. This component consumes the Advice API (Feature 15) to display personalized financial advice on the History page.

## Requirements Discussion

### Source Document

All requirements derived from comprehensive feature specification at:
`docs/product-development/features/16-advice-panel-ui.md`

### Key Requirements from Feature Doc

**Q1:** Where should the advice panel be displayed?
**Answer:** On the History page below the charts section (not Monthly Dashboard). Component location: `frontend/components/history/advice-panel.tsx`

**Q2:** What should the regenerate button behavior be?
**Answer:** Show loading spinner on button, disable during regeneration, keep existing advice visible while regenerating. No confirmation dialog needed.

**Q3:** How should the four advice sections be displayed?
**Answer:** As distinct visual sections with icons:

- 📊 Analysis (trend analysis overview)
- ⚠️ Problem Areas (categories exceeding targets)
- ✅ Recommendations (actionable improvement suggestions)
- 💪 Encouragement (positive reinforcement)

**Q4:** How should trends be color-coded?
**Answer:**

- Red for positive/increasing trends (bad - spending up)
- Green for negative/decreasing trends (good - spending down)
- Gray for neutral (0%)

**Q5:** What happens when no advice exists?
**Answer:** Show empty state with call-to-action: "Aucun conseil disponible" message and "Générer des conseils" button.

**Q6:** How should errors be displayed?
**Answer:** Inline within the advice panel with specific messages:

- Month not found: Link to Import page
- Insufficient data: "Il faut au moins 2 mois de données" with Import link
- API failure: "Erreur lors de la génération. Réessayez." with retry button
- Network error: "Problème de connexion" with retry button

**Q7:** What is out of scope?
**Answer:**

- Advice history (viewing previous months' advice)
- Advice comparison across months
- Export advice to PDF/text
- Push notifications for new advice

### Existing Code to Reference

**Similar Features Identified:**

- Feature: History Page UI - Path: `frontend/components/history/`
- Feature: Dashboard metric cards - Path: `frontend/components/dashboard/`
- Components to potentially reuse: Card, Button, Skeleton, Alert from shadcn/ui
- Backend logic: Advice API already complete at `backend/app/routers/advice.py`

### Visual Assets

### Files Provided

No visual assets provided.

### Visual Design from Feature Doc

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

ASCII wireframe in feature doc (section 7.1.3) shows:

- Card container with "CONSEILS PERSONNALISÉS" header
- Analysis section with trend overview text
- Problem areas as numbered list with category, amount, trend
- Recommendations as numbered list
- Regenerate button at bottom
- Empty state with centered message and generate button

## Requirements Summary

### Functional Requirements

- Display advice panel on History page below charts
- Fetch existing advice on component mount via GET `/api/advice/{year}/{month}`
- Show empty state when no advice exists (`exists: false`)
- Generate advice via POST `/api/advice/generate` when button clicked
- Regenerate with `regenerate: true` flag to replace cached advice
- Display all four sections: analysis, problem_areas, recommendations, encouragement
- Color-code trend indicators (red=increase, green=decrease, gray=neutral)
- Show timestamp: "Conseils générés le [date] à [time]" or relative time

### Component States

| State        | Description                            | Visual                          |
| ------------ | -------------------------------------- | ------------------------------- |
| Loading      | Fetching advice from API               | Skeleton loader                 |
| Loaded       | Advice successfully retrieved          | Full advice display             |
| Empty        | No advice exists for current month     | Prompt to generate              |
| Error        | API call failed                        | Error message with retry button |
| Regenerating | Generating new advice (button clicked) | Button shows loading spinner    |

### Props Interface

```typescript
interface AdvicePanelProps {
  year: number;
  month: number;
  className?: string;
}
```

### Reusability Opportunities

- shadcn/ui Card, Button, Skeleton, Alert components
- Existing History page patterns for component structure
- Dashboard metric card patterns for visual consistency

### Scope Boundaries

**In Scope:**

- AdvicePanel component with all states
- API client functions (getAdvice, generateAdvice)
- TypeScript types for advice data
- Integration on History page
- Unit and integration tests
- Responsive design (desktop, tablet, mobile)

**Out of Scope:**

- Advice history (viewing previous months' advice)
- Advice comparison across months
- Export advice to PDF/text
- Push notifications for new advice
- Auto-generate advice on page load

### Technical Considerations

- Uses existing Advice API endpoints (Feature 15)
- TypeScript types needed in `types/index.ts`
- API functions needed in `lib/api-client.ts`
- shadcn/ui components: Card, Button, Skeleton, Alert
- Optional: date-fns for timestamp formatting
- Responsive breakpoints: Desktop (≥1024px), Tablet (768-1023px), Mobile (<768px)
