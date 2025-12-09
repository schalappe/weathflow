import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ResultsSummary } from "@/components/import/results-summary";
import type { MonthResult } from "@/types";

const mockResults: MonthResult[] = [
  {
    year: 2025,
    month: 1,
    transactions_categorized: 89,
    low_confidence_count: 3,
    score: 3,
    score_label: "Great",
    core_percentage: 45,
    choice_percentage: 25,
    compound_percentage: 30,
  },
  {
    year: 2025,
    month: 2,
    transactions_categorized: 76,
    low_confidence_count: 0,
    score: 1,
    score_label: "Need Improvement",
    core_percentage: 60,
    choice_percentage: 35,
    compound_percentage: 5,
  },
];

describe("ResultsSummary", () => {
  it("renders each month with score, label, and percentages", () => {
    render(
      <ResultsSummary
        results={mockResults}
        monthsNotFound={[]}
        totalApiCalls={5}
        onFinish={vi.fn()}
      />,
    );

    // [>]: Check months are rendered.
    expect(screen.getByText("Jan 2025")).toBeInTheDocument();
    expect(screen.getByText("Feb 2025")).toBeInTheDocument();

    // [>]: Check score labels are rendered.
    expect(screen.getByText("Great")).toBeInTheDocument();
    expect(screen.getByText("Need Improvement")).toBeInTheDocument();
  });

  it("score badge displays correct color based on score value", () => {
    render(
      <ResultsSummary
        results={mockResults}
        monthsNotFound={[]}
        totalApiCalls={5}
        onFinish={vi.fn()}
      />,
    );

    // [>]: Check that the "Great" badge exists with green styling.
    const greatBadge = screen.getByText("Great");
    expect(greatBadge).toHaveClass("bg-green-500");

    // [>]: Check that "Need Improvement" badge has orange styling.
    const needImprovementBadge = screen.getByText("Need Improvement");
    expect(needImprovementBadge).toHaveClass("bg-orange-500");
  });

  it("View transactions button is disabled with tooltip", () => {
    render(
      <ResultsSummary
        results={mockResults}
        monthsNotFound={[]}
        totalApiCalls={5}
        onFinish={vi.fn()}
      />,
    );

    const viewButton = screen.getByRole("button", {
      name: /view transactions/i,
    });
    expect(viewButton).toBeDisabled();
  });
});
