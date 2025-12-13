import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { HistoryClient } from "@/components/history/history-client";
import * as apiClient from "@/lib/api-client";
import { createMonthHistory } from "@/__tests__/utils/test-factories";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getMonthsHistory: vi.fn(),
  getAdvice: vi.fn().mockResolvedValue({
    success: true,
    advice: null,
    generated_at: null,
    exists: false,
  }),
  generateAdvice: vi.fn(),
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

describe("HistoryClient - State Management", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts in loading state with default period of 12", async () => {
    // [>]: Setup mock to return after a delay to catch loading state.
    mockGetMonthsHistory.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ months: [], summary: createMockSummary() }),
            100,
          ),
        ),
    );

    render(<HistoryClient />);

    // [>]: Should show skeleton loader (animate-pulse elements).
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("transitions to loaded state with months data", async () => {
    const now = new Date();
    const mockMonths = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 3),
    ];

    mockGetMonthsHistory.mockResolvedValue({
      months: mockMonths,
      summary: createMockSummary(),
    });

    render(<HistoryClient />);

    await waitFor(() => {
      expect(screen.getByText("History")).toBeInTheDocument();
    });

    // [>]: Charts should be visible.
    expect(screen.getByText("Score Evolution")).toBeInTheDocument();
  });

  it("transitions to empty state when no months returned", async () => {
    mockGetMonthsHistory.mockResolvedValue({
      months: [],
      summary: createMockSummary(),
    });

    render(<HistoryClient />);

    await waitFor(() => {
      expect(screen.getByText("No historical data")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Import your transactions to see your budget evolution over time and get personalized advice.",
      ),
    ).toBeInTheDocument();
  });

  it("updates period and triggers refetch when selection changes", async () => {
    const user = userEvent.setup();
    const now = new Date();
    const mockMonths = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 2),
    ];

    mockGetMonthsHistory.mockResolvedValue({
      months: mockMonths,
      summary: createMockSummary(),
    });

    render(<HistoryClient />);

    // [>]: Wait for initial load.
    await waitFor(() => {
      expect(screen.getByText("History")).toBeInTheDocument();
    });

    // [>]: Initial call should be with default period (12).
    expect(mockGetMonthsHistory).toHaveBeenCalledWith(12);

    // [>]: Change period to 3 months.
    await user.click(screen.getByRole("combobox"));
    await user.click(screen.getByRole("option", { name: "3 mois" }));

    // [>]: Should trigger new fetch with period 3.
    await waitFor(() => {
      expect(mockGetMonthsHistory).toHaveBeenCalledWith(3);
    });
  });
});

describe("HistoryClient - Data Fetching", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches data on initial mount with period=12", async () => {
    mockGetMonthsHistory.mockResolvedValue({
      months: [],
      summary: createMockSummary(),
    });

    render(<HistoryClient />);

    await waitFor(() => {
      expect(mockGetMonthsHistory).toHaveBeenCalledWith(12);
    });
  });

  it("displays error state when API fails", async () => {
    mockGetMonthsHistory.mockRejectedValue(new Error("Network error"));

    render(<HistoryClient />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    // [>]: Retry button should be visible.
    expect(
      screen.getByRole("button", { name: /Try Again/i }),
    ).toBeInTheDocument();
  });

  it("retries fetch when retry button clicked", async () => {
    const user = userEvent.setup();

    // [>]: First call fails, second succeeds.
    mockGetMonthsHistory
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        months: [],
        summary: createMockSummary(),
      });

    render(<HistoryClient />);

    // [>]: Wait for error state.
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    // [>]: Click retry.
    await user.click(screen.getByRole("button", { name: /Try Again/i }));

    // [>]: Should fetch again.
    await waitFor(() => {
      expect(mockGetMonthsHistory).toHaveBeenCalledTimes(2);
    });
  });
});

describe("HistoryClient - UI Rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading skeleton during initial load", async () => {
    mockGetMonthsHistory.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ months: [], summary: createMockSummary() }),
            100,
          ),
        ),
    );

    render(<HistoryClient />);

    // [>]: Skeleton loader uses animate-pulse class.
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows empty state with message and import button", async () => {
    mockGetMonthsHistory.mockResolvedValue({
      months: [],
      summary: createMockSummary(),
    });

    render(<HistoryClient />);

    await waitFor(() => {
      expect(screen.getByText("No historical data")).toBeInTheDocument();
    });

    const importButton = screen.getByRole("link", {
      name: /Import Transactions/i,
    });
    expect(importButton).toHaveAttribute("href", "/import");
  });

  it("shows error alert with retry button", async () => {
    mockGetMonthsHistory.mockRejectedValue(new Error("Server error"));

    render(<HistoryClient />);

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /Try Again/i }),
    ).toBeInTheDocument();
  });

  it("shows both charts when data is loaded", async () => {
    const now = new Date();
    const mockMonths = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 3),
    ];

    mockGetMonthsHistory.mockResolvedValue({
      months: mockMonths,
      summary: createMockSummary(),
    });

    render(<HistoryClient />);

    await waitFor(() => {
      expect(screen.getByText("Score Evolution")).toBeInTheDocument();
    });

    expect(screen.getByText("Spending Breakdown")).toBeInTheDocument();
  });
});

// [>]: Helper to create mock HistorySummary.
function createMockSummary() {
  return {
    total_months: 0,
    average_score: 0,
    score_trend: "stable" as const,
    best_month: null,
    worst_month: null,
  };
}
