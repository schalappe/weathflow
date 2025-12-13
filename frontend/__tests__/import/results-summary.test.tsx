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
    score_label: "Excellent",
  },
  {
    year: 2025,
    month: 2,
    transactions_categorized: 76,
    transactions_skipped: 0,
    low_confidence_count: 0,
    score: 1,
    score_label: "À améliorer",
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

    // [>]: Check months are rendered (French format: janvier 2025, février 2025).
    expect(screen.getByText("janvier 2025")).toBeInTheDocument();
    expect(screen.getByText("février 2025")).toBeInTheDocument();

    // [>]: Check score labels are rendered.
    expect(screen.getByText("Excellent")).toBeInTheDocument();
    expect(screen.getByText("À améliorer")).toBeInTheDocument();
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

    // [>]: Check that the "Excellent" badge exists with Neutra green styling.
    const greatBadge = screen.getByText("Excellent");
    expect(greatBadge).toHaveClass("bg-[#788c5d]");

    // [>]: Check that "À améliorer" badge has Neutra coral styling.
    const needImprovementBadge = screen.getByText("À améliorer");
    expect(needImprovementBadge).toHaveClass("bg-[#d97757]");
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
      name: /Voir les transactions/i,
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
      screen.getByText(/Certains mois n'ont pas été trouvés dans le CSV/i),
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
    expect(screen.getByText(/3 faible confiance/i)).toBeInTheDocument();
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
        score_label: "Excellent",
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

    expect(screen.getByText(/2 ignorée/i)).toBeInTheDocument();
  });
});
