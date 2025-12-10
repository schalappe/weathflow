import type {
  CategorizeResponse,
  ImportMode,
  MonthDetailResponse,
  MonthsListResponse,
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
): Promise<MonthDetailResponse> {
  const url = new URL(`${API_BASE}/api/months/${year}/${month}`);
  url.searchParams.set("page", page.toString());
  url.searchParams.set("page_size", pageSize.toString());

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
