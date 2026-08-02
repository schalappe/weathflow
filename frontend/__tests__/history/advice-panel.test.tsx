import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdvicePanel } from "@/components/history/advice-panel";
import * as apiClient from "@/lib/api-client";
import {
  createMockAdviceData,
  createMockRecommendationOutput,
} from "@/__tests__/utils/test-factories";
import type { AdviceData, EligibilityInfo } from "@/types";

vi.mock("@/lib/api-client", () => ({
  getAdvice: vi.fn(),
  generateAdvice: vi.fn(),
}));

const mockGetAdvice = vi.mocked(apiClient.getAdvice);
const mockGenerateAdvice = vi.mocked(apiClient.generateAdvice);
const eligibility: EligibilityInfo = {
  can_generate: true,
  is_first_advice: false,
  reason: null,
};

function loaded(advice: AdviceData = createMockAdviceData()) {
  return {
    success: true,
    exists: true as const,
    advice,
    generated_at: "2026-01-01T12:00:00Z",
    is_valid: true as const,
    eligibility,
  };
}

describe("AdvicePanel decision outputs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders recommendation, no-action, unresolved, and auditable trace", async () => {
    const recommendation = createMockRecommendationOutput();
    const advice = createMockAdviceData({
      outputs: [
        recommendation,
        {
          type: "no_action",
          priority: "low",
          conclusion: "Aucune action n'est justifiée pour l'épargne.",
          trace: recommendation.trace,
        },
        {
          type: "unresolved",
          priority: "medium",
          conclusion: "Le niveau de réserve liquide ne peut pas être conclu.",
          trace: recommendation.trace,
        },
      ],
    });
    mockGetAdvice.mockResolvedValue(loaded(advice));

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText("Recommandation")).toBeInTheDocument();
    expect(screen.getByText("Conclusion sans action")).toBeInTheDocument();
    expect(screen.getByText("Sujet non conclu")).toBeInTheDocument();
    expect(screen.getByText(recommendation.action)).toBeInTheDocument();
    expect(
      screen.getByText("Aucune action n'est justifiée pour l'épargne."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Faits observés")).toHaveLength(3);
    expect(
      screen.getAllByText("240 € dépensés contre 120 € en moyenne."),
    ).toHaveLength(3);
    expect(screen.getAllByText("octobre à décembre 2025")).toHaveLength(3);
    expect(
      screen.getAllByText("Transactions CHOICE / Dining out"),
    ).toHaveLength(3);
    expect(
      screen.getAllByText("240 € - 120 € = 120 € d'écart mensuel."),
    ).toHaveLength(3);
  });

  it("shows derived amount and deadline only when present", async () => {
    const withoutOptional = createMockRecommendationOutput({
      action: "Maintenir la trajectoire actuelle.",
      amount: undefined,
      deadline: undefined,
    });
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [withoutOptional] })),
    );

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText(withoutOptional.action)).toBeInTheDocument();
    expect(screen.queryByText("Montant")).not.toBeInTheDocument();
    expect(screen.queryByText("Échéance")).not.toBeInTheDocument();
  });

  it("never renders historical advice sections", async () => {
    mockGetAdvice.mockResolvedValue(loaded());

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText("Recommandation")).toBeInTheDocument();
    for (const heading of [
      "Points de vigilance",
      "Patterns de dépenses",
      "Suivi des progrès",
      "Objectif du mois",
      "Encouragements",
    ]) {
      expect(screen.queryByText(heading)).not.toBeInTheDocument();
    }
  });

  it("generates from the empty state", async () => {
    const user = userEvent.setup();
    const advice = createMockAdviceData();
    mockGetAdvice.mockResolvedValue({
      success: true,
      exists: false,
      advice: null,
      generated_at: null,
      is_valid: false,
      eligibility,
    });
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice,
      generated_at: "2026-01-01T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.click(
      await screen.findByRole("button", { name: /Générer des conseils/i }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, false);
    expect(await screen.findByText("Recommandation")).toBeInTheDocument();
  });

  it("keeps valid advice visible when regeneration fails", async () => {
    const user = userEvent.setup();
    const advice = createMockAdviceData();
    mockGetAdvice.mockResolvedValue(loaded(advice));
    mockGenerateAdvice.mockRejectedValue(new Error("AI service unavailable"));

    render(<AdvicePanel year={2025} month={12} />);
    await user.click(await screen.findByRole("button", { name: /Régénérer/i }));

    expect(
      await screen.findByText("AI service unavailable"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(advice.outputs[0].trace.summary),
    ).toBeInTheDocument();
  });

  it("retries loading after a fetch error", async () => {
    const user = userEvent.setup();
    mockGetAdvice
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(loaded());

    render(<AdvicePanel year={2025} month={12} />);
    await user.click(await screen.findByRole("button", { name: /Réessayer/i }));

    await waitFor(() => expect(mockGetAdvice).toHaveBeenCalledTimes(2));
  });
});
