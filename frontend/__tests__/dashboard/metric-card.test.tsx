import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricCard } from "@/components/dashboard/metric-card";

describe("MetricCard", () => {
  it("renders category title and formatted amount", () => {
    render(<MetricCard title="Income" amount={2500} />);

    expect(screen.getByText("Income")).toBeInTheDocument();
    // [>]: French locale formats 2500 as "2 500 €".
    expect(screen.getByText(/2[\s\u00A0]500[\s\u00A0]€/)).toBeInTheDocument();
  });

  it("renders percentage for non-Income categories", () => {
    render(
      <MetricCard title="Core" amount={1200} percentage={48.5} isSuccess />,
    );

    // [>]: New UI shows "X% of income" format.
    expect(screen.getByText("48.5% of income")).toBeInTheDocument();
  });

  it("shows checkmark when threshold met", () => {
    render(<MetricCard title="Core" amount={1200} percentage={45} isSuccess />);

    expect(screen.getByLabelText("Threshold met")).toBeInTheDocument();
  });

  it("shows X icon when threshold exceeded", () => {
    render(
      <MetricCard
        title="Core"
        amount={1500}
        percentage={60}
        isSuccess={false}
      />,
    );

    expect(screen.getByLabelText("Threshold exceeded")).toBeInTheDocument();
  });

  it("shows Savings indicator when compound is positive", () => {
    render(
      <MetricCard
        title="Compound"
        amount={500}
        percentage={20}
        isSuccess
        compoundDirection="positive"
      />,
    );

    expect(screen.getByText("Savings")).toBeInTheDocument();
  });

  it("shows Withdrawal indicator when compound is negative", () => {
    render(
      <MetricCard
        title="Compound"
        amount={1082}
        percentage={-75.3}
        isSuccess={false}
        compoundDirection="negative"
      />,
    );

    expect(screen.getByText("Withdrawal")).toBeInTheDocument();
  });

  it("does not show direction indicator for non-Compound categories", () => {
    render(
      <MetricCard title="Core" amount={1200} percentage={48.5} isSuccess />,
    );

    expect(screen.queryByText("Savings")).not.toBeInTheDocument();
    expect(screen.queryByText("Withdrawal")).not.toBeInTheDocument();
  });
});
