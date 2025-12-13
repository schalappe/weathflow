import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll } from "vitest";
import { SpendingPieChart } from "@/components/dashboard/spending-pie-chart";

// [>]: Mock ResizeObserver for Recharts ResponsiveContainer.
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("SpendingPieChart", () => {
  it("renders pie chart with three segments", () => {
    render(<SpendingPieChart core={500} choice={300} compound={200} />);

    // [>]: Chart should render without empty state.
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
    expect(screen.getByText("Répartition des dépenses")).toBeInTheDocument();
  });

  it("displays chart container with recharts", () => {
    const { container } = render(
      <SpendingPieChart core={500} choice={300} compound={200} />,
    );

    // [>]: Recharts adds a responsive container class.
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("handles empty/zero values gracefully", () => {
    render(<SpendingPieChart core={0} choice={0} compound={0} />);

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByText("Aucune donnée de dépenses")).toBeInTheDocument();
  });
});
