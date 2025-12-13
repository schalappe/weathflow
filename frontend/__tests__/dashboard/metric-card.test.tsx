import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricCard } from "@/components/dashboard/metric-card";

describe("MetricCard", () => {
  it("renders category label and formatted amount", () => {
    render(<MetricCard category="Income" amount={2500} />);

    // [>]: Category key "Income" displays French label "Revenus".
    expect(screen.getByText("Revenus")).toBeInTheDocument();
    // [>]: French locale formats 2500 as "2 500 €".
    expect(screen.getByText(/2[\s\u00A0]500[\s\u00A0]€/)).toBeInTheDocument();
  });

  it("renders percentage for non-Income categories", () => {
    render(
      <MetricCard category="Core" amount={1200} percentage={48.5} isSuccess />,
    );

    // [>]: New UI shows "X% des revenus" format.
    expect(screen.getByText("48.5% des revenus")).toBeInTheDocument();
  });

  it("shows checkmark when threshold met", () => {
    render(
      <MetricCard category="Core" amount={1200} percentage={45} isSuccess />,
    );

    expect(screen.getByLabelText("Objectif atteint")).toBeInTheDocument();
  });

  it("shows X icon when threshold exceeded", () => {
    render(
      <MetricCard
        category="Core"
        amount={1500}
        percentage={60}
        isSuccess={false}
      />,
    );

    expect(screen.getByLabelText("Objectif dépassé")).toBeInTheDocument();
  });

  it("shows Savings indicator when compound is positive", () => {
    render(
      <MetricCard
        category="Compound"
        amount={500}
        percentage={20}
        isSuccess
        compoundDirection="positive"
      />,
    );

    // [>]: Both category label and direction indicator show "Épargne".
    // Verify by checking for exactly 2 occurrences.
    const matches = screen.getAllByText("Épargne");
    expect(matches).toHaveLength(2);
  });

  it("shows Withdrawal indicator when compound is negative", () => {
    render(
      <MetricCard
        category="Compound"
        amount={1082}
        percentage={-75.3}
        isSuccess={false}
        compoundDirection="negative"
      />,
    );

    expect(screen.getByText("Retrait")).toBeInTheDocument();
  });

  it("does not show direction indicator for non-Compound categories", () => {
    render(
      <MetricCard category="Core" amount={1200} percentage={48.5} isSuccess />,
    );

    // [>]: "Épargne" here refers to the direction indicator, not the category label.
    expect(screen.queryByText(/Épargne$/)).not.toBeInTheDocument();
    expect(screen.queryByText("Retrait")).not.toBeInTheDocument();
  });
});
