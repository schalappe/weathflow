import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricCard } from "@/components/dashboard/metric-card";

describe("MetricCard", () => {
  it("renders category title and formatted amount", () => {
    render(
      <MetricCard
        title="Income"
        amount={2500}
        colorClass="border-l-blue-500"
      />,
    );

    expect(screen.getByText("Income")).toBeInTheDocument();
    // [>]: French locale formats 2500 as "2 500 €".
    expect(screen.getByText(/2[\s\u00A0]500[\s\u00A0]€/)).toBeInTheDocument();
  });

  it("renders percentage for non-Income categories", () => {
    render(
      <MetricCard
        title="Core"
        amount={1200}
        percentage={48.5}
        isSuccess={true}
        colorClass="border-l-violet-500"
      />,
    );

    expect(screen.getByText("48.5%")).toBeInTheDocument();
  });

  it("shows checkmark when threshold met", () => {
    render(
      <MetricCard
        title="Core"
        amount={1200}
        percentage={45}
        isSuccess={true}
        colorClass="border-l-violet-500"
      />,
    );

    expect(screen.getByLabelText("Threshold met")).toBeInTheDocument();
  });

  it("shows X icon when threshold exceeded", () => {
    render(
      <MetricCard
        title="Core"
        amount={1500}
        percentage={60}
        isSuccess={false}
        colorClass="border-l-violet-500"
      />,
    );

    expect(screen.getByLabelText("Threshold exceeded")).toBeInTheDocument();
  });
});
