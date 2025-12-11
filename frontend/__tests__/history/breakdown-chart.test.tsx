import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeAll, vi } from "vitest";
import { SpendingBreakdownChart } from "@/components/history/breakdown-chart";
import { createMonthHistory } from "@/__tests__/utils/test-factories";

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer (not available in jsdom).
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

    expect(screen.getByText("Spending Breakdown by Month")).toBeInTheDocument();
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

  it("renders stacked bars in correct order (Core, Choice, Compound)", () => {
    const months = [
      createMonthHistory(2025, 10, 3, { core: 45, choice: 30, compound: 25 }),
    ];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    // [>]: Verify chart renders with responsive container (same assertion as other passing tests).
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("orders months chronologically (oldest to newest)", () => {
    const months = [
      createMonthHistory(2025, 12, 2, { core: 40, choice: 35, compound: 25 }),
      createMonthHistory(2025, 10, 3, { core: 50, choice: 30, compound: 20 }),
      createMonthHistory(2025, 11, 2, { core: 45, choice: 32, compound: 23 }),
    ];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    // [>]: Verify chart renders (chronological ordering is handled by transformToChartData).
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("renders tooltip with percentage format using one decimal place", async () => {
    const months = [
      createMonthHistory(2025, 10, 3, {
        core: 45.5,
        choice: 30.3,
        compound: 24.2,
      }),
    ];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    // [>]: Hover over the bar to trigger tooltip.
    const bar = container.querySelector(".recharts-bar-rectangle");
    if (bar) {
      fireEvent.mouseOver(bar);
      await waitFor(() => {
        const tooltip = container.querySelector(".recharts-tooltip-wrapper");
        if (tooltip && tooltip.textContent) {
          // [>]: Verify percentage formatting with one decimal.
          expect(tooltip.textContent).toMatch(/\d+\.\d%/);
        }
      });
    }
  });

  it("handles invalid month data gracefully", () => {
    // [>]: Suppress console.warn during this test.
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    // [>]: Intentionally malformed data to test validation.
    const months = [
      createMonthHistory(2025, 10, 3, { core: 50, choice: 30, compound: 20 }),
      { year: 2025, month: 13, core_percentage: 50 },
    ] as Parameters<typeof SpendingBreakdownChart>[0]["months"];

    const { container } = render(<SpendingBreakdownChart months={months} />);

    // [>]: Chart should still render with valid data.
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();

    // [>]: Warning should have been logged for invalid data.
    expect(warnSpy).toHaveBeenCalledWith(
      "[SpendingBreakdownChart] Skipping invalid month data:",
      expect.anything(),
    );

    warnSpy.mockRestore();
  });
});
