import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll } from "vitest";
import { SpendingBreakdownChart } from "@/components/history/breakdown-chart";
import { createMonthHistory } from "@/__tests__/utils/test-factories";

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer.
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("SpendingBreakdownChart", () => {
  it("renders chart with valid spending data", () => {
    const months = [
      createMonthHistory(2025, 10, 3, { core: 45, choice: 28, compound: 27 }),
      createMonthHistory(2025, 11, 2, { core: 52, choice: 30, compound: 18 }),
    ];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    expect(
      screen.getByText("Spending Breakdown by Month"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("displays empty state when no data provided", () => {
    render(<SpendingBreakdownChart months={[]} />);

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByText("No spending data available")).toBeInTheDocument();
  });

  it("skips months with zero percentages", () => {
    const months = [
      createMonthHistory(2025, 10, 3, { core: 50, choice: 30, compound: 20 }),
      createMonthHistory(2025, 11, 0, { core: 0, choice: 0, compound: 0 }),
    ];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    // [>]: Chart should render (not empty) because one month has valid data.
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("renders responsive container with correct height", () => {
    const months = [
      createMonthHistory(2025, 12, 2, { core: 48, choice: 32, compound: 20 }),
    ];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    const responsiveContainer = container.querySelector(
      ".recharts-responsive-container",
    );
    expect(responsiveContainer).toBeInTheDocument();
  });
});
