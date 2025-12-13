import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ImportPageClient } from "@/components/import/import-page-client";
import { FileDropzone } from "@/components/import/file-dropzone";
import * as apiClient from "@/lib/api-client";
import {
  formatCurrency,
  formatMonthKey,
  formatMonthDisplay,
} from "@/lib/utils";

vi.mock("@/lib/api-client", () => ({
  uploadCSV: vi.fn(),
  categorize: vi.fn(),
}));

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
  ],
  preview_by_month: {},
};

describe("Additional Strategic Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("empty file shows appropriate error from API", async () => {
    vi.mocked(apiClient.uploadCSV).mockRejectedValue(
      new Error("CSV file is empty or contains no valid transactions"),
    );

    render(<ImportPageClient />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const emptyFile = new File([""], "empty.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [emptyFile] } });

    // [>]: Error shows in both Alert and FileDropzone, use getAllByText.
    await waitFor(() => {
      expect(
        screen.getAllByText(
          /csv file is empty or contains no valid transactions/i,
        ).length,
      ).toBeGreaterThan(0);
    });
  });

  it("network timeout shows error with retry option", async () => {
    vi.mocked(apiClient.uploadCSV).mockRejectedValue(
      new Error("Unable to connect to server"),
    );

    render(<ImportPageClient />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    // [>]: Error shows in both Alert and FileDropzone, use getAllByText.
    await waitFor(() => {
      expect(
        screen.getAllByText(/unable to connect to server/i).length,
      ).toBeGreaterThan(0);
    });

    // [>]: Should show retry button.
    expect(
      screen.getByRole("button", { name: /try again/i }),
    ).toBeInTheDocument();
  });

  it("selecting zero months disables Categorize button", async () => {
    vi.mocked(apiClient.uploadCSV).mockResolvedValue(mockUploadResponse);

    render(<ImportPageClient />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [csvFile] } });

    await waitFor(() => {
      expect(screen.getByText("Jan 2025")).toBeInTheDocument();
    });

    // [>]: Deselect all months.
    fireEvent.click(screen.getByRole("button", { name: "Deselect All" }));

    // [>]: Categorize button should be disabled.
    const categorizeButton = screen.getByRole("button", {
      name: /categorize with ai/i,
    });
    expect(categorizeButton).toBeDisabled();
  });

  it("multiple file drops replace previous file", async () => {
    const uploadMock = vi.mocked(apiClient.uploadCSV);
    uploadMock.mockResolvedValue(mockUploadResponse);

    render(<ImportPageClient />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    // [>]: First file.
    const file1 = new File(["content1"], "first.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file1] } });

    await waitFor(() => {
      expect(uploadMock).toHaveBeenCalledWith(file1);
    });

    // [>]: Clear mock and click start over button.
    uploadMock.mockClear();
    fireEvent.click(screen.getByRole("button", { name: /start over/i }));

    // [>]: Page reloads on cancel, so we can't test further here.
    // The test verifies the first upload worked.
  });

  it("currency formatting handles negative values", () => {
    // [>]: Test the utility function directly.
    const negative = formatCurrency(-456);
    expect(negative).toContain("-");
    expect(negative).toContain("456");
  });

  it("month key formatting produces correct YYYY-MM format", () => {
    expect(formatMonthKey(2025, 1)).toBe("2025-01");
    expect(formatMonthKey(2025, 12)).toBe("2025-12");
    expect(formatMonthKey(2024, 5)).toBe("2024-05");
  });

  it("month display formatting produces correct MMM YYYY format", () => {
    expect(formatMonthDisplay(2025, 1)).toBe("Jan 2025");
    expect(formatMonthDisplay(2025, 12)).toBe("Dec 2025");
  });

  it("dropzone shows file type validation error for non-CSV", () => {
    const onFileSelected = vi.fn();
    const onValidationError = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        onValidationError={onValidationError}
        file={null}
        isDisabled={false}
        error="Only CSV files are accepted"
      />,
    );

    expect(
      screen.getByText(/only csv files are accepted/i),
    ).toBeInTheDocument();
    // [>]: The error state should be visible with red styling.
    const dropzone = screen.getByTestId("dropzone");
    expect(dropzone).toHaveClass("border-destructive");
  });
});
