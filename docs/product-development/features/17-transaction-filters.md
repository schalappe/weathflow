# Feature 17: Transaction Filters

## Overview

Add filtering capabilities to the transaction table, allowing users to filter by category type, date range, and search by description. This enhances the existing TransactionTable component (Feature #8) to help users find specific transactions quickly.

**Size:** S (Small)
**Dependencies:** Feature #8 (Monthly Dashboard UI)

## User Story

```txt
En tant qu'utilisateur,
Je veux filtrer mes transactions par categorie, date et description,
Afin de retrouver rapidement des transactions specifiques.
```

### Acceptance Criteria

- [ ] Filter transactions by Money Map category type (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED)
- [ ] Filter transactions by date range within the selected month
- [ ] Search transactions by description text (case-insensitive)
- [ ] Filters can be combined (category + date + search)
- [ ] Clear all filters with a single action
- [ ] Filter state persists during pagination
- [ ] Show active filter count indicator
- [ ] Empty state when no transactions match filters

## Technical Specifications

### Component Location

```txt
frontend/
  components/
    dashboard/
      transaction-table.tsx       # Existing - add filter props
      transaction-filters.tsx     # New - filter controls component
```

### Filter Types

```typescript
// types/index.ts

type MoneyMapType = 'INCOME' | 'CORE' | 'CHOICE' | 'COMPOUND' | 'EXCLUDED';

interface TransactionFilters {
  categoryTypes: MoneyMapType[];      // Multi-select categories
  dateFrom: string | null;            // ISO date string (YYYY-MM-DD)
  dateTo: string | null;              // ISO date string (YYYY-MM-DD)
  searchQuery: string;                // Description search text
}

// Default empty filters
const DEFAULT_FILTERS: TransactionFilters = {
  categoryTypes: [],
  dateFrom: null,
  dateTo: null,
  searchQuery: '',
};
```

### Backend API Changes

Extend the existing endpoint `GET /api/months/{year}/{month}` with query parameters:

```txt
GET /api/months/{year}/{month}?page=1&page_size=20&category=CORE,CHOICE&date_from=2025-10-01&date_to=2025-10-15&search=netflix
```

| Parameter | Type   | Description                                         |
| --------- | ------ | --------------------------------------------------- |
| category  | string | Comma-separated list of category types to include   |
| date_from | string | Filter transactions on or after this date (ISO)     |
| date_to   | string | Filter transactions on or before this date (ISO)    |
| search    | string | Case-insensitive search in transaction descriptions |

### Backend Implementation

Update `backend/app/routers/months.py`:

```python
from datetime import date
from typing import Annotated

@router.get("/{year}/{month}")
async def get_month_detail(
    year: int,
    month: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None, description="Comma-separated category types"),
    date_from: date | None = Query(default=None, description="Filter from date"),
    date_to: date | None = Query(default=None, description="Filter to date"),
    search: str | None = Query(default=None, description="Search in description"),
    db: Session = Depends(get_db),
):
    """Get month detail with optional transaction filters."""
    # Parse category filter
    category_types = category.split(",") if category else None

    # Apply filters in CRUD layer
    ...
```

Update `backend/app/db/crud.py`:

```python
def get_filtered_transactions(
    db: Session,
    month_id: int,
    category_types: list[str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Transaction], int]:
    """
    Get transactions with optional filters.

    Returns
    -------
    tuple[list[Transaction], int]
        Filtered transactions and total count.
    """
    query = db.query(Transaction).filter(Transaction.month_id == month_id)

    if category_types:
        query = query.filter(Transaction.money_map_type.in_(category_types))

    if date_from:
        query = query.filter(Transaction.date >= date_from)

    if date_to:
        query = query.filter(Transaction.date <= date_to)

    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    total = query.count()
    transactions = query.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return transactions, total
```

## UI Specifications

### Visual Design

Filters appear above the transaction table within the same Card component:

```txt
+---------------------------------------------------------------+
|  TRANSACTIONS                                    [Page 1/5]   |
+---------------------------------------------------------------+
|                                                               |
|  [Category v] [Date From] [Date To] [Search...     ] [Clear]  |
|                                                               |
|  Active filters: 2                                            |
|                                                               |
+---------------------------------------------------------------+
|  Date       Description          Amount      Category         |
|  29/10     CB Domoro             -2.50       CHOICE           |
|  29/10     Virement Salaire    +2823.29      INCOME           |
|  ...                                                          |
+---------------------------------------------------------------+
```

### Filter Components

| Component | Type         | Description                                     |
| --------- | ------------ | ----------------------------------------------- |
| Category  | Multi-select | Dropdown with checkboxes for each category type |
| Date From | Date picker  | Calendar input for start date                   |
| Date To   | Date picker  | Calendar input for end date                     |
| Search    | Text input   | Debounced input field (300ms)                   |
| Clear     | Button       | Resets all filters to default                   |

### Category Multi-Select Options

| Value    | Label    | Color Badge |
| -------- | -------- | ----------- |
| INCOME   | Income   | Blue        |
| CORE     | Core     | Purple      |
| CHOICE   | Choice   | Amber       |
| COMPOUND | Compound | Emerald     |
| EXCLUDED | Excluded | Gray        |

### Filter Behavior

1. **Category Filter**: Select one or more categories. Empty selection = all categories.
2. **Date Range**: Constrained to the selected month's boundaries.
3. **Search**: Triggers after 300ms of no typing (debounced).
4. **Pagination**: Resets to page 1 when filters change.
5. **Clear Button**: Only visible when at least one filter is active.

### Empty State

When filters return no results:

```txt
+---------------------------------------------------------------+
|  TRANSACTIONS                                                 |
+---------------------------------------------------------------+
|                                                               |
|  [Category: CORE v] [Date From] [Date To] [netflix   ] [Clear]|
|                                                               |
|                   No transactions found                       |
|                                                               |
|         Try adjusting your filters or [clear all filters]     |
|                                                               |
+---------------------------------------------------------------+
```

## Component API

### TransactionFilters Props

```typescript
interface TransactionFiltersProps {
  filters: TransactionFilters;
  onFiltersChange: (filters: TransactionFilters) => void;
  monthYear: { year: number; month: number };  // Constrain date range
  disabled?: boolean;
}
```

### Updated TransactionTable Props

```typescript
interface TransactionTableProps {
  transactions: TransactionResponse[];
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  onTransactionClick: (transaction: TransactionResponse) => void;
  isLoading: boolean;
  // New props for filtering
  filters: TransactionFilters;
  onFiltersChange: (filters: TransactionFilters) => void;
  monthYear: { year: number; month: number };
}
```

### API Client Extension

Add to `lib/api-client.ts`:

```typescript
export interface GetMonthDetailParams {
  year: number;
  month: number;
  page?: number;
  pageSize?: number;
  filters?: TransactionFilters;
}

export async function getMonthDetail({
  year,
  month,
  page = 1,
  pageSize = 20,
  filters,
}: GetMonthDetailParams): Promise<MonthDetailResponse> {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(pageSize));

  if (filters?.categoryTypes.length) {
    params.set('category', filters.categoryTypes.join(','));
  }
  if (filters?.dateFrom) {
    params.set('date_from', filters.dateFrom);
  }
  if (filters?.dateTo) {
    params.set('date_to', filters.dateTo);
  }
  if (filters?.searchQuery) {
    params.set('search', filters.searchQuery);
  }

  const response = await fetch(`${API_URL}/api/months/${year}/${month}?${params}`);
  if (!response.ok) throw new Error('Failed to fetch month detail');
  return response.json();
}
```

## Implementation Notes

### State Management

Filters are managed at the dashboard page level, passed down to components:

```typescript
// app/page.tsx or components/dashboard/dashboard-client.tsx

const [filters, setFilters] = useState<TransactionFilters>(DEFAULT_FILTERS);
const [page, setPage] = useState(1);

// Reset page when filters change
const handleFiltersChange = (newFilters: TransactionFilters) => {
  setFilters(newFilters);
  setPage(1);  // Reset to first page
};
```

### Debounced Search

Use a custom hook for debounced search input:

```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}
```

### Date Range Constraints

The date picker should be constrained to the selected month:

```typescript
// For October 2025
const minDate = new Date(2025, 9, 1);   // Oct 1
const maxDate = new Date(2025, 9, 31);  // Oct 31
```

### Active Filter Count

```typescript
function getActiveFilterCount(filters: TransactionFilters): number {
  let count = 0;
  if (filters.categoryTypes.length > 0) count++;
  if (filters.dateFrom) count++;
  if (filters.dateTo) count++;
  if (filters.searchQuery.trim()) count++;
  return count;
}
```

## Responsive Design

### Desktop (>= 1024px)

- All filter controls in a single horizontal row
- Full-width search input

### Tablet (768px - 1023px)

- Filters wrap to two rows if needed
- Category dropdown and date pickers on first row
- Search input on second row

### Mobile (< 768px)

- Stacked vertical layout
- Each filter control takes full width
- Collapsible filter section (optional enhancement)

## shadcn/ui Components Used

- `Select` / `MultiSelect` - Category filter dropdown
- `Popover` + `Calendar` - Date pickers (date-from, date-to)
- `Input` - Search text field
- `Button` - Clear filters action
- `Badge` - Active filter indicators

## Testing Requirements

### Unit Tests

```typescript
// tests/components/dashboard/transaction-filters.test.tsx

describe('TransactionFilters', () => {
  it('renders all filter controls', () => {});
  it('calls onFiltersChange when category is selected', () => {});
  it('calls onFiltersChange when date range is set', () => {});
  it('debounces search input by 300ms', () => {});
  it('shows clear button only when filters are active', () => {});
  it('clears all filters when clear button clicked', () => {});
  it('constrains date picker to selected month', () => {});
  it('shows active filter count correctly', () => {});
});
```

### Backend Tests

```python
# tests/test_months_router.py

def test_get_month_with_category_filter():
    """Filter by single category type."""

def test_get_month_with_multiple_categories():
    """Filter by multiple category types."""

def test_get_month_with_date_range():
    """Filter by date from and date to."""

def test_get_month_with_search():
    """Filter by description search."""

def test_get_month_with_combined_filters():
    """Apply all filters simultaneously."""

def test_get_month_search_case_insensitive():
    """Search should be case-insensitive."""

def test_get_month_empty_filters_returns_all():
    """No filters should return all transactions."""
```

### Integration Tests

```typescript
describe('Transaction Filtering Integration', () => {
  it('filters update URL query params', () => {});
  it('page resets to 1 when filters change', () => {});
  it('shows empty state when no results match', () => {});
  it('preserves filters during pagination', () => {});
});
```

## Implementation Steps

1. **Backend: Add filter parameters** to `GET /api/months/{year}/{month}` endpoint
2. **Backend: Update CRUD** with `get_filtered_transactions` function
3. **Backend: Add tests** for all filter combinations
4. **Frontend: Create types** for `TransactionFilters` in `types/index.ts`
5. **Frontend: Build TransactionFilters component** with all controls
6. **Frontend: Update TransactionTable** to accept filter props
7. **Frontend: Update dashboard page** to manage filter state
8. **Frontend: Update API client** with filter parameters
9. **Frontend: Add unit tests** for filter components
10. **Frontend: Add integration tests** for filtering flow

## Out of Scope

- Saving filter presets
- Export filtered results
- Advanced search (regex, multiple terms)
- Filter by amount range
- Filter by account name
- URL persistence of filter state (nice-to-have for future)
