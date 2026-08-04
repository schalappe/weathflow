/** @module api-client Typed backend HTTP boundary. */

import type {
  ActivePriorityInput,
  ActivePriorityResponse,
  CommitmentContextResponse,
  CommitmentFactInput,
  CommitmentFactResponse,
  ConstraintContextResponse,
  ConstraintFactInput,
  ConstraintFactResponse,
  EmergencyFundContextResponse,
  EmergencyFundFactInput,
  EmergencyFundFactResponse,
  EmergencyFundFactType,
  IncomeContextResponse,
  IncomeFactInput,
  IncomeFactResponse,
  IncomeFactType,
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

// [>]: Backend limits page_size to 100, so we use this for bulk fetching.
const MAX_PAGE_SIZE = 100;

/**
 * Fetches all transactions for a month by paginating through all pages.
 * Used by GroupedTransactionList which needs all transactions for grouping.
 */
export async function getMonthDetailAllTransactions(
  year: number,
  month: number,
): Promise<MonthDetailResponse> {
  // [>]: First fetch to get total count and first batch.
  const firstPage = await getMonthDetail(year, month, 1, MAX_PAGE_SIZE);

  // [>]: If all transactions fit in first page, return directly.
  if (firstPage.pagination.total_pages <= 1) {
    return firstPage;
  }

  // [>]: Fetch remaining pages in parallel.
  const remainingPages = Array.from(
    { length: firstPage.pagination.total_pages - 1 },
    (_, i) => i + 2,
  );

  const additionalResponses = await Promise.all(
    remainingPages.map((page) =>
      getMonthDetail(year, month, page, MAX_PAGE_SIZE),
    ),
  );

  // [>]: Combine all transactions.
  const allTransactions = [
    ...firstPage.transactions,
    ...additionalResponses.flatMap((r) => r.transactions),
  ];

  return {
    month: firstPage.month,
    transactions: allTransactions,
    pagination: {
      page: 1,
      page_size: allTransactions.length,
      total_items: allTransactions.length,
      total_pages: 1,
    },
  };
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

/**
 * Load declared active priority.
 * @returns Priority lifecycle data, or null.
 * @throws Network or API failure.
 */
export async function getActivePriority(): Promise<ActivePriorityResponse> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/active-priority`,
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to load active priority"),
    );
  }
  return safeParseJson<ActivePriorityResponse>(response);
}

/**
 * Create or correct active priority.
 * @param priority - Explicit goal, target, and optional deadline.
 * @returns Updated lifecycle data.
 * @throws Network or API failure.
 */
export async function putActivePriority(
  priority: ActivePriorityInput,
): Promise<ActivePriorityResponse> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/active-priority`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(priority),
    },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to save active priority"),
    );
  }
  return safeParseJson<ActivePriorityResponse>(response);
}

/**
 * Delete active priority.
 * @returns Completion.
 * @throws Network or API failure.
 */
