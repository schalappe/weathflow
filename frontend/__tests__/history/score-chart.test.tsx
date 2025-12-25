import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll } from "vitest";
import { ScoreChart } from "@/components/history/score-chart";
import { createMonthHistory } from "@/__tests__/utils/test-factories";
import { t } from "@/lib/translations";

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer.
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("ScoreChart", () => {
  it("renders chart with data points", () => {
    const now = new Date();
    const months = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 3),
    ];

    const { container } = render(<ScoreChart months={months} period={12} />);

    expect(screen.getByText(t.scoreChart.title)).toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("displays empty state when no months provided", () => {
    render(<ScoreChart months={[]} period={12} />);

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByText(t.scoreChart.empty)).toBeInTheDocument();
  });

  it("renders responsive container for chart", () => {
    const now = new Date();
    const months = [
      createMonthHistory(now.getFullYear(), now.getMonth() + 1, 2),
    ];

    const { container } = render(<ScoreChart months={months} period={6} />);

    // [>]: Verify Recharts ResponsiveContainer renders (same pattern as spending-pie-chart test).
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("displays historical data from any time period", () => {
    // [>]: Chart displays all valid months in the data, regardless of how old they are.
    const historicalMonths = [createMonthHistory(2020, 1, 3)];

    const { container } = render(
      <ScoreChart months={historicalMonths} period={12} />,
    );

    // [>]: Chart should render with data, not show empty state.
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });
});
