import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ScoreCard } from "@/components/dashboard/score-card";

describe("ScoreCard", () => {
  it("renders correct score format X/3", () => {
    render(
      <ScoreCard score={2} scoreLabel="Okay" monthDisplay="octobre 2025" />,
    );

    expect(screen.getByText("Score: 2/3")).toBeInTheDocument();
  });

  it("renders correct label for each score", () => {
    const { rerender } = render(
      <ScoreCard score={3} scoreLabel="Great" monthDisplay="octobre 2025" />,
    );
    expect(screen.getByText("Great")).toBeInTheDocument();

    rerender(
      <ScoreCard score={0} scoreLabel="Poor" monthDisplay="octobre 2025" />,
    );
    expect(screen.getByText("Poor")).toBeInTheDocument();

    rerender(
      <ScoreCard
        score={1}
        scoreLabel="Need Improvement"
        monthDisplay="octobre 2025"
      />,
    );
    expect(screen.getByText("Need Improvement")).toBeInTheDocument();
  });

  it("applies correct color class based on score", () => {
    const { rerender } = render(
      <ScoreCard score={3} scoreLabel="Great" monthDisplay="octobre 2025" />,
    );
    // [>]: Score 3 should have green badge.
    expect(screen.getByText("Great")).toHaveClass("bg-green-500");

    rerender(
      <ScoreCard score={2} scoreLabel="Okay" monthDisplay="octobre 2025" />,
    );
    expect(screen.getByText("Okay")).toHaveClass("bg-yellow-500");

    rerender(
      <ScoreCard
        score={1}
        scoreLabel="Need Improvement"
        monthDisplay="octobre 2025"
      />,
    );
    expect(screen.getByText("Need Improvement")).toHaveClass("bg-orange-500");

    rerender(
      <ScoreCard score={0} scoreLabel="Poor" monthDisplay="octobre 2025" />,
    );
    expect(screen.getByText("Poor")).toHaveClass("bg-red-500");
  });
});
