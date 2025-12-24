// [>]: Backend API response types - mirroring backend/app/responses/upload.py.

export interface TransactionPreview {
  date: string;
  description: string;
  amount: number;
}

export interface MonthSummaryResponse {
  year: number;
  month: number;
  transaction_count: number;
  total_income: number;
  total_expenses: number;
}

export interface UploadResponse {
  success: boolean;
  total_transactions: number;
  months_detected: MonthSummaryResponse[];
  preview_by_month: Record<string, TransactionPreview[]>;
}

export type ScoreLabel = "Poor" | "Need Improvement" | "Okay" | "Great";

export interface MonthResult {
  year: number;
  month: number;
  transactions_categorized: number;
  transactions_skipped: number;
  low_confidence_count: number;
  score: number;
  score_label: ScoreLabel;
}

export interface CategorizeResponse {
  success: boolean;
  months_processed: MonthResult[];
  months_not_found: string[];
  total_api_calls: number;
}

// [>]: Frontend state types for the import page state machine.

export type PageState =
  | "empty"
  | "uploading"
  | "preview"
  | "categorizing"
  | "results"
  | "error";

export type ImportMode = "replace" | "merge";

export interface ImportState {
  pageState: PageState;
  file: File | null;
  uploadResponse: UploadResponse | null;
  selectedMonths: Set<string>;
  importMode: ImportMode;
  categorizeResponse: CategorizeResponse | null;
  error: string | null;
}

// [>]: Discriminated union for type-safe reducer actions.

export type ImportAction =
  | { type: "FILE_SELECTED"; payload: File }
  | { type: "FILE_VALIDATION_ERROR"; payload: string }
  | { type: "UPLOAD_START" }
  | { type: "UPLOAD_SUCCESS"; payload: UploadResponse }
  | { type: "UPLOAD_ERROR"; payload: string }
  | { type: "TOGGLE_MONTH"; payload: string }
  | { type: "SELECT_ALL_MONTHS" }
  | { type: "DESELECT_ALL_MONTHS" }
  | { type: "SET_IMPORT_MODE"; payload: ImportMode }
  | { type: "CATEGORIZE_START" }
  | { type: "CATEGORIZE_SUCCESS"; payload: CategorizeResponse }
  | { type: "CATEGORIZE_ERROR"; payload: string }
  | { type: "RESET" };

// [>]: Dashboard API response types - mirroring backend/app/responses/months.py.

export type MoneyMapType =
  | "INCOME"
  | "CORE"
  | "CHOICE"
  | "COMPOUND"
  | "EXCLUDED";

// [>]: Transaction filter state for dashboard filtering.
export interface TransactionFilters {
  categoryTypes: MoneyMapType[];
  dateFrom: string | null;
  dateTo: string | null;
  searchQuery: string;
}

// [>]: Default empty filters constant.
export const DEFAULT_FILTERS: TransactionFilters = {
  categoryTypes: [],
  dateFrom: null,
  dateTo: null,
  searchQuery: "",
};

export interface MonthSummary {
  id: number;
  year: number;
  month: number;
  total_income: number;
  total_core: number;
  total_choice: number;
  total_compound: number;
  core_percentage: number;
  choice_percentage: number;
  compound_percentage: number;
  score: number;
  score_label: ScoreLabel | null;
  transaction_count: number;
  created_at: string;
  updated_at: string;
}

export interface TransactionResponse {
  id: number;
  date: string;
  description: string;
  account: string | null;
  amount: number;
  bankin_category: string | null;
  bankin_subcategory: string | null;
  money_map_type: MoneyMapType | null;
  money_map_subcategory: string | null;
  is_manually_corrected: boolean;
}

