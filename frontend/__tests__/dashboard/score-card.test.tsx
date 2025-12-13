import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ScoreCard } from "@/components/dashboard/score-card";

describe("ScoreCard", () => {
  it("renders correct score format X/3", () => {
    render(
      <ScoreCard score={2} scoreLabel="Okay" monthDisplay="octobre 2025" />,
    );

    // [>]: New UI shows score and /3 as separate elements.
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("/3")).toBeInTheDocument();
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

  it("applies correct gradient class based on score", () => {
    const { rerender } = render(
      <ScoreCard score={3} scoreLabel="Great" monthDisplay="octobre 2025" />,
    );
    // [>]: Neutra theme uses gradient classes instead of solid colors.
    expect(screen.getByText("Great").closest("div")).toHaveClass(
      "score-gradient-great",
    );

    rerender(
      <ScoreCard score={2} scoreLabel="Okay" monthDisplay="octobre 2025" />,
    );
    expect(screen.getByText("Okay").closest("div")).toHaveClass(
      "score-gradient-okay",
    );

    rerender(
      <ScoreCard
        score={1}
        scoreLabel="Need Improvement"
        monthDisplay="octobre 2025"
      />,
    );
    expect(screen.getByText("Need Improvement").closest("div")).toHaveClass(
      "score-gradient-need-improvement",
    );

    rerender(
      <ScoreCard score={0} scoreLabel="Poor" monthDisplay="octobre 2025" />,
    );
    expect(screen.getByText("Poor").closest("div")).toHaveClass(
      "score-gradient-poor",
    );
  });
});
