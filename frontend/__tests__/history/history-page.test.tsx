import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import HistoryPage from "@/app/history/page";
import * as apiClient from "@/lib/api-client";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getMonthsHistory: vi.fn(),
}));

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer.
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockGetMonthsHistory = vi.mocked(apiClient.getMonthsHistory);

describe("History Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders HistoryClient component", async () => {
    mockGetMonthsHistory.mockResolvedValue({
      months: [],
      summary: {
        total_months: 0,
        average_score: 0,
        score_trend: "stable" as const,
        best_month: null,
        worst_month: null,
      },
    });

    render(<HistoryPage />);

    // [>]: Should show content from HistoryClient (empty state in this case).
    await waitFor(() => {
      expect(screen.getByText("Aucune donnee historique")).toBeInTheDocument();
    });
  });

  it("wraps content in ErrorBoundary", async () => {
    // [>]: Verify ErrorBoundary catches errors gracefully.
    mockGetMonthsHistory.mockRejectedValue(new Error("Test error"));

    render(<HistoryPage />);

    // [>]: Error is caught and displayed via HistoryClient's error state.
    await waitFor(() => {
      expect(screen.getByText("Test error")).toBeInTheDocument();
    });
  });
});
