import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GroupedTransactionList } from "@/components/dashboard/grouped-transaction-list";
import type { TransactionResponse } from "@/types";

// [>]: Factory for creating test transactions with minimal required fields.
function createTransaction(
  overrides: Partial<TransactionResponse> = {},
): TransactionResponse {
  return {
    id: 1,
    date: "2024-01-15",
    description: "Test transaction",
    account: "Main",
    amount: -50,
    bankin_category: null,
    bankin_subcategory: null,
    money_map_type: "CORE",
    money_map_subcategory: "Groceries",
    is_manually_corrected: false,
    ...overrides,
  };
}

describe("GroupedTransactionList", () => {
  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  describe("Tab rendering", () => {
    it("renders tabs with correct transaction counts", () => {
      const transactions = [
        createTransaction({
          id: 1,
          amount: 3000,
          money_map_type: "INCOME",
          money_map_subcategory: "Job",
        }),
        createTransaction({
          id: 2,
          amount: -100,
          money_map_type: "CORE",
          money_map_subcategory: "Groceries",
        }),
        createTransaction({
          id: 3,
          amount: -50,
          money_map_type: "CHOICE",
          money_map_subcategory: "Dining out",
        }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: Check tab triggers show counts.
      expect(screen.getByRole("tab", { name: /Entrées/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /Sorties/i })).toBeInTheDocument();

      // [>]: Verify count badges (1 input, 2 outputs).
      const inputsTab = screen.getByRole("tab", { name: /Entrées/i });
      const outputsTab = screen.getByRole("tab", { name: /Sorties/i });

      expect(within(inputsTab).getByText("1")).toBeInTheDocument();
      expect(within(outputsTab).getByText("2")).toBeInTheDocument();
    });

    it("defaults to outputs tab", () => {
      const transactions = [
        createTransaction({ id: 1, amount: -100 }),
        createTransaction({ id: 2, amount: 1000, money_map_type: "INCOME" }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      const outputsTab = screen.getByRole("tab", { name: /Sorties/i });
      expect(outputsTab).toHaveAttribute("data-state", "active");
    });
  });

  describe("Subcategory grouping", () => {
    it("displays subcategories sorted by total amount descending", () => {
      const transactions = [
        createTransaction({
          id: 1,
          amount: -50,
          money_map_subcategory: "Groceries",
        }),
        createTransaction({
          id: 2,
          amount: -200,
          money_map_subcategory: "Dining out",
        }),
        createTransaction({
          id: 3,
          amount: -100,
          money_map_subcategory: "Entertainment",
        }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      const subcategoryButtons = screen.getAllByRole("button", {
        expanded: false,
      });

      // [>]: First subcategory should be "Restaurant" (Dining out = 200).
      expect(
        within(subcategoryButtons[0]).getByText("Restaurant"),
      ).toBeInTheDocument();
    });

    it("shows translated subcategory names", () => {
      const transactions = [
        createTransaction({
          id: 1,
          amount: -100,
          money_map_subcategory: "Groceries",
        }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: "Groceries" translates to "Courses" in French.
      expect(screen.getByText("Courses")).toBeInTheDocument();
    });
  });

  describe("Expand/collapse behavior", () => {
    it("expands subcategory on click and shows transactions", async () => {
      const user = userEvent.setup();
      const transactions = [
        createTransaction({
          id: 1,
          amount: -100,
          description: "Weekly groceries",
          money_map_subcategory: "Groceries",
        }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: Initially transactions are not visible.
      expect(screen.queryByText("Weekly groceries")).not.toBeInTheDocument();

      // [>]: Click to expand.
      const subcategoryButton = screen.getByRole("button", { expanded: false });
      await user.click(subcategoryButton);

      // [>]: Now transaction should be visible.
      expect(screen.getByText("Weekly groceries")).toBeInTheDocument();
    });

    it("collapses subcategory on second click", async () => {
      const user = userEvent.setup();
      const transactions = [
        createTransaction({
          id: 1,
          amount: -100,
          description: "Weekly groceries",
          money_map_subcategory: "Groceries",
        }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      const subcategoryButton = screen.getByRole("button", { expanded: false });

      // [>]: Expand.
      await user.click(subcategoryButton);
      expect(screen.getByText("Weekly groceries")).toBeInTheDocument();

      // [>]: Collapse.
      await user.click(screen.getByRole("button", { expanded: true }));
      expect(screen.queryByText("Weekly groceries")).not.toBeInTheDocument();
    });
  });

  describe("Transaction click callback", () => {
    it("triggers onTransactionClick when transaction row is clicked", async () => {
      const user = userEvent.setup();
      const transaction = createTransaction({
        id: 42,
        amount: -100,
        description: "Test purchase",
        money_map_subcategory: "Groceries",
      });

      render(
        <GroupedTransactionList
          transactions={[transaction]}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: Expand subcategory first.
      await user.click(screen.getByRole("button", { expanded: false }));

      // [>]: Click on the transaction row.
      await user.click(screen.getByText("Test purchase"));

      expect(mockOnClick).toHaveBeenCalledTimes(1);
      expect(mockOnClick).toHaveBeenCalledWith(transaction);
    });
  });

  describe("Empty states", () => {
    it("shows empty message when no transactions", () => {
      render(
        <GroupedTransactionList
          transactions={[]}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: Active tab (outputs) shows empty state.
      expect(screen.getByText("Aucune transaction")).toBeInTheDocument();
    });

    it("shows empty message for tab with no matching transactions", async () => {
      const user = userEvent.setup();
      const transactions = [
        createTransaction({ id: 1, amount: -100 }), // Only outputs
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: Switch to inputs tab.
      await user.click(screen.getByRole("tab", { name: /Entrées/i }));

      // [>]: Should show empty message.
      expect(screen.getByText("Aucune transaction")).toBeInTheDocument();
    });
  });

  describe("Loading state", () => {
    it("applies opacity when loading", () => {
      render(
        <GroupedTransactionList
          transactions={[]}
          onTransactionClick={mockOnClick}
          isLoading={true}
        />,
      );

      // [>]: The card should have opacity-50 class (find by data-slot).
      const card = screen
        .getByText("Transactions")
        .closest('[data-slot="card"]');
      expect(card).toHaveClass("opacity-50");
    });
  });

  describe("Manually corrected indicator", () => {
    it("shows pencil icon for manually corrected transactions", async () => {
      const user = userEvent.setup();
      const transactions = [
        createTransaction({
          id: 1,
          amount: -100,
          description: "Corrected purchase",
          money_map_subcategory: "Groceries",
          is_manually_corrected: true,
        }),
      ];

      render(
        <GroupedTransactionList
          transactions={transactions}
          onTransactionClick={mockOnClick}
          isLoading={false}
        />,
      );

      // [>]: Expand to see the transaction.
      await user.click(screen.getByRole("button", { expanded: false }));

      // [>]: Pencil icon container should be visible (has the choice bg class).
      const pencilContainer = document.querySelector(".bg-choice\\/10");
      expect(pencilContainer).toBeInTheDocument();
    });
  });
});
