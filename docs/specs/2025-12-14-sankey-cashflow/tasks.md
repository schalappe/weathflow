# Task Breakdown: Sankey Cash Flow Diagram

## Overview

Total Tasks: 18
Estimated Complexity: Medium
Primary Stack: FastAPI + Next.js + Recharts

## Task List

### Backend Layer

#### Task Group 1: Response Schema and Repository

**Dependencies:** None

- [x] 1.0 Complete backend data layer
  - [x] 1.1 Write 4 focused tests for aggregation logic
    - Test aggregate_by_subcategory returns grouped data
    - Test empty month_ids returns empty list
    - Test EXCLUDED transactions are filtered out
    - Test amounts are absolute values for expenses
  - [x] 1.2 Create Pydantic response models in `backend/app/responses/cashflow.py`
    - `CategoryBreakdown`: subcategory (str), amount (float >= 0)
    - `CashFlowData`: totals + breakdowns for each category + deficit
    - `CashFlowResponse`: data + period_months
  - [x] 1.3 Add `aggregate_by_subcategory()` method to TransactionRepository
    - Query with GROUP BY money_map_type, money_map_subcategory
    - Filter to INCOME, CORE, CHOICE, COMPOUND only
    - Use func.abs() for expense amounts
    - Return list of (type, subcategory, total) tuples
  - [x] 1.4 Ensure tests pass (run only tests from 1.1)

**Acceptance Criteria:**

- Response models validate with Pydantic
- Repository method returns correct aggregations
- Tests from 1.1 pass

---

#### Task Group 2: Service and API Endpoint

**Dependencies:** Task Group 1

- [x] 2.0 Complete backend API layer
  - [x] 2.1 Write 4 focused tests for cashflow endpoint
    - Test GET /api/months/cashflow returns 200 with valid data
    - Test months=0 fetches all months
    - Test deficit calculation when spending > income
    - Test empty response when no months exist
  - [x] 2.2 Create cashflow service in `backend/app/services/data/cashflow.py`
    - `get_cashflow_data(month_repo, transaction_repo, months)` function
    - Fetch months via `month_repo.get_recent(months)`
    - Aggregate via `transaction_repo.aggregate_by_subcategory(month_ids)`
    - Group results by category, calculate deficit
    - Return CashFlowData object
  - [x] 2.3 Add `/cashflow` endpoint to `backend/app/api/months.py`
    - GET /api/months/cashflow with months Query param (default=12, ge=0, le=24)
    - Inject MonthRepo and TransactionRepo
    - Call cashflow service, return CashFlowResponse
    - Error handling matching existing patterns
  - [x] 2.4 Ensure tests pass (run only tests from 2.1)

**Acceptance Criteria:**

- Endpoint accessible at GET /api/months/cashflow
- Period parameter works (0=all, 1-24=limited)
- Deficit calculated correctly
- Tests from 2.1 pass

---

### Frontend Layer

#### Task Group 3: Types and API Client

**Dependencies:** Task Group 2

- [x] 3.0 Complete frontend API integration
  - [x] 3.1 Add TypeScript types to `frontend/types/index.ts`
    - `CategoryBreakdown` interface
    - `CashFlowData` interface
    - `CashFlowResponse` interface
  - [x] 3.2 Add `getCashFlow()` function to `frontend/lib/api-client.ts`
    - Follow existing pattern from `getMonthsHistory()`
    - Accept months parameter (default 12)
    - Return Promise<CashFlowResponse>
  - [x] 3.3 Add translations to `frontend/lib/translations.ts`
    - sankeyChart.title: "Flux de trésorerie"
    - sankeyChart.subtitle: "Répartition des revenus par catégorie"
    - sankeyChart.empty: "Aucune donnée disponible"
    - sankeyChart.error: "Impossible d'afficher le diagramme"
    - sankeyChart.deficit: "Déficit"
    - Add subcategory translations if missing

**Acceptance Criteria:**

- Types match backend response schema
- API client function compiles without errors
- Translations complete for French UI

---

