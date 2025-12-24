import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TransactionTable } from "@/components/dashboard/transaction-table";
import type { TransactionResponse, PaginationInfo } from "@/types";
import { DEFAULT_FILTERS } from "@/types";

const mockTransactions: TransactionResponse[] = [
  {
    id: 1,
    date: "2025-10-15",
    description: "Salary payment",
    account: "Main Account",
    amount: 3000,
    bankin_category: "Income",
    bankin_subcategory: "Salary",
    money_map_type: "INCOME",
    money_map_subcategory: "Salary",
    is_manually_corrected: false,
  },
  {
    id: 2,
    date: "2025-10-16",
    description: "Grocery shopping",
    account: "Main Account",
    amount: -85.5,
    bankin_category: "Food",
    bankin_subcategory: "Groceries",
    money_map_type: "CORE",
    money_map_subcategory: "Food",
    is_manually_corrected: false,
  },
  // [>]: Add manually corrected transaction for indicator tests.
  {
    id: 3,
    date: "2025-10-17",
    description: "Corrected expense",
    account: "Main Account",
    amount: -50,
    bankin_category: "Shopping",
    bankin_subcategory: "Misc",
    money_map_type: "CHOICE",
    money_map_subcategory: "Entertainment",
    is_manually_corrected: true,
  },
];

const mockPagination: PaginationInfo = {
  page: 1,
  page_size: 50,
  total_items: 85,
  total_pages: 2,
};

// [>]: Default props for filter-related requirements.
const mockSelectedMonth = { year: 2025, month: 10 };
const mockFiltersChange = vi.fn();

