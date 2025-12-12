# Spec Requirements: Transaction Filters

## Initial Description

Add filtering by category type, date range, and search by description to the transaction table.

## Requirements Discussion

### Source Document

All requirements are defined in the existing feature specification:
`docs/product-development/features/17-transaction-filters.md`

### Key Requirements Extracted

**Q1: Filter Location**
**Answer:** Filters appear above the transaction table within the same Card component (filter bar layout).

**Q2: Category Filter**
**Answer:** Multi-select dropdown with checkboxes for each category type (INCOME, CORE, CHOICE, COMPOUND, EXCLUDED). Empty selection = all categories.

**Q3: Date Range Filter**
**Answer:** Constrained to the selected month's boundaries. For example, October 2025 would constrain to Oct 1-31.

**Q4: Search Behavior**
**Answer:** Case-insensitive "contains" match with 300ms debounce. No advanced search options.

**Q5: Filter Persistence**
**Answer:** Page resets to 1 when filters change. Filter state persists during pagination within the same month.

**Q6: URL State**
**Answer:** Out of scope. Local component state only. URL persistence is a "nice-to-have for future."

**Q7: Empty State**
**Answer:** Show "No transactions found" message with "Try adjusting your filters or [clear all filters]" link.

**Q8: Out of Scope**
**Answer:**

- Saving filter presets
- Export filtered results
- Advanced search (regex, multiple terms)
- Filter by amount range
- Filter by account name
- URL persistence of filter state

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Transaction Table - Path: `frontend/components/dashboard/transaction-table.tsx`
- Feature: Dashboard Page - Path: `frontend/app/page.tsx` or `frontend/components/dashboard/`
- Backend: Months Router - Path: `backend/app/routers/months.py`
- Backend: CRUD - Path: `backend/app/db/crud.py`

### Follow-up Questions

None required - feature document is comprehensive.

## Visual Assets

### Files Provided

No visual assets provided.

### Visual Design (from spec)

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

ASCII mockup provided in feature document showing filter bar layout:

- Horizontal row: [Category v] [Date From] [Date To] [Search...] [Clear]
- Active filter count indicator
- Empty state with clear filters link

## Requirements Summary

### Functional Requirements

- Filter transactions by Money Map category type (multi-select)
- Filter transactions by date range within selected month
- Search transactions by description text (case-insensitive, debounced)
- Filters can be combined (category + date + search)
- Clear all filters with a single action
- Filter state persists during pagination
- Show active filter count indicator
- Empty state when no transactions match filters

### Technical Requirements

- Backend: Extend `GET /api/months/{year}/{month}` with query parameters
- Backend: Add `get_filtered_transactions` function to CRUD layer
- Frontend: New `TransactionFilters` component
- Frontend: Update `TransactionTable` to accept filter props
- Frontend: Update API client with filter parameters
- Frontend: Use shadcn/ui components (Select, Popover + Calendar, Input, Button, Badge)

### Reusability Opportunities

- Existing TransactionTable component to extend
- Existing category color scheme (blue/purple/amber/emerald/gray)
- Existing pagination logic
- shadcn/ui components already in use

### Scope Boundaries

**In Scope:**

- Category multi-select filter
- Date range filter (constrained to month)
- Description search (debounced, case-insensitive)
- Clear all filters button
- Active filter count indicator
- Empty state handling
- Responsive design (desktop/tablet/mobile)
- Backend filter support with pagination

**Out of Scope:**

- Saved filter presets
- Export filtered results
- Advanced search (regex, multiple terms)
- Filter by amount range
- Filter by account name
- URL persistence of filter state

### Technical Considerations

- 300ms debounce for search input
- Date pickers constrained to selected month boundaries
- Page resets to 1 when filters change
- Server-side filtering (filters passed as query params)
- Filter state managed at dashboard page level
