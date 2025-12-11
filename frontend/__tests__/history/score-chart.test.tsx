import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll } from "vitest";
import { ScoreChart } from "@/components/history/score-chart";
import type { MonthHistory, Score } from "@/types";

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer.
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

// [>]: Factory for test month data.
function createMonthHistory(
  year: number,
  month: number,
  score: Score,
): MonthHistory {
  const scoreLabels = ["Poor", "Need Improvement", "Okay", "Great"] as const;
  const monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  return {
    year,
    month,
    total_income: 5000,
    total_core: 2000,
    total_choice: 1500,
    total_compound: 1000,
    core_percentage: 40,
    choice_percentage: 30,
    compound_percentage: 20,
    score,
    score_label: scoreLabels[score],
    month_label: `${monthNames[month - 1]} ${year}`,
  };
}

describe("ScoreChart", () => {
  it("renders chart with data points", () => {
    const now = new Date();
    const months = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 3),
    ];

    const { container } = render(<ScoreChart months={months} />);

    expect(
      screen.getByText("Score Evolution (Last 12 Months)"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("displays empty state when no months provided", () => {
    render(<ScoreChart months={[]} />);

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(
      screen.getByText("No historical data available"),
    ).toBeInTheDocument();
  });

  it("renders responsive container for chart", () => {
    const now = new Date();
    const months = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 2),
    ];

    const { container } = render(<ScoreChart months={months} />);

    // [>]: Verify Recharts ResponsiveContainer renders (same pattern as spending-pie-chart test).
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("handles months outside 12-month window gracefully", () => {
    // [>]: Old data should not appear in chart (outside window).
    const oldMonths = [createMonthHistory(2020, 1, 3)];

    render(<ScoreChart months={oldMonths} />);

    // [>]: Chart treats this as empty since data is outside range.
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });
});
