import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import { TransactionTable } from "@/components/dashboard/transaction-table";
import * as apiClient from "@/lib/api-client";
import { meetsThreshold } from "@/lib/utils";
import type { PaginationInfo } from "@/types";

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

// [>]: Mock ResizeObserver for Recharts.
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("Additional Dashboard Tests - Gap Analysis", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("DashboardClient - Empty State", () => {
    it("shows empty state with link to import when no months exist", async () => {
      vi.mocked(apiClient.getMonthsList).mockResolvedValue({
        months: [],
        total: 0,
      });

      render(<DashboardClient />);

      await waitFor(() => {
        expect(screen.getByText("No months imported yet")).toBeInTheDocument();
      });

      // [>]: Should have CTA to import page (button says "Import Transactions").
      expect(
        screen.getByRole("link", { name: /import transactions/i }),
      ).toHaveAttribute("href", "/import");
    });
  });

  describe("TransactionTable - Edge Cases", () => {
    const emptyPagination: PaginationInfo = {
      page: 1,
      page_size: 50,
      total_items: 0,
      total_pages: 0,
    };

    it("shows 'No transactions' message when list is empty", () => {
      render(
        <TransactionTable
          transactions={[]}
          pagination={emptyPagination}
          onPageChange={vi.fn()}
          isLoading={false}
        />,
      );

      expect(screen.getByText("No transactions")).toBeInTheDocument();
    });

    it("applies loading overlay when isLoading is true", () => {
      const { container } = render(
        <TransactionTable
          transactions={[]}
          pagination={emptyPagination}
          onPageChange={vi.fn()}
          isLoading={true}
        />,
      );

      // [>]: Loading state applies opacity-50 class.
      const content = container.querySelector(".opacity-50");
      expect(content).toBeInTheDocument();
    });
  });

  describe("Threshold Logic - meetsThreshold utility", () => {
    it("CORE threshold met when percentage <= 50", () => {
      expect(meetsThreshold("CORE", 50)).toBe(true);
      expect(meetsThreshold("CORE", 49)).toBe(true);
      expect(meetsThreshold("CORE", 51)).toBe(false);
    });

    it("CHOICE threshold met when percentage <= 30", () => {
      expect(meetsThreshold("CHOICE", 30)).toBe(true);
      expect(meetsThreshold("CHOICE", 29)).toBe(true);
      expect(meetsThreshold("CHOICE", 31)).toBe(false);
    });

    it("COMPOUND threshold met when percentage >= 20 (inverse logic)", () => {
      // [>]: Compound is the only category with >= condition.
      expect(meetsThreshold("COMPOUND", 20)).toBe(true);
      expect(meetsThreshold("COMPOUND", 21)).toBe(true);
      expect(meetsThreshold("COMPOUND", 19)).toBe(false);
    });
  });

  describe("DashboardClient - Full Data Flow", () => {
    it("renders all components with correct data after load", async () => {
      const mockMonthsList = {
        months: [
          {
            id: 1,
            year: 2025,
            month: 10,
            total_income: 3000,
            total_core: 1500,
            total_choice: 600,
            total_compound: 900,
            core_percentage: 50,
            choice_percentage: 20,
            compound_percentage: 30,
            score: 3,
            score_label: "Great" as const,
            transaction_count: 50,
            created_at: "2025-10-01",
            updated_at: "2025-10-01",
          },
        ],
        total: 1,
      };

      const mockMonthDetail = {
        month: mockMonthsList.months[0],
        transactions: [
          {
            id: 1,
            date: "2025-10-15",
            description: "Test Transaction",
            account: null,
            amount: 100,
            bankin_category: null,
            bankin_subcategory: null,
            money_map_type: "INCOME" as const,
            money_map_subcategory: null,
            is_manually_corrected: false,
          },
        ],
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 1,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.getMonthsList).mockResolvedValue(mockMonthsList);
      vi.mocked(apiClient.getMonthDetail).mockResolvedValue(mockMonthDetail);

      render(<DashboardClient />);

      // [>]: Wait for full render.
      await waitFor(() => {
        expect(screen.getByText("Score: 3/3")).toBeInTheDocument();
      });

      // [>]: Verify all metric cards rendered.
      expect(screen.getByText("Income")).toBeInTheDocument();
      expect(screen.getByText("Core")).toBeInTheDocument();
      expect(screen.getByText("Choice")).toBeInTheDocument();
      expect(screen.getByText("Compound")).toBeInTheDocument();

      // [>]: Verify transaction table.
      expect(screen.getByText("Transactions")).toBeInTheDocument();
      expect(screen.getByText("Test Transaction")).toBeInTheDocument();

      // [>]: Verify pie chart.
      expect(screen.getByText("Spending Distribution")).toBeInTheDocument();
    });
  });
});
