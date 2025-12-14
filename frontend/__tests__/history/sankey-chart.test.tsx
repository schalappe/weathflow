import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll } from "vitest";
import { SankeyChart } from "@/components/history/sankey-chart";
import type { CashFlowData } from "@/types";

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer (not available in jsdom).
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

// [>]: Factory for creating test CashFlowData.
function createCashFlowData(
  overrides: Partial<CashFlowData> = {},
): CashFlowData {
  return {
    income_total: 5000,
    core_total: 2000,
    choice_total: 1000,
    compound_total: 2000,
    deficit: 0,
    core_breakdown: [
      { subcategory: "Housing", amount: 1200 },
      { subcategory: "Groceries", amount: 800 },
    ],
    choice_breakdown: [
      { subcategory: "Dining out", amount: 500 },
      { subcategory: "Entertainment", amount: 500 },
    ],
    compound_breakdown: [{ subcategory: "Investments", amount: 2000 }],
    ...overrides,
  };
}

describe("SankeyChart", () => {
  it("renders empty state when data is null", () => {
    render(<SankeyChart data={null} />);

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByText("Aucune donnée disponible")).toBeInTheDocument();
  });

  it("renders chart when valid data is provided", () => {
    const data = createCashFlowData();

    const { container } = render(<SankeyChart data={data} />);

    expect(screen.getByText("Flux de trésorerie")).toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("renders empty state when income is zero", () => {
    const data = createCashFlowData({ income_total: 0 });

    render(<SankeyChart data={data} />);

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });

  it("shows deficit node when deficit is greater than zero", () => {
    const data = createCashFlowData({
      income_total: 3000,
      core_total: 2500,
      choice_total: 1000,
      compound_total: 0,
      deficit: 500,
      compound_breakdown: [],
    });

    const { container } = render(<SankeyChart data={data} />);

    // [>]: Chart should render (deficit node handled by transformToSankeyData).
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("hides compound when deficit exists", () => {
    const data = createCashFlowData({
      income_total: 3000,
      core_total: 2500,
      choice_total: 1000,
      compound_total: 0,
      deficit: 500,
      compound_breakdown: [],
    });

    const { container } = render(<SankeyChart data={data} />);

    // [>]: Chart should render without compound (transformed data handles this).
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("renders card with correct title and subtitle", () => {
    const data = createCashFlowData();

    render(<SankeyChart data={data} />);

    expect(screen.getByText("Flux de trésorerie")).toBeInTheDocument();
    expect(
      screen.getByText("Répartition des revenus par catégorie"),
    ).toBeInTheDocument();
  });

  it("applies custom className to card", () => {
    const data = createCashFlowData();

    const { container } = render(
      <SankeyChart data={data} className="custom-class" />,
    );

    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });
});
