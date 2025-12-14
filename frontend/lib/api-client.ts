import type {
  CashFlowResponse,
  CategorizeResponse,
  GenerateAdviceResponse,
  GetAdviceResponse,
  HistoryResponse,
  ImportMode,
  MonthDetailResponse,
  MonthsListResponse,
  TransactionFilters,
  UpdateTransactionPayload,
  UpdateTransactionResponse,
  UploadResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// [>]: Safely parse JSON from response, with user-friendly error on failure.
async function safeParseJson<T>(response: Response): Promise<T> {
  try {
    return await response.json();
  } catch (parseError) {
    console.error(
      `[safeParseJson] Failed to parse response from ${response.url}:`,
      parseError,
    );
    throw new Error("Server returned an invalid response. Please try again.");
  }
}

// [>]: Extract error message from response, handling non-JSON responses gracefully.
async function extractErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const error = await response.json();
    return error.detail || fallback;
  } catch (parseError) {
    // [!]: Log JSON parse failure for debugging.
    console.error(
      `Failed to parse error response as JSON from ${response.url}:`,
      parseError,
    );
    return response.statusText || fallback;
  }
}

export async function uploadCSV(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
    });
  } catch (networkError) {
    console.error("Network error during CSV upload:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to upload file",
    );
    console.error(`Upload failed with status ${response.status}: ${message}`);
    throw new Error(message);
  }

  return safeParseJson<UploadResponse>(response);
}

export async function categorize(
  file: File,
  months: string[],
  importMode: ImportMode,
): Promise<CategorizeResponse> {
  // [>]: Validate months before making API call.
  if (months.length === 0) {
    throw new Error(
      "No months selected. Please select at least one month from the preview table before categorizing.",
    );
  }

  const formData = new FormData();
  formData.append("file", file);

  const url = new URL(`${API_BASE}/api/categorize`);
  url.searchParams.set("months_to_process", months.join(","));
  url.searchParams.set("import_mode", importMode);

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      method: "POST",
      body: formData,
    });
  } catch (networkError) {
    console.error("Network error during categorization:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to categorize transactions",
    );
    console.error(
      `Categorization failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<CategorizeResponse>(response);
}

export async function getMonthsList(): Promise<MonthsListResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/months`);
  } catch (networkError) {
    console.error("Network error fetching months list:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to load months",
    );
    console.error(
      `Months list failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<MonthsListResponse>(response);
}

export async function getMonthDetail(
  year: number,
  month: number,
  page: number = 1,
  pageSize: number = 50,
  filters?: TransactionFilters,
): Promise<MonthDetailResponse> {
  const url = new URL(`${API_BASE}/api/months/${year}/${month}`);
  url.searchParams.set("page", page.toString());
  url.searchParams.set("page_size", pageSize.toString());

  // [>]: Add filter parameters if provided.
  if (filters?.categoryTypes.length) {
    url.searchParams.set("category", filters.categoryTypes.join(","));
  }
  if (filters?.dateFrom) {
    url.searchParams.set("start_date", filters.dateFrom);
  }
  if (filters?.dateTo) {
    url.searchParams.set("end_date", filters.dateTo);
  }
  if (filters?.searchQuery.trim()) {
    url.searchParams.set("search", filters.searchQuery.trim());
  }

  let response: Response;
  try {
    response = await fetch(url.toString());
  } catch (networkError) {
    console.error("Network error fetching month detail:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to load month data",
    );
    console.error(
      `Month detail failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<MonthDetailResponse>(response);
}

export async function updateTransaction(
  transactionId: number,
  payload: UpdateTransactionPayload,
): Promise<UpdateTransactionResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/transactions/${transactionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (networkError) {
    console.error("Network error updating transaction:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to update transaction",
    );
    console.error(
      `Transaction update failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<UpdateTransactionResponse>(response);
}

export async function getMonthsHistory(
  months: number = 12,
): Promise<HistoryResponse> {
  const url = new URL(`${API_BASE}/api/months/history`);
  url.searchParams.set("months", months.toString());

  let response: Response;
  try {
    response = await fetch(url.toString());
  } catch (networkError) {
    console.error("Network error fetching months history:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to load history data",
    );
    console.error(
      `Months history failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<HistoryResponse>(response);
}

export async function getCashFlow(
  months: number = 12,
): Promise<CashFlowResponse> {
  const url = new URL(`${API_BASE}/api/months/cashflow`);
  url.searchParams.set("months", months.toString());

  let response: Response;
  try {
    response = await fetch(url.toString());
  } catch (networkError) {
    console.error("Network error fetching cashflow data:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to load cashflow data",
    );
    console.error(
      `Cashflow fetch failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<CashFlowResponse>(response);
}

export async function getAdvice(
  year: number,
  month: number,
): Promise<GetAdviceResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/advice/${year}/${month}`);
  } catch (networkError) {
    console.error("Network error fetching advice:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to load advice",
    );
    console.error(
      `Get advice failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<GetAdviceResponse>(response);
}

export async function generateAdvice(
  year: number,
  month: number,
  regenerate: boolean = false,
): Promise<GenerateAdviceResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/advice/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ year, month, regenerate }),
    });
  } catch (networkError) {
    console.error("Network error generating advice:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(
      response,
      "Failed to generate advice",
    );
    console.error(
      `Generate advice failed with status ${response.status}: ${message}`,
    );
    throw new Error(message);
  }

  return safeParseJson<GenerateAdviceResponse>(response);
}

export type ExportFormat = "json" | "csv";

export async function exportMonthData(
  year: number,
  month: number,
  format: ExportFormat,
): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE}/api/months/${year}/${month}/export/${format}`,
    );
  } catch (networkError) {
    console.error("Network error during export:", networkError);
    throw new Error(
      "Unable to connect to server. Please check your network connection.",
    );
  }

  if (!response.ok) {
    const message = await extractErrorMessage(response, "Export failed");
    console.error(`Export failed with status ${response.status}: ${message}`);
    throw new Error(message);
  }

  try {
    return await response.blob();
  } catch (blobError) {
    console.error("Failed to process export response as blob:", blobError);
    throw new Error("Failed to download export file. Please try again.");
  }
}
