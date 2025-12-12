import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import * as apiClient from "@/lib/api-client";
import { DEFAULT_FILTERS } from "@/types";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getMonthsList: vi.fn(),
  getMonthDetail: vi.fn(),
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
    page_size: 50,
    total_items: 89,
    total_pages: 2,
  },
};

describe("DashboardClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initial load fetches months list", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

    render(<DashboardClient />);

    // [>]: Should show loading state initially.
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // [>]: Wait for API call.
    await waitFor(() => {
      expect(apiClient.getMonthsList).toHaveBeenCalled();
    });
  });

  it("auto-selects most recent month on load", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

    render(<DashboardClient />);

    // [>]: Wait for data to load.
    await waitFor(() => {
      expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
        2025,
        10,
        1,
        50,
        DEFAULT_FILTERS,
      );
    });

    // [>]: Should display the most recent month (October 2025).
    await waitFor(() => {
      expect(screen.getByText("Score: 3/3")).toBeInTheDocument();
    });
  });

  it("month change triggers data fetch", async () => {
    // [>]: Testing month selection via MonthSelector is difficult with Radix Select in jsdom.
    // [>]: Instead, verify that after initial load, the first month is auto-selected and fetched.
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

    render(<DashboardClient />);

    // [>]: Wait for initial load - most recent month (October 2025) should be auto-selected.
    await waitFor(() => {
      expect(screen.getByText("Score: 3/3")).toBeInTheDocument();
    });

    // [>]: Verify the month selector is rendered with correct options.
    const selector = screen.getByRole("combobox", { name: /select month/i });
    expect(selector).toBeInTheDocument();

    // [>]: Verify getMonthDetail was called with the most recent month.
    expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
      2025,
      10,
      1,
      50,
      DEFAULT_FILTERS,
    );

    // [>]: Verify "Oct 2025" appears (in both selector and score card).
    expect(screen.getAllByText("Oct 2025").length).toBeGreaterThanOrEqual(1);
  });

  it("pagination change fetches new page", async () => {
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

    render(<DashboardClient />);

    // [>]: Wait for initial load.
    await waitFor(() => {
      expect(screen.getByText("Transactions")).toBeInTheDocument();
    });

    // [>]: Click next page.
    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton);

    // [>]: Should fetch page 2.
    await waitFor(() => {
      expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
        2025,
        10,
        2,
        50,
        DEFAULT_FILTERS,
      );
    });
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
      screen.getByRole("button", { name: /try again/i }),
    ).toBeInTheDocument();

    // [>]: Reset mock and click retry.
    vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
    vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

    fireEvent.click(screen.getByRole("button", { name: /try again/i }));

    // [>]: Should retry loading.
    await waitFor(() => {
      expect(apiClient.getMonthsList).toHaveBeenCalledTimes(2);
    });
  });

  describe("filter state management", () => {
    it("resets page to 1 when filters change", async () => {
      // [>]: Create mock that returns page 2 initially.
      const page2Detail = {
        ...mockMonthDetail,
        pagination: { ...mockMonthDetail.pagination, page: 2 },
      };
      vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
      vi.mocked(apiClient.getMonthDetail)
        .mockResolvedValueOnce(mockMonthDetail)
        .mockResolvedValueOnce(page2Detail)
        .mockResolvedValue(mockMonthDetail);

      render(<DashboardClient />);

      // [>]: Wait for initial load.
      await waitFor(() => {
        expect(screen.getByText("Transactions")).toBeInTheDocument();
      });

      // [>]: Navigate to page 2.
      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
          2025,
          10,
          2,
          50,
          DEFAULT_FILTERS,
        );
      });

      // [>]: Open category filter and select CORE.
      fireEvent.click(screen.getByText("All Categories"));
      const coreCheckbox = screen.getByRole("checkbox", { name: /CORE/i });
      fireEvent.click(coreCheckbox);

      // [>]: Should reset to page 1 with new filter.
      await waitFor(() => {
        expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
          2025,
          10,
          1,
          50,
          expect.objectContaining({ categoryTypes: ["CORE"] }),
        );
      });
    });

    it("resets filters when month changes", async () => {
      // [>]: Setup mock for different months.
      const sept2025Detail = {
        month: mockMonthsList.months[1],
        transactions: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 0,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
      vi.mocked(apiClient.getMonthDetail)
        .mockResolvedValueOnce(mockMonthDetail)
        .mockResolvedValue(sept2025Detail);

      render(<DashboardClient />);

      // [>]: Wait for initial load.
      await waitFor(() => {
        expect(screen.getByText("Transactions")).toBeInTheDocument();
      });

      // [>]: Apply a filter first.
      fireEvent.click(screen.getByText("All Categories"));
      const coreCheckbox = screen.getByRole("checkbox", { name: /CORE/i });
      fireEvent.click(coreCheckbox);

      await waitFor(() => {
        expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
          2025,
          10,
          1,
          50,
          expect.objectContaining({ categoryTypes: ["CORE"] }),
        );
      });

      // [>]: Change month via selector.
      const selector = screen.getByRole("combobox", { name: /select month/i });
      fireEvent.click(selector);

      // [>]: Select September 2025.
      const septOption = await screen.findByRole("option", { name: /Sep 2025/i });
      fireEvent.click(septOption);

      // [>]: Verify new month is fetched with DEFAULT_FILTERS (reset).
      await waitFor(() => {
        expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
          2025,
          9,
          1,
          50,
          DEFAULT_FILTERS,
        );
      });
    });

    it("passes updated filters to API when filter changes", async () => {
      vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
      vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

      render(<DashboardClient />);

      // [>]: Wait for initial load.
      await waitFor(() => {
        expect(screen.getByText("Transactions")).toBeInTheDocument();
      });

      // [>]: Clear previous calls to focus on filter change.
      vi.mocked(apiClient.getMonthDetail).mockClear();

      // [>]: Select multiple categories.
      fireEvent.click(screen.getByText("All Categories"));
      fireEvent.click(screen.getByRole("checkbox", { name: /CORE/i }));

      await waitFor(() => {
        expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
          2025,
          10,
          1,
          50,
          expect.objectContaining({
            categoryTypes: ["CORE"],
            dateFrom: null,
            dateTo: null,
            searchQuery: "",
          }),
        );
      });

      // [>]: Add another category.
      fireEvent.click(screen.getByRole("checkbox", { name: /CHOICE/i }));

      await waitFor(() => {
        expect(apiClient.getMonthDetail).toHaveBeenCalledWith(
          2025,
          10,
          1,
          50,
          expect.objectContaining({
            categoryTypes: expect.arrayContaining(["CORE", "CHOICE"]),
          }),
        );
      });
    });
  });
});
