# Frontend Architecture

> **Last Updated:** December 2025
> **Framework:** Next.js 14+ (App Router) | React 18+ | TypeScript 5.x | Tailwind CSS 3.x

This document provides a comprehensive guide to the Money Map Manager frontend architecture, explaining the component structure, state management patterns, and data flow.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [App Router Pages](#app-router-pages)
- [Component Organization](#component-organization)
- [Type System](#type-system)
- [API Client](#api-client)
- [State Management](#state-management)
- [UI Component Library](#ui-component-library)
- [Chart Implementations](#chart-implementations)
- [Theming & Dark Mode](#theming--dark-mode)
- [Internationalization](#internationalization)
- [Performance Optimizations](#performance-optimizations)

---

## Overview

The frontend is a modern Next.js application using the App Router with a clean, feature-driven architecture:

```text
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (Pages)                             │
│  - App Router pages (server components)                 │
│  - Minimal logic, render client components              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Application Layer (Client Components)                  │
│  - State management with useReducer                     │
│  - Data fetching and caching                            │
│  - User interaction handling                            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Feature Components                                     │
│  - Dashboard, Import, History, Advice components        │
│  - Organized by feature in components/{feature}/        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  UI Components (shadcn/ui)                              │
│  - Reusable primitives (Button, Card, Dialog, etc.)     │
│  - Built on Radix UI + Tailwind CSS                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Infrastructure                                         │
│  - Centralized API client (lib/api-client.ts)           │
│  - Type definitions (types/index.ts)                    │
│  - Utilities (lib/utils.ts)                             │
└─────────────────────────────────────────────────────────┘
```

**Key Principles:**

- Server components by default, client components only when needed
- Feature-based component organization
- Centralized API communication
- Type-safe data flow with TypeScript
- Minimal external dependencies (no Redux, no Zustand)

---

## Project Structure

```text
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx            # Root layout with nav
│   ├── page.tsx              # Dashboard (/)
│   ├── import/
│   │   └── page.tsx          # Import page (/import)
│   ├── history/
│   │   └── page.tsx          # History page (/history)
│   └── advice/
│       └── page.tsx          # Advice page (/advice)
│
├── components/               # React components
│   ├── ui/                   # Reusable UI primitives (43 files)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── theme-provider.tsx
│   │   └── ...
│   │
│   ├── dashboard/            # Dashboard feature (8 files)
│   │   ├── dashboard-client.tsx
│   │   ├── score-card.tsx
│   │   ├── metric-card.tsx
│   │   ├── spending-pie-chart.tsx
│   │   ├── transaction-table.tsx
│   │   └── ...
│   │
│   ├── import/               # Import feature (6 files)
│   │   ├── import-page-client.tsx
│   │   ├── file-dropzone.tsx
│   │   ├── progress-panel.tsx
│   │   └── ...
│   │
│   ├── history/              # History feature (7 files)
│   │   ├── history-client.tsx
│   │   ├── score-chart.tsx
│   │   ├── breakdown-chart.tsx
│   │   ├── sankey-chart.tsx
│   │   └── ...
│   │
│   └── advice/               # Advice feature (1 file)
│       └── advice-page-client.tsx
│
├── lib/                      # Utilities and helpers
│   ├── api-client.ts         # Centralized API client
│   ├── utils.ts              # Utility functions
│   └── translations.ts       # French i18n strings
│
├── types/                    # TypeScript type definitions
│   └── index.ts              # All shared types
│
├── public/                   # Static assets
│   └── logo.svg
│
└── package.json              # Dependencies (managed with bun)
```

---

## App Router Pages

### Root Layout

**File:** `app/layout.tsx` (139 lines)

**Purpose:** Global layout with navigation and theme provider.

**Key Features:**

- Sticky navigation header with brand logo
- 4 main navigation links (Dashboard, Import, History, Advice)
- Theme toggle integration
- Sonner toast notifications
- Responsive grid layout (max-w-7xl container)
- French locale (`lang="fr"`)

**Code Structure:**

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={cn(delius.variable, googleSansText.variable)}>
        <ThemeProvider>
          <div className="min-h-screen bg-background">
            {/* Navigation */}
            <nav className="sticky top-0 z-50 border-b bg-background/95">
              <div className="container mx-auto flex items-center justify-between px-4 py-3">
                <Logo />
                <NavLinks />
                <ThemeToggle />
              </div>
            </nav>

            {/* Main content */}
            <main className="container mx-auto max-w-7xl px-4 py-6">
              {children}
            </main>
          </div>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
```

---

### Dashboard Page (`/`)

**File:** `app/page.tsx`

**Purpose:** Main Money Map dashboard with monthly overview and transactions.

**Renders:** `DashboardClient` component

**Features:**

- Month selector dropdown
- Score card (0-3 display)
- Metric cards (Income, Core, Choice, Compound)
- Interactive pie chart
- Filterable transaction table
- Transaction category editing

---

### Import Page (`/import`)

**File:** `app/import/page.tsx`

**Purpose:** CSV upload and transaction categorization workflow.

**Renders:** `ImportPageClient` component

**Workflow:**

1. Upload CSV file (drag-drop or click)
2. Preview detected months
3. Select months to import
4. Choose import mode (replace or merge)
5. Trigger categorization
6. View results summary

---

### History Page (`/history`)

**File:** `app/history/page.tsx`

**Purpose:** Historical analysis and trends visualization.

**Renders:** `HistoryClient` component

**Features:**

- Period selector (6 or 12 months)
- Score line chart (evolution over time)
- Spending breakdown chart (stacked bar)
- Cash flow Sankey diagram
- Monthly advice panels

---

### Advice Page (`/advice`)

**File:** `app/advice/page.tsx`

**Purpose:** AI-generated personalized budget advice.

**Renders:** `AdvicePageClient` component

**Features:**

- Month selector
- Advice display with analysis
- Problem areas identification
- Actionable recommendations
- Encouragement message
- Regenerate advice button

---

## Component Organization

### Feature-Based Structure

Components are organized by feature, not by type:

```text
✅ Good (Feature-based)
components/
├── dashboard/
│   ├── dashboard-client.tsx
│   ├── score-card.tsx
│   └── transaction-table.tsx
└── import/
    ├── import-page-client.tsx
    └── file-dropzone.tsx

❌ Bad (Type-based)
components/
├── cards/
│   └── score-card.tsx
├── tables/
│   └── transaction-table.tsx
└── forms/
    └── file-dropzone.tsx
```

**Benefits:**

- Easy to find related components
- Easier to refactor features
- Clear feature ownership
- Better code splitting

---

### Dashboard Components

| Component              | Purpose                           | File                         |
| ---------------------- | --------------------------------- | ---------------------------- |
| `DashboardClient`      | Main dashboard state machine      | `dashboard-client.tsx`       |
| `MonthSelector`        | Month dropdown picker             | `month-selector.tsx`         |
| `ScoreCard`            | Large score display (0-3)         | `score-card.tsx`             |
| `MetricCard`           | Income/Core/Choice/Compound cards | `metric-card.tsx`            |
| `SpendingPieChart`     | Interactive pie chart             | `spending-pie-chart.tsx`     |
| `TransactionTable`     | Paginated transaction list        | `transaction-table.tsx`      |
| `TransactionFilters`   | Category/date/search filters      | `transaction-filters.tsx`    |
| `TransactionEditModal` | Category correction modal         | `transaction-edit-modal.tsx` |
| `ExportButtons`        | CSV/JSON export                   | `export-buttons.tsx`         |

---

### Import Components

| Component           | Purpose                           | File                      |
| ------------------- | --------------------------------- | ------------------------- |
| `ImportPageClient`  | Import workflow state machine     | `import-page-client.tsx`  |
| `FileDropzone`      | Drag-drop CSV upload              | `file-dropzone.tsx`       |
| `MonthPreviewTable` | Show detected months              | `month-preview-table.tsx` |
| `ImportOptions`     | Replace vs. merge selection       | `import-options.tsx`      |
| `ProgressPanel`     | Real-time categorization progress | `progress-panel.tsx`      |
| `ResultsSummary`    | Import completion summary         | `results-summary.tsx`     |

---

### History Components

| Component            | Purpose                                  | File                       |
| -------------------- | ---------------------------------------- | -------------------------- |
| `HistoryClient`      | History page state machine               | `history-client.tsx`       |
| `PeriodSelector`     | 6/12 month period selector               | `period-selector.tsx`      |
| `ScoreChart`         | Line chart of scores over time           | `score-chart.tsx`          |
| `BreakdownChart`     | Stacked bar chart (Core/Choice/Compound) | `breakdown-chart.tsx`      |
| `SankeyChart`        | Cash flow visualization                  | `sankey-chart.tsx`         |
| `AdvicePanel`        | Advice card display container            | `advice-panel.tsx`         |
| `AdvicePanelContent` | Advice generation & display              | `advice-panel-content.tsx` |

---

## Type System

**File:** `types/index.ts` (294 lines)

**Purpose:** Complete TypeScript types that mirror backend API responses.

### Core Types

```typescript
// Money Map enums
type MoneyMapType = 'INCOME' | 'CORE' | 'CHOICE' | 'COMPOUND' | 'EXCLUDED'
type ScoreLabel = 'Poor' | 'Need Improvement' | 'Okay' | 'Great'
type Score = 0 | 1 | 2 | 3

// Month summary
interface MonthSummary {
  id: number
  year: number
  month: number
  total_income: number
  total_core: number
  total_choice: number
  total_compound: number
  core_percentage: number
  choice_percentage: number
  compound_percentage: number
  score: Score
  score_label: ScoreLabel
  transaction_count: number
  created_at: string
  updated_at: string
}

// Transaction
interface TransactionResponse {
  id: number
  date: string
  description: string
  account: string
  amount: number
  bankin_category: string
  bankin_subcategory: string
  money_map_type: MoneyMapType
  money_map_subcategory: string
  is_manually_corrected: boolean
}
```

### API Response Types

```typescript
// Upload responses
interface UploadResponse {
  success: boolean
  total_transactions: number
  months_detected: number
  preview_by_month: Record<string, MonthSummaryResponse>
}

// Categorization responses
interface CategorizeResponse {
  success: boolean
  months_processed: MonthResult[]
  months_not_found: string[]
  total_api_calls: number
}

// Month detail
interface MonthDetailResponse {
  month: MonthSummary
  transactions: TransactionResponse[]
  pagination: {
    page: number
    page_size: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_previous: boolean
  }
}

// Advice (discriminated union)
type GetAdviceResponse =
  | { success: true; exists: false; advice: null; generated_at: null }
  | { success: true; exists: true; advice: AdviceData; generated_at: string }

interface AdviceData {
  analysis: string
  problem_areas: ProblemArea[]
  recommendations: string[]
  encouragement: string
}
```

### State Machine Types

```typescript
// Dashboard state machine
type DashboardPageState = 'loading' | 'loaded' | 'empty' | 'error'

interface DashboardState {
  pageState: DashboardPageState
  monthsList: MonthSummary[]
  selectedMonth: MonthSummary | null
  monthDetail: MonthDetailResponse | null
  currentPage: number
  error: string | null
  editingTransaction: TransactionResponse | null
  filters: TransactionFilters
}

// Discriminated union for type-safe actions
type DashboardAction =
  | { type: 'MONTHS_LOADING' }
  | { type: 'MONTHS_LOADED'; monthsList: MonthSummary[] }
  | { type: 'MONTHS_ERROR'; error: string }
  | { type: 'MONTH_SELECTED'; month: MonthSummary }
  | { type: 'MONTH_DETAIL_LOADED'; monthDetail: MonthDetailResponse }
  | { type: 'PAGE_CHANGED'; page: number }
  | { type: 'FILTERS_CHANGED'; filters: TransactionFilters }
  | { type: 'OPEN_EDIT_MODAL'; transaction: TransactionResponse }
  | { type: 'CLOSE_EDIT_MODAL' }
  | { type: 'TRANSACTION_UPDATED'; transaction: TransactionResponse; updatedMonth: MonthSummary }
```

---

## API Client

**File:** `lib/api-client.ts` (383 lines)

**Purpose:** Centralized REST client with error handling and type safety.

### Core Functions

```typescript
// Upload & Categorization
async function uploadCSV(file: File): Promise<UploadResponse>
async function categorize(
  file: File,
  monthsToProcess: string[],
  importMode: 'replace' | 'merge'
): Promise<CategorizeResponse>

// Month Data
async function getMonthsList(): Promise<MonthSummary[]>
async function getMonthDetail(
  year: number,
  month: number,
  page: number,
  pageSize: number,
  filters: TransactionFilters
): Promise<MonthDetailResponse>
async function getMonthsHistory(months: number): Promise<HistoryResponse>
async function getCashFlow(months: number): Promise<CashFlowData>

// Transactions
async function updateTransaction(
  id: number,
  payload: { money_map_type: MoneyMapType; money_map_subcategory: string }
): Promise<TransactionResponse>

// Advice
async function getAdvice(year: number, month: number): Promise<GetAdviceResponse>
async function generateAdvice(
  year: number,
  month: number,
  regenerate: boolean
): Promise<GetAdviceResponse>

// Export
async function exportMonthData(
  year: number,
  month: number,
  format: 'json' | 'csv'
): Promise<Blob>
```

### Error Handling Pattern

```typescript
// Helper: Extract error message from response
async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json()
    return data.detail || fallback
  } catch {
    return fallback
  }
}

// Example API call with error handling
export async function getMonthsList(): Promise<MonthSummary[]> {
  try {
    const response = await fetch(`${API_URL}/api/months`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const errorMsg = await extractErrorMessage(response, 'Failed to fetch months')
      throw new Error(errorMsg)
    }

    return await safeParseJson<MonthSummary[]>(response)
  } catch (error) {
    console.error('Error in getMonthsList:', error)
    throw error
  }
}
```

**Error Flow:**

1. Network errors caught and converted to user messages
2. HTTP errors checked, error message extracted from response
3. Parse errors handled gracefully with fallback
4. All errors logged to console for debugging

---

## State Management

### Pattern: useReducer + Discriminated Unions

**Why useReducer over useState:**

- Complex state transitions (5-10 different states)
- Multiple state updates that need to be atomic
- Easy to test reducers in isolation
- Clear action history for debugging

**Example: Dashboard State Machine**

**File:** `components/dashboard/dashboard-client.tsx` (488 lines)

```typescript
// Initial state
const initialState: DashboardState = {
  pageState: 'loading',
  monthsList: [],
  selectedMonth: null,
  monthDetail: null,
  currentPage: 1,
  error: null,
  editingTransaction: null,
  filters: DEFAULT_FILTERS,
}

// Reducer with discriminated union actions
function dashboardReducer(state: DashboardState, action: DashboardAction): DashboardState {
  switch (action.type) {
    case 'MONTHS_LOADING':
      return { ...state, pageState: 'loading', error: null }

    case 'MONTHS_LOADED':
      const mostRecent = action.monthsList[0]
      return {
        ...state,
        pageState: 'loaded',
        monthsList: action.monthsList,
        selectedMonth: mostRecent,
      }

    case 'MONTH_DETAIL_LOADED':
      return {
        ...state,
        pageState: 'loaded',
        monthDetail: action.monthDetail,
      }

    case 'TRANSACTION_UPDATED':
      // Optimistic UI update
      if (!state.monthDetail) return state

      const updatedTransactions = state.monthDetail.transactions.map((t) =>
        t.id === action.transaction.id ? action.transaction : t
      )

      return {
        ...state,
        monthDetail: {
          ...state.monthDetail,
          month: action.updatedMonth,
          transactions: updatedTransactions,
        },
        editingTransaction: null,
      }

    default:
      return state
  }
}

// Component usage
export default function DashboardClient() {
  const [state, dispatch] = useReducer(dashboardReducer, initialState)

  // Effect 1: Load months list on mount
  useEffect(() => {
    dispatch({ type: 'MONTHS_LOADING' })
    getMonthsList()
      .then((months) => dispatch({ type: 'MONTHS_LOADED', monthsList: months }))
      .catch((error) => dispatch({ type: 'MONTHS_ERROR', error: error.message }))
  }, [])

  // Effect 2: Load month detail when selectedMonth changes
  useEffect(() => {
    if (!state.selectedMonth) return

    getMonthDetail(state.selectedMonth.year, state.selectedMonth.month, state.currentPage, 25, state.filters)
      .then((detail) => dispatch({ type: 'MONTH_DETAIL_LOADED', monthDetail: detail }))
      .catch((error) => dispatch({ type: 'MONTHS_ERROR', error: error.message }))
  }, [state.selectedMonth, state.currentPage, state.filters])

  // ...rest of component
}
```

---

### Import Page State Machine

**File:** `components/import/import-page-client.tsx`

**State Flow:**

```text
empty
  ↓ FILE_SELECTED
uploading
  ↓ UPLOAD_SUCCESS
preview
  ↓ CATEGORIZE_START
categorizing
  ↓ CATEGORIZE_SUCCESS
results
  ↓ RESET
empty
```

**State Types:**

```typescript
type PageState = 'empty' | 'uploading' | 'preview' | 'categorizing' | 'results' | 'error'

interface ImportState {
  pageState: PageState
  file: File | null
  uploadResponse: UploadResponse | null
  selectedMonths: string[]
  importMode: 'replace' | 'merge'
  categorizeResponse: CategorizeResponse | null
  error: string | null
}

type ImportAction =
  | { type: 'FILE_SELECTED'; file: File }
  | { type: 'UPLOAD_START' }
  | { type: 'UPLOAD_SUCCESS'; response: UploadResponse }
  | { type: 'UPLOAD_ERROR'; error: string }
  | { type: 'TOGGLE_MONTH'; monthKey: string }
  | { type: 'SET_IMPORT_MODE'; mode: 'replace' | 'merge' }
  | { type: 'CATEGORIZE_START' }
  | { type: 'CATEGORIZE_SUCCESS'; response: CategorizeResponse }
  | { type: 'CATEGORIZE_ERROR'; error: string }
  | { type: 'RESET' }
```

---

## UI Component Library

### shadcn/ui Integration

**Foundation:** Radix UI + Tailwind CSS with custom styling

**Installation Pattern:**

```bash
bunx shadcn@latest add button card dialog
```

**Customization:** All components in `components/ui/` are local copies that can be customized.

### Key Components

| Component  | Usage               | Features                                             |
| ---------- | ------------------- | ---------------------------------------------------- |
| `Button`   | Actions, navigation | Variants: default, destructive, outline, ghost, link |
| `Card`     | Content containers  | Header, title, description, content, footer          |
| `Dialog`   | Modals              | Overlay, content, header, footer, close button       |
| `Select`   | Dropdowns           | Month selector, filters                              |
| `Input`    | Text fields         | Search, date inputs                                  |
| `Tooltip`  | Help text           | Hover information                                    |
| `Table`    | Data display        | Headers, rows, cells                                 |
| `Badge`    | Labels              | Category badges with colors                          |
| `Alert`    | Notifications       | Error, warning, info states                          |
| `Skeleton` | Loading states      | Placeholder animations                               |

### Example: Transaction Edit Modal

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Button } from '@/components/ui/button'

export function TransactionEditModal({ transaction, onSave, onClose }) {
  const [category, setCategory] = useState(transaction.money_map_type)

  return (
    <Dialog open={!!transaction} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Transaction</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label>Description</label>
            <p className="text-sm">{transaction.description}</p>
          </div>

          <div>
            <label>Category</label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="CORE">Core</SelectItem>
                <SelectItem value="CHOICE">Choice</SelectItem>
                <SelectItem value="COMPOUND">Compound</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={() => onSave(transaction.id, category)}>
              Save
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

---

## Chart Implementations

All charts use **Recharts** (React-native charting library).

### Spending Pie Chart

**File:** `components/dashboard/spending-pie-chart.tsx` (249 lines)

**Type:** Donut/ring pie chart

**Features:**

- Category selector dropdown to highlight segments
- Custom active shape with highlighting
- Center label showing percentage and category name
- Responsive sizing (max-w-[280px])
- Empty state handling

**Code Structure:**

```tsx
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

export function SpendingPieChart({ month }: { month: MonthSummary }) {
  const [activeCategory, setActiveCategory] = useState<'CORE' | 'CHOICE' | 'COMPOUND'>('CORE')

  const data = [
    { name: 'CORE', value: month.total_core, color: CATEGORY_COLORS.CORE },
    { name: 'CHOICE', value: month.total_choice, color: CATEGORY_COLORS.CHOICE },
    { name: 'COMPOUND', value: month.total_compound, color: CATEGORY_COLORS.COMPOUND },
  ]

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={85}
          dataKey="value"
          activeIndex={data.findIndex((item) => item.name === activeCategory)}
          activeShape={renderActiveShape}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  )
}
```

---

### Score Line Chart

**File:** `components/history/score-chart.tsx`

**Type:** Line chart with scatter plots

**Features:**

- Monthly scores (0-3) plotted over 12 months
- Dynamic color-coded dots (red → orange → yellow → green)
- Score icons on each point (XCircle, AlertTriangle, Target, Trophy)
- CartesianGrid with custom tooltip
- Y-axis range: 0-3

**Code Structure:**

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter } from 'recharts'

export function ScoreChart({ months }: { months: MonthHistory[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={months}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month_label" />
        <YAxis domain={[0, 3]} ticks={[0, 1, 2, 3]} />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#8884d8"
          strokeWidth={2}
          dot={<CustomDot />}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function CustomDot({ cx, cy, payload }) {
  const Icon = getIconForScore(payload.score)
  const color = getColorForScore(payload.score)

  return <Icon x={cx - 12} y={cy - 12} width={24} height={24} fill={color} />
}
```

---

### Sankey Diagram (Complex)

**File:** `components/history/sankey-chart.tsx` (449 lines)

**Type:** Cash flow Sankey diagram

**Purpose:** Visualize money flow from Income → Categories → Subcategories

**Architecture:**

1. **Data Transformation:**

```typescript
function transformToSankeyData(data: CashFlowData): SankeyDataOutput | null {
  const nodes: SankeyNode[] = []
  const links: SankeyLink[] = []

  // Layer 0: Income (source)
  nodes.push({ name: 'Income' })

  // Layer 1: Categories (Core, Choice, Compound, Deficit)
  nodes.push({ name: 'Core' }, { name: 'Choice' }, { name: 'Compound' })

  // Layer 2: Subcategories
  data.core_breakdown.forEach((item) => {
    nodes.push({ name: item.subcategory })
    links.push({
      source: nodes.findIndex((n) => n.name === 'Core'),
      target: nodes.findIndex((n) => n.name === item.subcategory),
      value: item.amount,
    })
  })

  // Links: Income → Categories
  links.push(
    { source: 0, target: 1, value: data.core_total },
    { source: 0, target: 2, value: data.choice_total },
    { source: 0, target: 3, value: data.compound_total }
  )

  return { nodes, links }
}
```

2. **Dynamic Height Calculation:**

```typescript
function calculateChartHeight(data: CashFlowData): number {
  const subcategoryCount =
    data.core_breakdown.length +
    data.choice_breakdown.length +
    data.compound_breakdown.length

  // Base 300px + 28px per subcategory beyond 8, max 600px
  return Math.min(300 + Math.max(0, subcategoryCount - 8) * 28, 600)
}
```

3. **Custom Renderers:**

```tsx
function CustomNode({ x, y, width, height, index, payload }) {
  const isCategory = index > 0 && index <= 3 // Core, Choice, Compound, Deficit
  const isIncome = index === 0

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={getColor(payload.name)} />
      <text
        x={isCategory ? x + width / 2 : x + width + 10}
        y={y + height / 2}
        textAnchor={isCategory ? 'middle' : 'start'}
        fill={isCategory ? '#fff' : '#000'}
      >
        {payload.name}
      </text>
    </g>
  )
}

function CustomLink({ sourceX, targetX, sourceY, targetY, sourceControlX, targetControlX, linkWidth, index, payload }) {
  const color = getCategoryColor(payload.source) // Color by source category

  return (
    <path
      d={`M${sourceX},${sourceY} C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}`}
      stroke={color}
      strokeWidth={linkWidth}
      fill="none"
      opacity={0.5}
    />
  )
}
```

**Features:**

- Defensive null checks (returns empty `<g />` when needed)
- Error boundary wrapper
- Responsive container
- French labels for categories/subcategories

---

## Theming & Dark Mode

**File:** `components/ui/theme-provider.tsx` (70 lines)

**Pattern:** `useSyncExternalStore` for hydration-safe theme management

### Implementation

```tsx
import { useSyncExternalStore } from 'react'

type Theme = 'light' | 'dark' | 'system'

class ThemeStore {
  private listeners = new Set<() => void>()
  private theme: Theme = 'system'

  subscribe(listener: () => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  getSnapshot() {
    return this.theme
  }

  setTheme(newTheme: Theme) {
    this.theme = newTheme
    localStorage.setItem('theme', newTheme)
    this.updateDOM()
    this.listeners.forEach((listener) => listener())
  }

  private updateDOM() {
    const isDark = this.theme === 'dark' || (this.theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
}

const themeStore = new ThemeStore()

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSyncExternalStore(
    themeStore.subscribe.bind(themeStore),
    themeStore.getSnapshot.bind(themeStore),
    () => 'system' // Server snapshot
  )

  useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored) {
      themeStore.setTheme(stored)
    }
  }, [])

  return <ThemeContext.Provider value={{ theme, setTheme: themeStore.setTheme }}>{children}</ThemeContext.Provider>
}
```

**Benefits:**

- No hydration mismatches (server always renders 'system')
- Persists to localStorage
- Respects system preference
- Instant theme switching

---

## Internationalization

**File:** `lib/translations.ts` (150+ lines)

**Approach:** Single centralized object with French translations

**Structure:**

```typescript
export const t = {
  nav: {
    dashboard: 'Tableau de bord',
    import: 'Importer',
    history: 'Historique',
    advice: 'Conseils',
  },
  categories: {
    INCOME: 'Revenus',
    CORE: 'Essentiel',
    CHOICE: 'Choix',
    COMPOUND: 'Épargne',
    EXCLUDED: 'Exclus',
  },
  subcategories: {
    Job: 'Salaire',
    Housing: 'Logement',
    Groceries: 'Courses',
    Utilities: 'Factures',
    // ... 25+ subcategories
  },
  dashboard: {
    title: 'Tableau de bord Money Map',
    subtitle: 'Vue mensuelle de vos finances',
    empty: 'Aucune donnée disponible. Importez vos transactions pour commencer.',
    // ...
  },
  // ... more sections
}
```

**Usage:**

```tsx
import { t } from '@/lib/translations'

function Dashboard() {
  return (
    <div>
      <h1>{t.dashboard.title}</h1>
      <p>{t.dashboard.subtitle}</p>
    </div>
  )
}
```

**Future Enhancement:** Replace with i18next for multi-language support.

---

## Performance Optimizations

### Applied Optimizations

1. **useMemo for Heavy Calculations:**

```tsx
const chartData = useMemo(() => {
  return transformToSankeyData(cashFlowData)
}, [cashFlowData])
```

2. **useCallback for Event Handlers:**

```tsx
const handleMonthChange = useCallback((month: MonthSummary) => {
  dispatch({ type: 'MONTH_SELECTED', month })
}, [])
```

3. **Pagination:**

- 25 transactions per page (limits DOM nodes)
- Server-side pagination (reduces data transfer)

4. **Lazy Chart Rendering:**

```tsx
{chartData ? <SankeyChart data={chartData} /> : <EmptyState />}
```

5. **Responsive Breakpoints:**

```tsx
<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
  {/* Mobile: 1 column, Desktop: 2 columns */}
</div>
```

6. **Code Splitting:**

- Automatic via Next.js App Router (per-page bundles)
- Dynamic imports for heavy components (if needed)

7. **Image/Icon Optimization:**

- Lucide React for tree-shakeable icons
- SVG logos (scalable, no HTTP requests)

---

## Best Practices

### Client vs. Server Components

**Default:** Server components (no `'use client'`)

**Use `'use client'` only when:**

- Component uses React hooks (`useState`, `useEffect`, `useReducer`)
- Component handles user interactions (onClick, onChange)
- Component uses browser APIs (localStorage, window)
- Component uses client-only libraries (Recharts)

**Examples:**

```tsx
// ✅ Server component (default)
export default function Page() {
  return <DashboardClient />
}

// ✅ Client component (needs state)
'use client'

export function DashboardClient() {
  const [state, dispatch] = useReducer(...)
  // ...
}
```

---

### Error Handling

**Pattern:** Error boundaries + graceful degradation

```tsx
import { ErrorBoundary } from '@/components/ui/error-boundary'

export function Page() {
  return (
    <ErrorBoundary fallback={<ErrorFallback />}>
      <DashboardClient />
    </ErrorBoundary>
  )
}
```

---

### Loading States

**Pattern:** Skeleton components that match final layout

```tsx
function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    </div>
  )
}
```

---

## Next Steps

- **[Backend Architecture](./backend-architecture.md)**: Understand the FastAPI backend
- **[API Reference](./api-reference.md)**: Complete API endpoint documentation

---

**Questions?** Check the [Product Mission](../product/mission.md) or [Tech Stack](../product/tech-stack.md) for context.
