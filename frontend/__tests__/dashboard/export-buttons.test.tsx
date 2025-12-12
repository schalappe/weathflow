import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { ExportButtons } from "@/components/dashboard/export-buttons";
import * as apiClient from "@/lib/api-client";
import { toast } from "sonner";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  exportMonthData: vi.fn(),
}));

// [>]: Mock sonner toast for verifying user feedback.
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// [>]: Mock URL methods for file download testing.
const mockCreateObjectURL = vi.fn(() => "blob:mock-url");
const mockRevokeObjectURL = vi.fn();

describe("ExportButtons", () => {
  beforeAll(() => {
    // [>]: Setup URL mocks in beforeAll to ensure window is available.
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders JSON and CSV export buttons", () => {
      render(<ExportButtons year={2025} month={10} />);

      expect(screen.getByRole("button", { name: /json/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /csv/i })).toBeInTheDocument();
    });

    it("disables buttons when disabled prop is true", () => {
      render(<ExportButtons year={2025} month={10} disabled />);

      expect(screen.getByRole("button", { name: /json/i })).toBeDisabled();
      expect(screen.getByRole("button", { name: /csv/i })).toBeDisabled();
    });
  });

  describe("export functionality", () => {
    it("calls exportMonthData with correct parameters for JSON", async () => {
      const mockBlob = new Blob(["{}"], { type: "application/json" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      await waitFor(() => {
        expect(apiClient.exportMonthData).toHaveBeenCalledWith(
          2025,
          10,
          "json",
        );
      });
    });

    it("calls exportMonthData with correct parameters for CSV", async () => {
      const mockBlob = new Blob(["data"], { type: "text/csv" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /csv/i }));

      await waitFor(() => {
        expect(apiClient.exportMonthData).toHaveBeenCalledWith(2025, 10, "csv");
      });
    });

    it("triggers file download with correct filename", async () => {
      const mockBlob = new Blob(["{}"], { type: "application/json" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={3} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      // [>]: Verify blob URL was created.
      await waitFor(() => {
        expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
      });

      // [>]: Verify cleanup - object URL should be revoked after download.
      await waitFor(() => {
        expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
      });

      // [>]: Verify success toast was shown (indicates download completed).
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "JSON exported successfully",
        );
      });
    });
  });

  describe("loading state", () => {
    it("shows 'Exporting...' and disables both buttons during export", async () => {
      // [>]: Create a promise that we control to test loading state.
      let resolveExport: (blob: Blob) => void;
      const exportPromise = new Promise<Blob>((resolve) => {
        resolveExport = resolve;
      });
      vi.mocked(apiClient.exportMonthData).mockReturnValue(exportPromise);

      render(<ExportButtons year={2025} month={10} />);

      // [>]: Click JSON export.
      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      // [>]: Both buttons should be disabled during export.
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /exporting/i }),
        ).toBeDisabled();
        expect(screen.getByRole("button", { name: /csv/i })).toBeDisabled();
      });

      // [>]: Resolve the export.
      resolveExport!(new Blob(["{}"]));

      // [>]: Buttons should be re-enabled after export completes.
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /json/i }),
        ).not.toBeDisabled();
        expect(screen.getByRole("button", { name: /csv/i })).not.toBeDisabled();
      });
    });

    it("re-enables buttons after export completes", async () => {
      const mockBlob = new Blob(["{}"], { type: "application/json" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      // [>]: Wait for export to complete.
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });

      // [>]: Buttons should be enabled again.
      expect(screen.getByRole("button", { name: /json/i })).not.toBeDisabled();
      expect(screen.getByRole("button", { name: /csv/i })).not.toBeDisabled();
    });
  });

  describe("success feedback", () => {
    it("shows success toast on successful JSON export", async () => {
      const mockBlob = new Blob(["{}"], { type: "application/json" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "JSON exported successfully",
        );
      });
    });

    it("shows success toast on successful CSV export", async () => {
      const mockBlob = new Blob(["data"], { type: "text/csv" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /csv/i }));

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("CSV exported successfully");
      });
    });
  });

  describe("error handling", () => {
    it("shows error toast with message when export fails", async () => {
      vi.mocked(apiClient.exportMonthData).mockRejectedValue(
        new Error("No data found for this month"),
      );

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith("Export failed", {
          description: "No data found for this month",
        });
      });
    });

    it("shows generic error message for non-Error exceptions", async () => {
      vi.mocked(apiClient.exportMonthData).mockRejectedValue("Unknown error");

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /csv/i }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith("Export failed", {
          description: "An unexpected error occurred",
        });
      });
    });

    it("re-enables buttons after export fails", async () => {
      vi.mocked(apiClient.exportMonthData).mockRejectedValue(
        new Error("Network error"),
      );

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      // [>]: Wait for error handling.
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });

      // [>]: Buttons should be enabled again.
      expect(screen.getByRole("button", { name: /json/i })).not.toBeDisabled();
      expect(screen.getByRole("button", { name: /csv/i })).not.toBeDisabled();
    });

    it("cleans up object URL on successful export", async () => {
      const mockBlob = new Blob(["{}"], { type: "application/json" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={10} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      // [>]: Wait for export to complete.
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });

      // [>]: Object URL should be revoked (cleanup in finally block).
      expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
    });
  });

  describe("month formatting", () => {
    it("pads single-digit months in filename", async () => {
      const mockBlob = new Blob(["{}"], { type: "application/json" });
      vi.mocked(apiClient.exportMonthData).mockResolvedValue(mockBlob);

      render(<ExportButtons year={2025} month={1} />);

      fireEvent.click(screen.getByRole("button", { name: /json/i }));

      // [>]: Verify the API was called with single-digit month.
      await waitFor(() => {
        expect(apiClient.exportMonthData).toHaveBeenCalledWith(2025, 1, "json");
      });

      // [>]: Verify export completed successfully.
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "JSON exported successfully",
        );
      });
    });
  });
});
