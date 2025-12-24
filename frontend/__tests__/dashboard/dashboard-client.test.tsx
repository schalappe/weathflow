import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import * as apiClient from "@/lib/api-client";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getMonthsList: vi.fn(),
  getMonthDetailAllTransactions: vi.fn(),
}));

// [>]: Mock Next.js Link component.
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

const mockMonthsList = {
  months: [
    {
      id: 1,
      year: 2025,
      month: 10,
      total_income: 2823,
      total_core: 1245,
      total_choice: 678,
      total_compound: 900,
      core_percentage: 44.1,
      choice_percentage: 24.0,
      compound_percentage: 31.9,
      score: 3,
      score_label: "Great" as const,
      transaction_count: 89,
      created_at: "2025-10-01",
      updated_at: "2025-10-01",
    },
    {
      id: 2,
      year: 2025,
      month: 9,
      total_income: 2500,
      total_core: 1300,
      total_choice: 500,
      total_compound: 700,
      core_percentage: 52.0,
      choice_percentage: 20.0,
      compound_percentage: 28.0,
      score: 2,
      score_label: "Okay" as const,
      transaction_count: 76,
      created_at: "2025-09-01",
      updated_at: "2025-09-01",
    },
  ],
  total: 2,
};

const mockMonthDetail = {
  month: mockMonthsList.months[0],
  transactions: [
    {
      id: 1,
      date: "2025-10-29",
      description: "Virement Salaire",
      account: null,
      amount: 2823.29,
      bankin_category: null,
      bankin_subcategory: null,
      money_map_type: "INCOME" as const,
      money_map_subcategory: null,
      is_manually_corrected: false,
    },
    {
      id: 2,
      date: "2025-10-28",
      description: "CB Carrefour",
      account: null,
      amount: -125.5,
      bankin_category: null,
      bankin_subcategory: null,
      money_map_type: "CORE" as const,
      money_map_subcategory: null,
      is_manually_corrected: false,
    },
  ],
  pagination: {
    page: 1,
    page_size: 25,
    total_items: 89,
    total_pages: 4,
  },
};

describe("DashboardClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initial load fetches months list", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetailAllTransactions).mockResolvedValue(
      mockMonthDetail,
    );

    render(<DashboardClient />);

    // [>]: Should show loading skeleton initially (animate-pulse class).
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);

    // [>]: Wait for API call.
    await waitFor(() => {
      expect(apiClient.getMonthsList).toHaveBeenCalled();
    });
  });

  it("auto-selects most recent month on load", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetailAllTransactions).mockResolvedValue(
      mockMonthDetail,
    );

    render(<DashboardClient />);

    // [>]: Wait for data to load.
    await waitFor(() => {
      // [>]: New API fetches all transactions without pagination parameters.
      expect(apiClient.getMonthDetailAllTransactions).toHaveBeenCalledWith(
        2025,
        10,
      );
    });

    // [>]: Should display the most recent month (October 2025).
    // [>]: New UI shows score and /3 as separate elements.
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("/3")).toBeInTheDocument();
    });
  });

  it("month change triggers data fetch via chevron navigation", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetailAllTransactions).mockResolvedValue(
      mockMonthDetail,
    );

    render(<DashboardClient />);

    // [>]: Wait for initial load - most recent month (October 2025) should be auto-selected.
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("/3")).toBeInTheDocument();
    });

    // [>]: Verify the month navigator is rendered with chevron buttons.
    expect(screen.getByLabelText("Mois précédent")).toBeInTheDocument();
    expect(screen.getByLabelText("Mois suivant")).toBeInTheDocument();

    // [>]: Verify getMonthDetailAllTransactions was called with the most recent month.
    expect(apiClient.getMonthDetailAllTransactions).toHaveBeenCalledWith(
      2025,
      10,
    );

    // [>]: Verify "octobre 2025" appears (in both navigator and score card).
    expect(screen.getAllByText("octobre 2025").length).toBeGreaterThanOrEqual(
      1,
    );

    // [>]: Mock response for September.
    const septemberDetail = {
      ...mockMonthDetail,
      month: mockMonthsList.months[1],
    };
    vi.mocked(apiClient.getMonthDetailAllTransactions).mockResolvedValue(
      septemberDetail,
    );

    // [>]: Click previous month button to navigate to September.
    fireEvent.click(screen.getByLabelText("Mois précédent"));

    // [>]: Should fetch September data.
    await waitFor(() => {
      expect(apiClient.getMonthDetailAllTransactions).toHaveBeenCalledWith(
        2025,
        9,
      );
    });
  });

  it("displays grouped transaction list", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetailAllTransactions).mockResolvedValue(
      mockMonthDetail,
    );

    render(<DashboardClient />);

    // [>]: Wait for initial load.
    await waitFor(() => {
      expect(screen.getByText("Transactions")).toBeInTheDocument();
    });

    // [>]: New grouped view shows tabs instead of pagination.
    expect(screen.getByRole("tab", { name: /Entrées/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Sorties/i })).toBeInTheDocument();
  });

  it("error state displays with retry button", async () => {
    vi.mocked(apiClient.getMonthsList).mockRejectedValue(
      new Error("Network error"),
    );

    render(<DashboardClient />);

    // [>]: Wait for error state.
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });

    // [>]: Should show retry button.
    expect(
      screen.getByRole("button", { name: /réessayer/i }),
    ).toBeInTheDocument();

    // [>]: Reset mock and click retry.
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetailAllTransactions).mockResolvedValue(
      mockMonthDetail,
    );

    fireEvent.click(screen.getByRole("button", { name: /réessayer/i }));

    // [>]: Should retry loading.
    await waitFor(() => {
      expect(apiClient.getMonthsList).toHaveBeenCalledTimes(2);
    });
  });

  // [>]: Filter tests removed - GroupedTransactionList uses client-side grouping
  // instead of server-side filtering. Filtering can be re-added in a future iteration.
});
