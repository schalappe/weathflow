# Spec Requirements: Sankey Cash Flow Diagram

## Initial Description

Add a Sankey diagram (cash flow visualization) to the history page. Based on the selected period (3 months, 6 months, 12 months, all), the backend provides total Core/Choice amounts and totals for each subcategory (Core: Housing, Groceries, etc. / Choice: Dining out, Entertainment, etc.).

## Requirements Discussion

### Questions & Answers

**Q1:** I assume the Sankey diagram should show Income → Categories (Core/Choice/Compound) → Subcategories. Is that the flow you want, or something different?
**A:** Show Income → Categories (Core/Choice/Compound) → Subcategories. Take into consideration that Compound can be negative if Core + Choice > Income.

**Q2:** For subcategories, are they currently stored in the database?
**A:** Yes, subcategories already exist (stored in `money_map_subcategory` field).

**Q3:** Should the chart aggregate totals over the selected period or show averages/per-month data?
**A:** Aggregate totals over the selected period.

**Q4:** For the UI placement, should the Sankey diagram replace an existing chart, be added as a third chart, or have its own tab/section?
**A:** Add as a third chart below the existing grid (all visible at once, scrollable).

**Q5:** Should the Sankey diagram be interactive or is a static visualization sufficient?
**A:** Static visualization is sufficient.

**Q6:** What should be explicitly OUT of scope?
**A:** Focus on the Sankey diagram only.

### Follow-up Questions

**Q1:** For negative Compound (when Core + Choice > Income), how should we visualize this?
**A:** Option A - Show a "Deficit" node flowing out from Income (red color to indicate overspending).

**Q2:** Clarification on "third chart" vs "own tab/section"?
**A:** Option A - Add the Sankey as a third card below the existing 2x grid (all visible at once, scrollable).

### Existing Code References

- `frontend/components/history/history-client.tsx` - Main history page component with period state management
- `frontend/components/history/period-selector.tsx` - Period selector (3, 6, 12 months, all)
- `frontend/components/history/breakdown-chart.tsx` - Existing Recharts implementation for reference
- `backend/app/db/models/transaction.py` - Transaction model with `money_map_type` and `money_map_subcategory` fields
- `backend/app/services/categorization/mapping.py` - Subcategory definitions (Groceries, Housing, Dining out, etc.)

## Visual Assets

### Files Found

No visual assets provided.

### Visual Insights

N/A

## Requirements Summary

### Functional Requirements

- Display a Sankey diagram showing cash flow: Income → Categories → Subcategories
- Support period selection (3, 6, 12 months, or all) using existing PeriodSelector
- Aggregate transaction totals across the selected period
- Show three main category nodes: Core, Choice, Compound
- Show subcategory nodes for each category (e.g., Groceries, Housing under Core)
- Handle negative Compound scenario with a "Deficit" node (red color) when Core + Choice > Income
- Backend endpoint to provide aggregated data grouped by category and subcategory

### Data Structure

**Existing fields to use:**

- `money_map_type`: INCOME, CORE, CHOICE, COMPOUND, EXCLUDED
- `money_map_subcategory`: Groceries, Housing, Transportation, Utilities, Healthcare, Insurance, Phone and internet, Dining out, Entertainment, Hobby supplies, Subscription services, Fancy clothing, Electronics and gadgets, Home decor, Gifts, Travel and vacations, Investments

**Flow visualization:**

```text
Income ──┬── Core ──────┬── Groceries
         │              ├── Housing
         │              ├── Transportation
         │              ├── Utilities
         │              └── ...
         │
         ├── Choice ────┬── Dining out
         │              ├── Entertainment
         │              ├── Subscription services
         │              └── ...
         │
         └── Compound ──┬── Investments
                        └── ...

(When Core + Choice > Income)
Income ──┬── Core ──────┬── ...
         ├── Choice ────┬── ...
         └── Deficit ◄── (red, indicates overspending)
```

### Reusability Opportunities

- Existing `PeriodSelector` component for period selection
- Existing Recharts setup in `breakdown-chart.tsx`
- Existing history page state management with `useReducer`
- Existing `getMonthsHistory` API client function (may need new endpoint or extension)

### Scope Boundaries

**In Scope:**

- Sankey diagram component using Recharts
- Backend endpoint for aggregated category/subcategory totals
- Integration with existing period selector
- Deficit visualization for overspending scenarios
- Static (non-interactive) visualization

**Out of Scope:**

- Interactive features (click to filter, drill-down)
- Animations or transitions
- Export functionality for the chart
- Comparison between periods
- Any modifications to existing charts
- Mobile-specific optimizations

### Technical Considerations

- Recharts has a Sankey component that can be used
- Backend needs to aggregate by `money_map_type` and `money_map_subcategory`
- Period parameter already exists in the history API
- Deficit calculation: `deficit = (core_total + choice_total) - income_total` (if positive)
