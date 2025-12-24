import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MonthNavigator } from "@/components/dashboard/month-navigator";
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
  {
    id: 3,
    year: 2025,
    month: 8,
    total_income: 2900,
    total_core: 1450,
    total_choice: 870,
    total_compound: 580,
    core_percentage: 50,
    choice_percentage: 30,
    compound_percentage: 20,
    score: 3,
    score_label: "Great",
    transaction_count: 68,
    created_at: "2025-08-01T00:00:00Z",
    updated_at: "2025-08-01T00:00:00Z",
  },
];

describe("MonthNavigator", () => {
  it("renders current month and navigation buttons", () => {
    render(
      <MonthNavigator
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={9}
        onMonthChange={vi.fn()}
        isDisabled={false}
      />,
    );

    expect(screen.getByText("septembre 2025")).toBeInTheDocument();
    expect(screen.getByLabelText("Mois précédent")).toBeInTheDocument();
    expect(screen.getByLabelText("Mois suivant")).toBeInTheDocument();
  });

  it("navigates to previous month when clicking left chevron", () => {
    const onMonthChange = vi.fn();
    render(
      <MonthNavigator
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={9}
        onMonthChange={onMonthChange}
        isDisabled={false}
      />,
    );

    fireEvent.click(screen.getByLabelText("Mois précédent"));
    expect(onMonthChange).toHaveBeenCalledWith(2025, 8);
  });

  it("navigates to next month when clicking right chevron", () => {
    const onMonthChange = vi.fn();
    render(
      <MonthNavigator
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={9}
        onMonthChange={onMonthChange}
        isDisabled={false}
      />,
    );

    fireEvent.click(screen.getByLabelText("Mois suivant"));
    expect(onMonthChange).toHaveBeenCalledWith(2025, 10);
  });

  it("disables previous button on oldest month", () => {
    render(
      <MonthNavigator
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={8}
        onMonthChange={vi.fn()}
        isDisabled={false}
      />,
    );

    expect(screen.getByLabelText("Mois précédent")).toBeDisabled();
    expect(screen.getByLabelText("Mois suivant")).not.toBeDisabled();
  });

  it("disables next button on newest month", () => {
    render(
      <MonthNavigator
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={10}
        onMonthChange={vi.fn()}
        isDisabled={false}
      />,
    );

    expect(screen.getByLabelText("Mois précédent")).not.toBeDisabled();
    expect(screen.getByLabelText("Mois suivant")).toBeDisabled();
  });

  it("disables both buttons when isDisabled is true", () => {
    render(
      <MonthNavigator
        months={mockMonths}
        selectedYear={2025}
        selectedMonth={9}
        onMonthChange={vi.fn()}
        isDisabled={true}
      />,
    );

    expect(screen.getByLabelText("Mois précédent")).toBeDisabled();
    expect(screen.getByLabelText("Mois suivant")).toBeDisabled();
  });
});