describe("TransactionTable", () => {
  it("renders table with correct columns", () => {
    render(
      <TransactionTable
        transactions={mockTransactions}
        pagination={mockPagination}
        onPageChange={vi.fn()}
        onTransactionClick={vi.fn()}
        isLoading={false}
        filters={DEFAULT_FILTERS}
        onFiltersChange={mockFiltersChange}
        selectedMonth={mockSelectedMonth}
      />,
    );

    expect(screen.getByText("Date")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByText("Montant")).toBeInTheDocument();
    expect(screen.getByText("Catégorie")).toBeInTheDocument();
  });

  it("formats date as DD/MM", () => {
    render(
      <TransactionTable
        transactions={mockTransactions}
        pagination={mockPagination}
        onPageChange={vi.fn()}
        onTransactionClick={vi.fn()}
        isLoading={false}
        filters={DEFAULT_FILTERS}
        onFiltersChange={mockFiltersChange}
        selectedMonth={mockSelectedMonth}
      />,
    );

    // [>]: 2025-10-15 should be formatted as 15/10.
    expect(screen.getByText("15/10")).toBeInTheDocument();
    expect(screen.getByText("16/10")).toBeInTheDocument();
  });

  it("formats amount with sign and applies color", () => {
    render(
      <TransactionTable
        transactions={mockTransactions}
        pagination={mockPagination}
        onPageChange={vi.fn()}
        onTransactionClick={vi.fn()}
        isLoading={false}
        filters={DEFAULT_FILTERS}
        onFiltersChange={mockFiltersChange}
        selectedMonth={mockSelectedMonth}
      />,
    );

    // [>]: Positive amount should have + prefix and compound text color.
    const positiveAmount = screen.getByText(/\+3[\s\u00A0]000[\s\u00A0]€/);
    expect(positiveAmount).toBeInTheDocument();
    expect(positiveAmount).toHaveClass("text-compound-text");

    // [>]: Negative amount should have foreground color (no special styling).
    const negativeAmount = screen.getByText(/-86[\s\u00A0]€/);
    expect(negativeAmount).toBeInTheDocument();
    expect(negativeAmount).toHaveClass("text-foreground");
  });

  it("renders pagination controls", () => {
    const onPageChange = vi.fn();
    render(
      <TransactionTable
        transactions={mockTransactions}
        pagination={mockPagination}
        onPageChange={onPageChange}
        onTransactionClick={vi.fn()}
        isLoading={false}
        filters={DEFAULT_FILTERS}
        onFiltersChange={mockFiltersChange}
        selectedMonth={mockSelectedMonth}
      />,
    );

    // [>]: New UI shows "page / total_pages" format with icon buttons.
    expect(screen.getByText("1 / 2")).toBeInTheDocument();

    // [>]: Icon buttons don't have text labels, get all buttons and check state.
    const buttons = screen.getAllByRole("button");
    const prevButton = buttons.find((btn) =>
      btn.querySelector("svg.lucide-chevron-left"),
    );
    const nextButton = buttons.find((btn) =>
      btn.querySelector("svg.lucide-chevron-right"),
    );

    expect(prevButton).toBeDisabled();
    expect(nextButton).not.toBeDisabled();

    fireEvent.click(nextButton!);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  describe("row click behavior", () => {
    it("calls onTransactionClick with transaction data when row is clicked", () => {
      const onTransactionClick = vi.fn();
      render(
        <TransactionTable
          transactions={mockTransactions}
          pagination={mockPagination}
          onPageChange={vi.fn()}
          onTransactionClick={onTransactionClick}
          isLoading={false}
          filters={DEFAULT_FILTERS}
          onFiltersChange={mockFiltersChange}
          selectedMonth={mockSelectedMonth}
        />,
      );

      // [>]: Click the row containing "Grocery shopping".
      const groceryRow = screen.getByText("Grocery shopping").closest("tr");
      fireEvent.click(groceryRow!);

      expect(onTransactionClick).toHaveBeenCalledTimes(1);
      expect(onTransactionClick).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 2,
          description: "Grocery shopping",
          amount: -85.5,
        }),
      );
    });

    it("calls handler with correct transaction when multiple rows exist", () => {
      const onTransactionClick = vi.fn();
      render(
        <TransactionTable
          transactions={mockTransactions}
          pagination={mockPagination}
          onPageChange={vi.fn()}
          onTransactionClick={onTransactionClick}
          isLoading={false}
          filters={DEFAULT_FILTERS}
          onFiltersChange={mockFiltersChange}
          selectedMonth={mockSelectedMonth}
        />,
      );

      // [>]: Click different rows and verify correct transaction is passed.
      const salaryRow = screen.getByText("Salary payment").closest("tr");
      fireEvent.click(salaryRow!);
      expect(onTransactionClick).toHaveBeenLastCalledWith(
        expect.objectContaining({ id: 1 }),
      );

      const correctedRow = screen.getByText("Corrected expense").closest("tr");
      fireEvent.click(correctedRow!);
      expect(onTransactionClick).toHaveBeenLastCalledWith(
        expect.objectContaining({ id: 3, is_manually_corrected: true }),
      );
    });
  });

  describe("manually corrected indicator", () => {
    it("displays pencil icon for manually corrected transactions", () => {
      render(
        <TransactionTable
          transactions={mockTransactions}
          pagination={mockPagination}
          onPageChange={vi.fn()}
          onTransactionClick={vi.fn()}
          isLoading={false}
          filters={DEFAULT_FILTERS}
          onFiltersChange={mockFiltersChange}
          selectedMonth={mockSelectedMonth}
        />,
      );

      // [>]: The corrected row should contain the pencil icon (SVG with lucide class).
      const correctedCell = screen.getByText("Corrected expense").closest("td");
      const pencilIcon = correctedCell?.querySelector("svg");

      expect(pencilIcon).toBeInTheDocument();
      expect(pencilIcon).toHaveClass("h-3", "w-3");
    });

    it("does not display pencil icon for non-corrected transactions", () => {
      render(
        <TransactionTable
          transactions={mockTransactions}
          pagination={mockPagination}
          onPageChange={vi.fn()}
          onTransactionClick={vi.fn()}
          isLoading={false}
          filters={DEFAULT_FILTERS}
          onFiltersChange={mockFiltersChange}
          selectedMonth={mockSelectedMonth}
        />,
      );

      // [>]: Non-corrected rows should not have pencil icons.
      const salaryCell = screen.getByText("Salary payment").closest("td");
      const pencilIcon = salaryCell?.querySelector("svg");

      expect(pencilIcon).not.toBeInTheDocument();
    });
  });

  describe("tooltip accessibility", () => {
    it("has accessible tooltip trigger for manually corrected indicator", () => {
      render(
        <TransactionTable
          transactions={mockTransactions}
          pagination={mockPagination}
          onPageChange={vi.fn()}
          onTransactionClick={vi.fn()}
          isLoading={false}
          filters={DEFAULT_FILTERS}
          onFiltersChange={mockFiltersChange}
          selectedMonth={mockSelectedMonth}
        />,
      );

      // [>]: Find the tooltip trigger wrapper (the button/span wrapping the icon).
      const correctedCell = screen.getByText("Corrected expense").closest("td");
      const tooltipTrigger = correctedCell?.querySelector(
        "[data-slot='tooltip-trigger']",
      );

      // [>]: Verify tooltip trigger exists and is properly structured.
      expect(tooltipTrigger).toBeInTheDocument();
    });
  });
});
