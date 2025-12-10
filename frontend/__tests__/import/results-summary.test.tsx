import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ResultsSummary } from "@/components/import/results-summary";
import type { MonthResult } from "@/types";

const mockResults: MonthResult[] = [
  {
    year: 2025,
    month: 1,
    transactions_categorized: 89,
    transactions_skipped: 0,
    low_confidence_count: 3,
    score: 3,
    score_label: "Great",
  },
  {
    year: 2025,
    month: 2,
    transactions_categorized: 76,
    transactions_skipped: 0,
    low_confidence_count: 0,
    score: 1,
    score_label: "Need Improvement",
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

  it("displays warning when monthsNotFound contains items", () => {
    render(
      <ResultsSummary
        results={mockResults}
        monthsNotFound={["2024-11", "2024-12"]}
        totalApiCalls={5}
        onFinish={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/some months were not found in the csv/i),
    ).toBeInTheDocument();
    expect(screen.getByText("2024-11, 2024-12")).toBeInTheDocument();
  });

  it("displays low confidence count when greater than zero", () => {
    render(
      <ResultsSummary
        results={mockResults}
        monthsNotFound={[]}
        totalApiCalls={5}
        onFinish={vi.fn()}
      />,
    );

    // [>]: Jan 2025 has 3 low confidence transactions.
    expect(screen.getByText(/3 low confidence/i)).toBeInTheDocument();
  });

  it("displays skipped transactions warning when greater than zero", () => {
    const resultsWithSkipped: MonthResult[] = [
      {
        year: 2025,
        month: 1,
        transactions_categorized: 87,
        transactions_skipped: 2,
        low_confidence_count: 0,
        score: 3,
        score_label: "Great",
      },
    ];

    render(
      <ResultsSummary
        results={resultsWithSkipped}
        monthsNotFound={[]}
        totalApiCalls={2}
        onFinish={vi.fn()}
      />,
    );

    expect(screen.getByText(/2 skipped/i)).toBeInTheDocument();
  });
});
