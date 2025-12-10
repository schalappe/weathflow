import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TransactionTable } from "@/components/dashboard/transaction-table";
import type { TransactionResponse, PaginationInfo } from "@/types";

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
];

const mockPagination: PaginationInfo = {
  page: 1,
  page_size: 50,
  total_items: 85,
  total_pages: 2,
};

describe("TransactionTable", () => {
  it("renders table with correct columns", () => {
    render(
      <TransactionTable
        transactions={mockTransactions}
        pagination={mockPagination}
        onPageChange={vi.fn()}
        onTransactionClick={vi.fn()}
        isLoading={false}
      />,
    );

    expect(screen.getByText("Date")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByText("Amount")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
  });

  it("formats date as DD/MM", () => {
    render(
      <TransactionTable
        transactions={mockTransactions}
        pagination={mockPagination}
        onPageChange={vi.fn()}
        onTransactionClick={vi.fn()}
        isLoading={false}
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
      />,
    );

    // [>]: Positive amount should have + prefix and green color.
    const positiveAmount = screen.getByText(/\+3[\s\u00A0]000[\s\u00A0]€/);
    expect(positiveAmount).toBeInTheDocument();
    expect(positiveAmount).toHaveClass("text-green-600");

    // [>]: Negative amount should have red color (already has - from number).
    const negativeAmount = screen.getByText(/-86[\s\u00A0]€/);
    expect(negativeAmount).toBeInTheDocument();
    expect(negativeAmount).toHaveClass("text-red-600");
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
      />,
    );

    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
