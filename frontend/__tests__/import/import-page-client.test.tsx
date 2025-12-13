import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ImportPageClient } from "@/components/import/import-page-client";
import * as apiClient from "@/lib/api-client";
import { useRouter } from "next/navigation";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  uploadCSV: vi.fn(),
  categorize: vi.fn(),
}));

// [>]: Get mocked router for assertions.
vi.mock("next/navigation");

const mockUploadResponse = {
  success: true,
  total_transactions: 165,
  months_detected: [
    {
      year: 2025,
      month: 1,
      transaction_count: 89,
      total_income: 1429,
      total_expenses: 901,
    },
    {
      year: 2025,
      month: 2,
      transaction_count: 76,
      total_income: 0,
      total_expenses: 456,
    },
  ],
  preview_by_month: {},
};

const mockCategorizeResponse = {
  success: true,
  months_processed: [
    {
      year: 2025,
      month: 1,
      transactions_categorized: 89,
      transactions_skipped: 0,
      low_confidence_count: 3,
      score: 3,
      score_label: "Great" as const,
    },
  ],
  months_not_found: [],
  total_api_calls: 2,
};

describe("ImportPageClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("file upload triggers API call and shows preview state", async () => {
    vi.mocked(apiClient.uploadCSV).mockResolvedValue(mockUploadResponse);

    render(<ImportPageClient />);

    // [>]: Initially shows dropzone.
    expect(
      screen.getByText(/Glissez votre fichier CSV ici/i),
    ).toBeInTheDocument();

    // [>]: Simulate file upload.
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    // [>]: Wait for API call and state transition.
    await waitFor(() => {
      expect(apiClient.uploadCSV).toHaveBeenCalledWith(csvFile);
    });

    // [>]: Should show preview state with months.
    await waitFor(() => {
      expect(screen.getByText("janvier 2025")).toBeInTheDocument();
    });
  });

  it("categorize button triggers API call and shows results state", async () => {
    vi.mocked(apiClient.uploadCSV).mockResolvedValue(mockUploadResponse);
    vi.mocked(apiClient.categorize).mockResolvedValue(mockCategorizeResponse);

    render(<ImportPageClient />);

    // [>]: Upload file first.
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    // [>]: Wait for preview state.
    await waitFor(() => {
      expect(screen.getByText("janvier 2025")).toBeInTheDocument();
    });

    // [>]: Click categorize button.
    const categorizeButton = screen.getByRole("button", {
      name: /Catégoriser avec l'IA/i,
    });
    fireEvent.click(categorizeButton);

    // [>]: Wait for results.
    await waitFor(() => {
      expect(screen.getByText(/Import terminé/i)).toBeInTheDocument();
    });
  });

  it("error state displays Alert with retry option", async () => {
    vi.mocked(apiClient.uploadCSV).mockRejectedValue(
      new Error("Network error"),
    );

    render(<ImportPageClient />);

    // [>]: Upload file.
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    // [>]: Error shows in both Alert and FileDropzone, use getAllByText.
    await waitFor(() => {
      expect(screen.getAllByText(/network error/i).length).toBeGreaterThan(0);
    });

    // [>]: Should show Réessayer button.
    expect(
      screen.getByRole("button", { name: /Réessayer/i }),
    ).toBeInTheDocument();
  });

  it("state transitions follow correct flow", async () => {
    const mockPush = vi.fn();
    vi.mocked(useRouter).mockReturnValue({
      push: mockPush,
      replace: vi.fn(),
      refresh: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      prefetch: vi.fn(),
    });
    vi.mocked(apiClient.uploadCSV).mockResolvedValue(mockUploadResponse);
    vi.mocked(apiClient.categorize).mockResolvedValue(mockCategorizeResponse);

    render(<ImportPageClient />);

    // [>]: Initial: empty state - dropzone visible.
    expect(
      screen.getByText(/Glissez votre fichier CSV ici/i),
    ).toBeInTheDocument();

    // [>]: Upload file -> uploading -> preview.
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    // [>]: Preview state - months table visible.
    await waitFor(() => {
      expect(screen.getByText("janvier 2025")).toBeInTheDocument();
    });

    // [>]: Click categorize -> categorizing -> results.
    fireEvent.click(
      screen.getByRole("button", { name: /Catégoriser avec l'IA/i }),
    );

    // [>]: Results state - success message visible.
    await waitFor(() => {
      expect(screen.getByText(/Import terminé/i)).toBeInTheDocument();
    });

    // [>]: Click finish -> navigates to homepage.
    fireEvent.click(screen.getByRole("button", { name: /Terminer l'import/i }));

    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("categorization API error displays error with retry option", async () => {
    vi.mocked(apiClient.uploadCSV).mockResolvedValue(mockUploadResponse);
    vi.mocked(apiClient.categorize).mockRejectedValue(
      new Error("Claude API rate limit exceeded"),
    );

    render(<ImportPageClient />);

    // [>]: Upload file first.
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    // [>]: Wait for preview state.
    await waitFor(() => {
      expect(screen.getByText("janvier 2025")).toBeInTheDocument();
    });

    // [>]: Click categorize button.
    fireEvent.click(
      screen.getByRole("button", { name: /Catégoriser avec l'IA/i }),
    );

    // [>]: Error shows in both Alert and FileDropzone, use getAllByText.
    await waitFor(() => {
      expect(
        screen.getAllByText(/claude api rate limit exceeded/i).length,
      ).toBeGreaterThan(0);
    });

    expect(
      screen.getByRole("button", { name: /Réessayer/i }),
    ).toBeInTheDocument();
  });
});