#### Task Group 4: Sankey Chart Component

**Dependencies:** Task Group 3

- [x] 4.0 Complete Sankey chart component
  - [x] 4.1 Write 4 focused tests for SankeyChart component
    - Test renders empty state when data is null
    - Test renders chart when data provided
    - Test deficit node appears when deficit > 0
    - Test correct number of nodes/links generated
  - [x] 4.2 Create `frontend/components/history/sankey-chart.tsx`
    - Props: `data: CashFlowData | null`, `className?: string`
    - Card wrapper with gradient icon (GitBranch icon)
    - ErrorBoundary wrapper
    - Empty state handling
  - [x] 4.3 Implement `transformToSankeyData()` function
    - Build nodes array: Income, Core, Choice, Compound, subcategories
    - Build links array: Income→Categories, Categories→Subcategories
    - Apply CATEGORY_COLORS to nodes
    - Add Deficit node (red) when deficit > 0
  - [x] 4.4 Implement custom tooltip component
    - Show source → target flow
    - Display formatted currency amount
    - Follow existing CustomTooltipContent pattern
  - [x] 4.5 Ensure tests pass (run only tests from 4.1)

**Acceptance Criteria:**

- Component renders Recharts Sankey diagram
- Colors match CATEGORY_COLORS
- Deficit node shows in red when applicable
- Tests from 4.1 pass

---

#### Task Group 5: History Page Integration

**Dependencies:** Task Group 4

- [x] 5.0 Complete history page integration
  - [x] 5.1 Write 3 focused tests for integration
    - Test cashflow data loads when period changes
    - Test SankeyChart receives correct props
    - Test loading state during fetch
  - [x] 5.2 Extend HistoryState in `frontend/components/history/history-client.tsx`
    - Add `cashFlowData: CashFlowData | null` to state
    - Add `CASHFLOW_LOADED` action type
    - Add `CASHFLOW_ERROR` action type
  - [x] 5.3 Add parallel fetch for cashflow data
    - Fetch getCashFlow(period) alongside getMonthsHistory(period)
    - Dispatch CASHFLOW_LOADED on success
    - Handle errors gracefully
  - [x] 5.4 Render SankeyChart below charts grid
    - Add full-width section below the 2-column grid
    - Pass cashFlowData to SankeyChart
    - Show loading skeleton during fetch
  - [x] 5.5 Ensure tests pass (run only tests from 5.1)

**Acceptance Criteria:**

- Sankey chart appears below existing charts
- Data updates when period selector changes
- Loading state displays during fetch
- Tests from 5.1 pass

---

### Testing Layer

#### Task Group 6: Test Review and Gap Fill

**Dependencies:** Task Groups 1-5

- [x] 6.0 Complete testing coverage
  - [x] 6.1 Review tests from groups 1-5 (~15 tests)
  - [x] 6.2 Identify critical gaps for cashflow feature
    - Edge cases: zero income, all categories empty
    - Boundary conditions: months=0, months=24
    - Error scenarios: API failure handling
  - [x] 6.3 Write up to 6 additional tests for gaps
  - [x] 6.4 Run all cashflow-related tests
    - Backend: `uv run pytest tests/ -k cashflow -v`
    - Frontend: `bun test sankey -v`

**Acceptance Criteria:**

- All ~21 tests pass
- Critical edge cases covered
- No regressions in existing functionality

---

## Execution Order

1. **Task Group 1** (Backend Data Layer) — Foundation for API
2. **Task Group 2** (Backend API) — Depends on response models and repository
3. **Task Group 3** (Frontend Types/API) — Needs backend endpoint ready
4. **Task Group 4** (Sankey Component) — Needs types defined
5. **Task Group 5** (Integration) — Needs component ready
6. **Task Group 6** (Testing) — Final verification after all implementation

## Notes

- Backend uses existing MonthRepository.get_recent() for period filtering
- Frontend extends existing reducer pattern (no new state management)
- Recharts Sankey is already available in project dependencies
- Follow existing error handling and logging patterns
