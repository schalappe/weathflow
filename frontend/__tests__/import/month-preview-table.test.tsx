import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MonthPreviewTable } from "@/components/import/month-preview-table";
import type { MonthSummaryResponse } from "@/types";

const mockMonths: MonthSummaryResponse[] = [
  {
    year: 2025,
    month: 1,
    transaction_count: 89,
    total_income: 1429,
    total_expenses: 901,
  },
  {
    year: 2025,
    month: 2,
    transaction_count: 76,
    total_income: 0,
    total_expenses: 456,
  },
];

describe("MonthPreviewTable", () => {
  it("renders all months with correct columns", () => {
    render(
      <MonthPreviewTable
        months={mockMonths}
        selectedMonths={new Set(["2025-01", "2025-02"])}
        onToggleMonth={vi.fn()}
        onSelectAll={vi.fn()}
        onDeselectAll={vi.fn()}
        isDisabled={false}
      />,
    );

    // [>]: Check that both months are rendered.
    expect(screen.getByText("janvier 2025")).toBeInTheDocument();
    expect(screen.getByText("février 2025")).toBeInTheDocument();

    // [>]: Check transaction counts.
    expect(screen.getByText("89")).toBeInTheDocument();
    expect(screen.getByText("76")).toBeInTheDocument();
  });

  it("checkbox toggle updates selection", () => {
    const onToggleMonth = vi.fn();
    render(
      <MonthPreviewTable
        months={mockMonths}
        selectedMonths={new Set(["2025-01", "2025-02"])}
        onToggleMonth={onToggleMonth}
        onSelectAll={vi.fn()}
        onDeselectAll={vi.fn()}
        isDisabled={false}
      />,
    );

    // [>]: Click the first checkbox to toggle Jan 2025.
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    expect(onToggleMonth).toHaveBeenCalledWith("2025-01");
  });

  it("Select All and Deselect All buttons work correctly", () => {
    const onSelectAll = vi.fn();
    const onDeselectAll = vi.fn();

    render(
      <MonthPreviewTable
        months={mockMonths}
        selectedMonths={new Set(["2025-01"])}
        onToggleMonth={vi.fn()}
        onSelectAll={onSelectAll}
        onDeselectAll={onDeselectAll}
        isDisabled={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Tout sélectionner" }));
    expect(onSelectAll).toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole("button", { name: "Tout désélectionner" }),
    );
    expect(onDeselectAll).toHaveBeenCalled();
  });
});