export async function deleteActivePriority(): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/active-priority`,
    {
      method: "DELETE",
    },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to delete active priority"),
    );
  }
}

/**
 * Load emergency-fund facts.
 * @returns Stored facts, including expired values.
 * @throws Network or API failure.
 */
export async function getEmergencyFundContext(): Promise<EmergencyFundContextResponse> {
  const response = await fetch(`${API_BASE}/api/advice/context/emergency-fund`);
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(
        response,
        "Failed to load emergency-fund context",
      ),
    );
  }
  return safeParseJson<EmergencyFundContextResponse>(response);
}

/**
 * Create, correct, or reconfirm emergency-fund amount.
 * @param factType - Closed-catalog amount type.
 * @param amount - Declared euro amount.
 * @returns Updated lifecycle data.
 * @throws Network or API failure.
 */
export async function putEmergencyFundFact(
  factType: EmergencyFundFactType,
  amount: number,
): Promise<EmergencyFundFactResponse> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/emergency-fund/${factType}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount }),
    },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to save emergency-fund fact"),
    );
  }
  return safeParseJson<EmergencyFundFactResponse>(response);
}

/**
 * Delete emergency-fund amount.
 * @param factType - Closed-catalog amount type.
 * @returns Completion.
 * @throws Network or API failure.
 */
export async function deleteEmergencyFundFact(
  factType: EmergencyFundFactType,
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/emergency-fund/${factType}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(
        response,
        "Failed to delete emergency-fund fact",
      ),
    );
  }
}

/**
 * Load declared income facts.
 * @returns Stored facts, including expired values.
 * @throws Network or API failure.
 */
export async function getIncomeContext(): Promise<IncomeContextResponse> {
  const response = await fetch(`${API_BASE}/api/advice/context/income`);
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to load income context"),
    );
  }
  return safeParseJson<IncomeContextResponse>(response);
}

/**
 * Create, correct, or reconfirm income.
 * @param fact - Habitual or dated expected income.
 * @returns Updated lifecycle data.
 * @throws Network or API failure.
 */
export async function putIncomeFact(
  fact: IncomeFactInput,
): Promise<IncomeFactResponse> {
  const response = await fetch(`${API_BASE}/api/advice/context/income`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fact),
  });
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to save income fact"),
    );
  }
  return safeParseJson<IncomeFactResponse>(response);
}

/**
 * Delete declared income.
 * @param factType - Income fact key.
 * @returns Completion.
 * @throws Network or API failure.
 */
export async function deleteIncomeFact(
  factType: IncomeFactType,
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/income/${factType}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to delete income fact"),
    );
  }
}

/**
 * Fetch obligations and debt facts.
 * @returns Stored facts, including expired values.
 * @throws Network or API failure.
 */
export async function getCommitmentContext(): Promise<CommitmentContextResponse> {
  const response = await fetch(`${API_BASE}/api/advice/context/commitments`);
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to load commitments"),
    );
  }
  return safeParseJson<CommitmentContextResponse>(response);
}

/**
 * Correct or reconfirm obligation or debt fact.
 * @param factId - Stored fact id.
 * @param fact - Replacement value.
 * @returns Updated lifecycle data.
 * @throws Network or API failure.
 */
export async function putCommitmentFact(
  factId: number,
  fact: CommitmentFactInput,
): Promise<CommitmentFactResponse> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/commitments/${factId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fact),
    },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to save commitment"),
    );
  }
  return safeParseJson<CommitmentFactResponse>(response);
}

/**
 * Delete obligation or debt fact.
 * @param factId - Stored fact id.
 * @returns Completion.
 * @throws Network or API failure.
 */
export async function deleteCommitmentFact(factId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/commitments/${factId}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to delete commitment"),
    );
  }
}

/**
 * Load declared decision constraints.
 * @returns Stored constraints, including expired values.
 * @throws Network or API failure.
 */
export async function getConstraintContext(): Promise<ConstraintContextResponse> {
  const response = await fetch(`${API_BASE}/api/advice/context/constraints`);
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to load constraints"),
    );
  }
  return safeParseJson<ConstraintContextResponse>(response);
}

/**
 * Correct or reconfirm decision constraint.
 * @param factId - Stored constraint id.
 * @param fact - Replacement fields.
 * @returns Updated constraint.
 * @throws Network or API failure.
 */
export async function putConstraintFact(
  factId: number,
  fact: ConstraintFactInput,
): Promise<ConstraintFactResponse> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/constraints/${factId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fact),
    },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to update constraint"),
    );
  }
  return safeParseJson<ConstraintFactResponse>(response);
}

/**
 * Delete decision constraint.
 * @param factId - Stored constraint id.
 * @returns Completion.
 * @throws Network or API failure.
 */
export async function deleteConstraintFact(factId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/advice/context/constraints/${factId}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response, "Failed to delete constraint"),
    );
  }
}

/**
 * Generate advice with optional clarification answer.
 * @param year - Advice year.
 * @param month - Advice month.
 * @param options - Regeneration and active-priority answer.
 * @returns Current decision outputs.
 * @throws Network or API failure.
 */

export async function generateAdvice(
  year: number,
  month: number,
  options: {
    regenerate?: boolean;
    activePriority?: ActivePriorityInput;
    rememberPriority?: boolean;
    emergencyFundFact?: EmergencyFundFactInput;
    commitmentFact?: CommitmentFactInput;
    incomeFact?: IncomeFactInput;
    constraintFact?: ConstraintFactInput;
    rememberFact?: boolean;
    clarificationAction?: "skip" | "unknown";
  } = {},
): Promise<GenerateAdviceResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/advice/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        year,
        month,
        regenerate: options.regenerate ?? false,
        active_priority: options.activePriority,
        remember_priority: options.rememberPriority ?? true,
        emergency_fund_fact: options.emergencyFundFact,
        commitment_fact: options.commitmentFact,
        income_fact: options.incomeFact,
        constraint_fact: options.constraintFact,
        remember_fact:
          options.emergencyFundFact === undefined &&
          options.commitmentFact === undefined &&
          options.incomeFact === undefined &&
          options.constraintFact === undefined
            ? undefined
            : (options.rememberFact ?? true),
        clarification_action: options.clarificationAction,
      }),
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
