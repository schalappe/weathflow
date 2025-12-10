import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MonthSelector } from "@/components/dashboard/month-selector";
import type { MonthSummary } from "@/types";

const mockMonths: MonthSummary[] = [
  {
    id: 1,
    year: 2025,
    month: 10,
    total_income: 3000,
    total_core: 1500,
    total_choice: 900,
    total_compound: 600,
    core_percentage: 50,
    choice_percentage: 30,
    compound_percentage: 20,
    score: 3,
    score_label: "Great",
    transaction_count: 85,
    created_at: "2025-10-01T00:00:00Z",
    updated_at: "2025-10-01T00:00:00Z",
  },
  {
    id: 2,
    year: 2025,
    month: 9,
    total_income: 2800,
    total_core: 1400,
    total_choice: 840,
    total_compound: 560,
    core_percentage: 50,
    choice_percentage: 30,
    compound_percentage: 20,
    score: 3,
    score_label: "Great",
    transaction_count: 72,
    created_at: "2025-09-01T00:00:00Z",
    updated_at: "2025-09-01T00:00:00Z",
  },
];

describe("MonthSelector", () => {
  it("renders dropdown with month options", () => {
    render(
      <MonthSelector
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={10}
        onMonthChange={vi.fn()}
        isDisabled={false}
      />,
    );

    // [>]: Trigger should show selected month.
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByLabelText("Select month")).toBeInTheDocument();
  });

  it("displays selected month value", () => {
    render(
      <MonthSelector
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={10}
        onMonthChange={vi.fn()}
        isDisabled={false}
      />,
    );

    // [>]: The selected month should be visible in the trigger.
    expect(screen.getByText("Oct 2025")).toBeInTheDocument();
  });

  it("disables dropdown when isDisabled is true", () => {
    render(
      <MonthSelector
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={10}
        onMonthChange={vi.fn()}
        isDisabled={true}
      />,
    );

    expect(screen.getByRole("combobox")).toBeDisabled();
  });
});