export interface PaginationInfo {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface MonthsListResponse {
  months: MonthSummary[];
  total: number;
}

export interface MonthDetailResponse {
  month: MonthSummary;
  transactions: TransactionResponse[];
  pagination: PaginationInfo;
}

// [>]: Dashboard state types for reducer pattern.

export type DashboardPageState = "loading" | "loaded" | "empty" | "error";

export interface DashboardState {
  pageState: DashboardPageState;
  monthsList: MonthSummary[];
  selectedMonth: { year: number; month: number } | null;
  monthDetail: MonthDetailResponse | null;
  currentPage: number;
  error: string | null;
  editingTransaction: TransactionResponse | null;
  filters: TransactionFilters;
}

export type DashboardAction =
  | { type: "LOAD_START" }
  | { type: "MONTHS_LOADED"; payload: MonthSummary[] }
  | { type: "MONTH_DETAIL_LOADED"; payload: MonthDetailResponse }
  | { type: "SELECT_MONTH"; payload: { year: number; month: number } }
  | { type: "SET_PAGE"; payload: number }
  | { type: "SET_FILTERS"; payload: TransactionFilters }
  | { type: "LOAD_ERROR"; payload: string }
  | { type: "RETRY" }
  | { type: "OPEN_EDIT_MODAL"; payload: TransactionResponse }
  | { type: "CLOSE_EDIT_MODAL" }
  | { type: "TRANSACTION_UPDATED"; payload: UpdateTransactionResponse };

// [>]: Transaction update API types - mirroring backend/app/responses/transactions.py.

export interface UpdateTransactionPayload {
  money_map_type: MoneyMapType;
  money_map_subcategory: string | null;
}

export interface UpdateTransactionResponse {
  success: boolean;
  transaction: TransactionResponse;
  updated_month_stats: MonthSummary;
}

// [>]: Historical data API response types - mirroring backend/app/responses/history.py.

export type ScoreTrend = "improving" | "declining" | "stable";

// [>]: Score value constrained to 0-3 matching backend Field(ge=0, le=3).
export type Score = 0 | 1 | 2 | 3;

export interface MonthHistory {
  year: number;
  month: number;
  total_income: number;
  total_core: number;
  total_choice: number;
  total_compound: number;
  core_percentage: number;
  choice_percentage: number;
  compound_percentage: number;
  score: Score;
  score_label: ScoreLabel | null;
  month_label: string;
}

export interface MonthReference {
  year: number;
  month: number;
  score: Score;
}

export interface HistorySummary {
  total_months: number;
  average_score: number;
  score_trend: ScoreTrend;
  best_month: MonthReference | null;
  worst_month: MonthReference | null;
}

export interface HistoryResponse {
  months: MonthHistory[];
  summary: HistorySummary;
}

// [>]: Advice API response types based on backend/app/responses/advice.py.
// [>]: Uses discriminated union for type-safe null handling (safer than backend's optional fields).

export interface ProblemArea {
  category: string;
  amount: number;
  trend: string;
}

export interface AdviceData {
  analysis: string;
  problem_areas: ProblemArea[];
  recommendations: string[];
  encouragement: string;
}

// [>]: Eligibility info provided by backend to control UI behavior.
export interface EligibilityInfo {
  can_generate: boolean;
  is_first_advice: boolean;
  reason: string | null;
}

// [>]: Discriminated union for type-safe advice response handling.
// When exists=true, advice and generated_at are guaranteed non-null.
export type GetAdviceResponse =
  | {
      success: boolean;
      exists: false;
      advice: null;
      generated_at: null;
      eligibility: EligibilityInfo;
    }
  | {
      success: boolean;
      exists: true;
      advice: AdviceData;
      generated_at: string;
      eligibility: EligibilityInfo;
    };

export interface GenerateAdviceResponse {
  success: boolean;
  advice: AdviceData;
  generated_at: string;
  was_cached: boolean;
}

// [>]: Cash flow API response types for Sankey diagram visualization.

export interface CategoryBreakdown {
  subcategory: string;
  amount: number;
}

export interface CashFlowData {
  income_total: number;
  core_total: number;
  choice_total: number;
  compound_total: number;
  deficit: number;
  core_breakdown: CategoryBreakdown[];
  choice_breakdown: CategoryBreakdown[];
  compound_breakdown: CategoryBreakdown[];
}

export interface CashFlowResponse {
  data: CashFlowData;
  period_months: number;
}
