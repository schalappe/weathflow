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
  low_confidence_count: number;
  score: number;
  score_label: ScoreLabel;
  // [>]: Percentages come from backend MonthStats calculation.
  core_percentage?: number;
  choice_percentage?: number;
  compound_percentage?: number;
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
