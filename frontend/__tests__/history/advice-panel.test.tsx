import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdvicePanel } from "@/components/history/advice-panel";
import * as apiClient from "@/lib/api-client";
import {
  createMockAdviceData,
  createMockRecommendationOutput,
} from "@/__tests__/utils/test-factories";
import type {
  AdviceData,
  ClarificationTrace,
  DeclaredFactType,
  EligibilityInfo,
} from "@/types";

vi.mock("@/lib/api-client", () => ({
  getAdvice: vi.fn(),
  generateAdvice: vi.fn(),
  getActivePriority: vi.fn(),
  putActivePriority: vi.fn(),
  deleteActivePriority: vi.fn(),
  getEmergencyFundContext: vi.fn(),
  putEmergencyFundFact: vi.fn(),
  deleteEmergencyFundFact: vi.fn(),
  getCommitmentContext: vi.fn(),
  putCommitmentFact: vi.fn(),
  deleteCommitmentFact: vi.fn(),
  getIncomeContext: vi.fn(),
  putIncomeFact: vi.fn(),
  deleteIncomeFact: vi.fn(),
  getConstraintContext: vi.fn(),
  putConstraintFact: vi.fn(),
  deleteConstraintFact: vi.fn(),
}));

const mockGetAdvice = vi.mocked(apiClient.getAdvice);
const mockGenerateAdvice = vi.mocked(apiClient.generateAdvice);
const mockGetActivePriority = vi.mocked(apiClient.getActivePriority);
const mockPutActivePriority = vi.mocked(apiClient.putActivePriority);
const mockDeleteActivePriority = vi.mocked(apiClient.deleteActivePriority);
const mockGetEmergencyFundContext = vi.mocked(
  apiClient.getEmergencyFundContext,
);
const mockPutEmergencyFundFact = vi.mocked(apiClient.putEmergencyFundFact);
const mockDeleteEmergencyFundFact = vi.mocked(
  apiClient.deleteEmergencyFundFact,
);
const mockGetCommitmentContext = vi.mocked(apiClient.getCommitmentContext);
const mockPutCommitmentFact = vi.mocked(apiClient.putCommitmentFact);
const mockDeleteCommitmentFact = vi.mocked(apiClient.deleteCommitmentFact);
const mockGetIncomeContext = vi.mocked(apiClient.getIncomeContext);
const mockPutIncomeFact = vi.mocked(apiClient.putIncomeFact);
const mockDeleteIncomeFact = vi.mocked(apiClient.deleteIncomeFact);
const mockGetConstraintContext = vi.mocked(apiClient.getConstraintContext);
const mockPutConstraintFact = vi.mocked(apiClient.putConstraintFact);
const mockDeleteConstraintFact = vi.mocked(apiClient.deleteConstraintFact);
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
    mockGetActivePriority.mockResolvedValue({ priority: null });
    mockGetEmergencyFundContext.mockResolvedValue({ facts: [] });
    mockGetCommitmentContext.mockResolvedValue({ facts: [] });
    mockGetIncomeContext.mockResolvedValue({ facts: [] });
    mockGetConstraintContext.mockResolvedValue({ facts: [] });
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
          conditional_branches: [],
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

  it("renders selective abstention with uncertainty effects and explanatory branches", async () => {
    const payment = createMockRecommendationOutput();
    payment.action = "Payer le minimum exigible du prêt auto.";
    payment.trace.uncertainty = {
      state: "robust_despite_limit",
      effect: "Le revenu incertain ne change pas le paiement minimum exigible.",
    };
    const unresolved = {
      type: "unresolved" as const,
      priority: "medium" as const,
      conclusion: "Trajectoire d'épargne : sujet non conclu.",
      trace: {
        ...payment.trace,
        uncertainty: {
          state: "unresolved" as const,
          effect: "Le revenu manquant empêche de calculer une capacité soutenable.",
        },
      },
      conditional_branches: [
        {
          condition: "le revenu couvre les obligations",
          effect: "une capacité d'épargne peut exister",
        },
        {
          condition: "le revenu ne couvre pas les obligations",
          effect: "la trajectoire reste suspendue",
        },
      ],
    };
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [payment, unresolved] })),
    );

    render(<AdvicePanel year={2025} month={12} />);

    expect(
      await screen.findByText("Robuste malgré une limite explicite"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Le revenu incertain ne change pas le paiement minimum exigible.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Branches explicatives")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Si le revenu couvre les obligations, une capacité d'épargne peut exister.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Abstention totale")).not.toBeInTheDocument();
  });

  it("announces total abstention without recommendation or no-action conclusion", async () => {
    const trace = createMockRecommendationOutput().trace;
    const unresolved = {
      type: "unresolved" as const,
      priority: "high" as const,
      conclusion: "Budget mensuel : sujet non conclu.",
      trace: {
        ...trace,
        uncertainty: {
          state: "unresolved" as const,
          effect: "La couverture insuffisante empêche toute conclusion robuste.",
        },
      },
      conditional_branches: [
        {
          condition: "tous les comptes sont couverts",
          effect: "les agrégats peuvent être réévalués",
        },
        {
          condition: "un compte manque",
          effect: "les agrégats restent insuffisants pour conclure",
        },
      ],
    };
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [unresolved] })),
    );

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText("Abstention totale")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Aucune recommandation ni conclusion sans action n’est suffisamment étayée.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Recommandation")).not.toBeInTheDocument();
    expect(screen.queryByText("Conclusion sans action")).not.toBeInTheDocument();
  });

  it("shows declared priority status, validity, and correction link in its output", async () => {
    const recommendation = createMockRecommendationOutput();
    recommendation.trace.details.declared_facts = [
      {
        fact_type: "active_priority",
        goal: "Fonds d'urgence",
        target: "6 000 €",
        deadline: null,
        state: "active",
        last_confirmed_at: "2026-08-02T12:00:00Z",
        valid_until: "2027-01-29T12:00:00Z",
        can_correct: true,
        can_delete: true,
      },
    ];
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [recommendation] })),
    );

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText("Faits déclarés")).toBeInTheDocument();
    expect(screen.getByText("Fonds d'urgence — 6 000 €")).toBeInTheDocument();
    expect(screen.getByText("Statut : active")).toBeInTheDocument();
    expect(screen.getByText(/Valide jusqu’au/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Corriger ou supprimer" }),
    ).toHaveAttribute("href", "#active-priority-context");
  });

  it("keeps robust advice visible while answering one material priority question", async () => {
    const user = userEvent.setup();
    const recommendation = createMockRecommendationOutput();
    const clarification = {
      type: "clarification" as const,
      priority: "high" as const,
      subject: "Trajectoire d'épargne",
      observation: "600 € sont disponibles pour l'épargne.",
      possible_effect: "La destination de l'épargne change.",
      question: "Quelle est votre priorité financière active ?",
      fact_type: "active_priority" as const,
      material_effects: [
        "Affecter 600 € au fonds d'urgence.",
        "Affecter 600 € au prêt auto.",
      ],
    };
    mockGetAdvice.mockResolvedValue(
      loaded(
        createMockAdviceData({ outputs: [recommendation, clarification] }),
      ),
    );
    const sessionRecommendation = createMockRecommendationOutput({
      action: "Affecter 600 € au fonds d'urgence.",
    });
    sessionRecommendation.trace.details.declared_facts = [
      {
        fact_type: "active_priority",
        goal: "Fonds d'urgence",
        target: "6 000 €",
        deadline: null,
        state: "session",
        last_confirmed_at: "2026-08-02T12:00:00Z",
        valid_until: null,
        can_correct: true,
        can_delete: true,
      },
    ];
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({
        outputs: [sessionRecommendation],
      }),
      generated_at: "2026-08-02T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText(recommendation.action)).toBeInTheDocument();
    expect(screen.getAllByText("Clarification")).toHaveLength(1);
    expect(screen.getByText(clarification.question)).toBeInTheDocument();
    expect(
      screen.getByText(/réutilisée pour vos prochains conseils/i),
    ).toBeInTheDocument();
    await user.type(
      screen.getByLabelText("Objectif courant"),
      "Fonds d'urgence",
    );
    await user.type(screen.getByLabelText("Cible"), "6 000 €");
    await user.click(
      screen.getByRole("button", { name: "Cette fois seulement" }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      activePriority: {
        goal: "Fonds d'urgence",
        target: "6 000 €",
        deadline: null,
      },
      rememberPriority: false,
    });
    expect(
      await screen.findByText("Affecter 600 € au fonds d'urgence."),
    ).toBeInTheDocument();
    expect(screen.queryByText(clarification.question)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Corriger cette réponse de session",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Supprimer cette réponse de session",
      }),
    ).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", {
        name: "Corriger cette réponse de session",
      }),
    );
    expect(await screen.findByText(clarification.question)).toBeInTheDocument();
    await user.type(
      screen.getByLabelText("Objectif courant"),
      "Fonds d'urgence",
    );
    await user.type(screen.getByLabelText("Cible"), "6 000 €");
    await user.click(
      screen.getByRole("button", { name: "Cette fois seulement" }),
    );
    await screen.findByRole("button", {
      name: "Supprimer cette réponse de session",
    });
    await user.click(
      screen.getByRole("button", {
        name: "Supprimer cette réponse de session",
      }),
    );

    await waitFor(() => expect(mockGetAdvice).toHaveBeenCalledTimes(3));
    expect(mockGenerateAdvice).toHaveBeenCalledTimes(2);
    expect(screen.getByText(clarification.question)).toBeInTheDocument();
  });

  it("answers a material safety-floor question and renders its trajectory", async () => {
    const user = userEvent.setup();
    const clarification = {
      type: "clarification" as const,
      priority: "high" as const,
      subject: "Trajectoire du fonds d'urgence",
      observation: "700 € de capacité mensuelle et 2 000 € de réserve.",
      possible_effect: "Le plancher change l'écart et l'échéance.",
      question: "Quel plancher de sécurité souhaitez-vous protéger ?",
      fact_type: "safety_floor" as const,
      material_effects: [
        "Le plancher est atteint : aucune action.",
        "Un écart subsiste : trajectoire mensuelle.",
      ],
    };
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [clarification] })),
    );
    const trajectory = createMockRecommendationOutput({
      action: "Affecter 700 € par mois au fonds d'urgence.",
      amount: 700,
      deadline: "2026-01-31",
    });
    trajectory.trace.summary =
      "Un écart de 3 400 € reste à combler en environ cinq mois.";
    trajectory.trace.details.calculations = [
      "5 400 € - 2 000 € - 0 € = 3 400 €.",
      "3 400 € / 700 € = environ 5 mois.",
    ];
    trajectory.trace.details.declared_facts = [
      {
        fact_type: "safety_floor",
        amount: 5_400,
        state: "active",
        last_confirmed_at: "2026-08-02T12:00:00Z",
        valid_until: "2027-01-29T12:00:00Z",
        can_correct: true,
        can_delete: true,
      },
    ];
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({ outputs: [trajectory] }),
      generated_at: "2026-08-02T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await user.type(
      await screen.findByLabelText("Montant du plancher de sécurité"),
      "5400",
    );
    await user.click(
      screen.getByRole("button", { name: "Répondre et réutiliser" }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      emergencyFundFact: {
        fact_type: "safety_floor",
        amount: 5_400,
      },
      rememberFact: true,
    });
    expect(
      await screen.findByText("Affecter 700 € par mois au fonds d'urgence."),
    ).toBeInTheDocument();
    expect(screen.getByText(/écart de 3 400 €/i)).toBeInTheDocument();
    expect(screen.getByText(/environ 5 mois/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Corriger ou supprimer" }),
    ).toHaveAttribute("href", "#emergency-fund-context-safety_floor");
  });

  it("skip and unknown close the question without storing context", async () => {
    const user = userEvent.setup();
    const recommendation = createMockRecommendationOutput();
    mockGetAdvice.mockResolvedValue(
      loaded(
        createMockAdviceData({
          outputs: [
            recommendation,
            {
              type: "clarification",
              priority: "medium",
              subject: "Trajectoire d'épargne",
              observation: "Une capacité d'épargne est observée.",
              possible_effect: "Sa destination dépend de la priorité.",
              question: "Quelle est votre priorité financière active ?",
              fact_type: "active_priority",
              material_effects: ["Fonds d'urgence", "Dette"],
            },
          ],
        }),
      ),
    );
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({
        outputs: [
          recommendation,
          {
            type: "unresolved",
            priority: "medium",
            conclusion: "Trajectoire d'épargne : aucune action robuste.",
            trace: recommendation.trace,
            conditional_branches: [],
          },
        ],
      }),
      generated_at: "2026-08-02T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.click(
      await screen.findByRole("button", { name: "Je ne sais pas" }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      clarificationAction: "unknown",
    });
    expect(mockPutActivePriority).not.toHaveBeenCalled();
    expect(mockDeleteActivePriority).not.toHaveBeenCalled();
    expect(screen.getByText("Sujet non conclu")).toBeInTheDocument();
    expect(screen.getByText(recommendation.action)).toBeInTheDocument();
    expect(
      screen.getByText("Trajectoire d'épargne : aucune action robuste."),
    ).toBeInTheDocument();
  });

  it("keeps robust advice through the ordered three-question user flow", async () => {
    const user = userEvent.setup();
    const recommendation = createMockRecommendationOutput();
    const questionOrder: DeclaredFactType[] = [
      "period_coverage",
      "recurring_obligation",
      "usual_disposable_income",
    ];
    const questions = [
      {
        type: "clarification" as const,
        priority: "high" as const,
        decision_lever: "amount" as const,
        answer_ease: "easy" as const,
        subject: "Couverture",
        observation: "La période peut être incomplète.",
        possible_effect: "La couverture change le montant.",
        question: "Les deux mois couvrent-ils tous vos comptes ?",
        fact_type: "period_coverage" as const,
        material_effects: ["Aucune action", "Affecter 600 €"],
        coverage_months: ["2025-11", "2025-12"],
      },
      {
        type: "clarification" as const,
        priority: "high" as const,
        decision_lever: "amount" as const,
        answer_ease: "moderate" as const,
        subject: "Obligation récurrente",
        observation: "600 € restent disponibles.",
        possible_effect: "L’obligation change le montant.",
        question: "Quel montant devez-vous payer chaque mois ?",
        fact_type: "recurring_obligation" as const,
        material_effects: ["Aucune action", "Affecter 600 €"],
      },
      {
        type: "clarification" as const,
        priority: "high" as const,
        decision_lever: "amount" as const,
        answer_ease: "easy" as const,
        subject: "Revenu habituel",
        observation: "600 € restent disponibles.",
        possible_effect: "Le revenu change le montant soutenable.",
        question: "Quel est votre revenu disponible habituel ?",
        fact_type: "usual_disposable_income" as const,
        material_effects: ["Aucune action", "Affecter 600 €"],
      },
    ];
    const trace = (
      count: number,
      stopReason: ClarificationTrace["stop_reason"],
    ): ClarificationTrace => ({
      questions_consumed: count,
      questions: questionOrder.slice(0, count).map((factType, index) => ({
        question_number: index + 1,
        fact_type: factType,
        decision_lever: "amount",
        outcome:
          stopReason === "question_pending" && index === count - 1
            ? "pending"
            : "skipped",
      })),
      stop_reason: stopReason,
    });
    mockGetAdvice.mockResolvedValue(
      loaded(
        createMockAdviceData({
          outputs: [recommendation, { ...questions[0], question_number: 1 }],
          clarification_trace: trace(1, "question_pending"),
        }),
      ),
    );
    for (const index of [1, 2]) {
      mockGenerateAdvice.mockResolvedValueOnce({
        success: true,
        advice: createMockAdviceData({
          outputs: [
            recommendation,
            { ...questions[index], question_number: index + 1 },
          ],
          clarification_trace: trace(index + 1, "question_pending"),
        }),
        generated_at: "2026-08-02T12:00:00Z",
        is_valid: true,
        was_cached: false,
      });
    }
    mockGenerateAdvice.mockResolvedValueOnce({
      success: true,
      advice: createMockAdviceData({
        outputs: [
          recommendation,
          {
            type: "unresolved",
            priority: "high",
            conclusion: "Plancher de sécurité : sujet non conclu.",
            trace: recommendation.trace,
            conditional_branches: [],
          },
        ],
        clarification_trace: trace(3, "quota_reached"),
      }),
      generated_at: "2026-08-02T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);

    for (const question of questions) {
      expect(await screen.findByText(question.question)).toBeInTheDocument();
      expect(screen.getAllByText(recommendation.action)).toHaveLength(1);
      expect(screen.getAllByText("Clarification")).toHaveLength(1);
      await user.click(screen.getByRole("button", { name: "Passer" }));
    }

    expect(
      await screen.findByText("Arrêt : plafond de trois questions atteint."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Clarification")).not.toBeInTheDocument();
    expect(
      screen.getByText("3 questions sur 3 consommées"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Couverture de la période — passée"),
    ).toBeInTheDocument();
    expect(mockGenerateAdvice).toHaveBeenCalledTimes(3);
  });

  it("shows remembered priority and exposes correction and deletion", async () => {
    const user = userEvent.setup();
    const priority = {
      goal: "Fonds d'urgence",
      target: "6 000 €",
      deadline: "2027-06-30",
      state: "corrected" as const,
      last_confirmed_at: "2026-08-02T12:00:00Z",
      valid_until: "2027-01-29T12:00:00Z",
    };
    mockGetAdvice.mockResolvedValue(loaded());
    mockGetActivePriority.mockResolvedValue({ priority });
    mockPutActivePriority.mockResolvedValue({
      priority: { ...priority, goal: "Rembourser le prêt auto" },
    });
    mockDeleteActivePriority.mockResolvedValue();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText("Fonds d'urgence")).toBeInTheDocument();
    expect(screen.getByText("Corrigé")).toBeInTheDocument();
    expect(screen.getByText("Dernière confirmation")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Corriger" }));
    const goal = screen.getByLabelText("Objectif courant");
    await user.clear(goal);
    await user.type(goal, "Rembourser le prêt auto");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(mockPutActivePriority).toHaveBeenCalledWith({
      goal: "Rembourser le prêt auto",
      target: "6 000 €",
      deadline: "2027-06-30",
    });
    await user.click(await screen.findByRole("button", { name: "Supprimer" }));
    expect(mockDeleteActivePriority).toHaveBeenCalledOnce();
  });

  it("shows expired emergency context and exposes correction and deletion", async () => {
    const user = userEvent.setup();
    const fact = {
      fact_type: "safety_floor" as const,
      amount: 5_400,
      state: "to_confirm" as const,
      last_confirmed_at: "2026-01-01T12:00:00Z",
      valid_until: "2026-06-30T12:00:00Z",
    };
    mockGetAdvice.mockResolvedValue(loaded());
    mockGetEmergencyFundContext.mockResolvedValue({ facts: [fact] });
    mockPutEmergencyFundFact.mockResolvedValue({
      fact: { ...fact, amount: 6_000, state: "corrected" },
    });
    mockDeleteEmergencyFundFact.mockResolvedValue();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText("Plancher de sécurité")).toBeInTheDocument();
    expect(screen.getByText("À confirmer")).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", {
        name: "Corriger Plancher de sécurité",
      }),
    );
    const amount = screen.getByLabelText("Montant en euros");
    await user.clear(amount);
    await user.type(amount, "6000");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(mockPutEmergencyFundFact).toHaveBeenCalledWith(
      "safety_floor",
      6_000,
    );
    await user.click(
      await screen.findByRole("button", {
        name: "Supprimer Plancher de sécurité",
      }),
    );
    expect(mockDeleteEmergencyFundFact).toHaveBeenCalledWith("safety_floor");
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

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: false,
    });
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
      screen.getByText(createMockRecommendationOutput().trace.summary),
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

  it("answers debt terms and shows their declared provenance", async () => {
    const user = userEvent.setup();
    const clarification = {
      type: "clarification" as const,
      priority: "high" as const,
      subject: "Paiement de dette",
      observation: "Une capacité mensuelle est observée.",
      possible_effect: "Un minimum exigible changerait la priorité.",
      question: "Quelles sont les conditions essentielles de la dette ?",
      fact_type: "debt_terms" as const,
      material_effects: ["Payer le minimum.", "Ne pas conclure de paiement."],
    };
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [clarification] })),
    );
    const recommendation = createMockRecommendationOutput({
      action: "Payer le minimum exigible du prêt auto.",
      amount: 250,
    });
    recommendation.trace.details.declared_facts = [
      {
        fact_id: 7,
        fact_type: "debt_terms",
        label: "Prêt auto",
        minimum_payment: 250,
        annual_rate: 4.2,
        cost: null,
        end_date: null,
        state: "active",
        last_confirmed_at: "2026-08-02T12:00:00Z",
        valid_until: "2026-10-31T12:00:00Z",
        can_correct: true,
        can_delete: true,
      },
    ];
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({ outputs: [recommendation] }),
      generated_at: "2026-08-02T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.type(await screen.findByLabelText("Libellé"), "Prêt auto");
    await user.type(screen.getByLabelText("Paiement minimum"), "250");
    await user.type(screen.getByLabelText("Taux annuel (%)"), "4.2");
    await user.click(
      screen.getByRole("button", { name: "Répondre et réutiliser" }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      commitmentFact: {
        fact_type: "debt_terms",
        label: "Prêt auto",
        minimum_payment: 250,
        annual_rate: 4.2,
        cost: null,
        end_date: null,
      },
      rememberFact: true,
    });
    expect(await screen.findByText(/Prêt auto — minimum/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Corriger ou supprimer" }),
    ).toHaveAttribute("href", "#commitment-context-7");
  });

  it("corrects and deletes remembered obligations from declared context", async () => {
    const user = userEvent.setup();
    const fact = {
      fact_id: 3,
      fact_type: "recurring_obligation" as const,
      label: "Pension alimentaire",
      amount: 300,
      frequency: "monthly" as const,
      end_date: null,
      state: "active" as const,
      last_confirmed_at: "2026-08-02T12:00:00Z",
      valid_until: "2026-10-31T12:00:00Z",
    };
    mockGetCommitmentContext.mockResolvedValue({ facts: [fact] });
    mockGetAdvice.mockResolvedValue(loaded());
    mockPutCommitmentFact.mockResolvedValue({
      fact: { ...fact, amount: 350, state: "corrected" },
    });
    mockDeleteCommitmentFact.mockResolvedValue();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<AdvicePanel year={2025} month={12} />);
    expect(
      await screen.findByText(/Pension alimentaire — 300/),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Corriger" }));
    const amount = screen.getByLabelText("Montant");
    await user.clear(amount);
    await user.type(amount, "350");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(mockPutCommitmentFact).toHaveBeenCalledWith(3, {
      fact_type: "recurring_obligation",
      label: "Pension alimentaire",
      amount: 350,
      frequency: "monthly",
      end_date: null,
    });
    await user.click(screen.getByRole("button", { name: "Supprimer" }));
    expect(mockDeleteCommitmentFact).toHaveBeenCalledWith(3);
  });
  it("answers dated expected income and shows single-counted provenance", async () => {
    const user = userEvent.setup();
    const clarification = {
      type: "clarification" as const,
      priority: "medium" as const,
      subject: "Montant soutenable",
      observation: "Le revenu habituel ne couvre pas l'échéance.",
      possible_effect:
        "Une entrée attendue peut changer le montant ou la date.",
      question: "Quelle entrée exceptionnelle attendez-vous ?",
      fact_type: "expected_one_off_income" as const,
      material_effects: ["Agir le 15 août.", "Ne conseiller aucun montant."],
    };
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [clarification] })),
    );
    const recommendation = createMockRecommendationOutput({
      action: "Affecter la prime à la priorité le 15 août.",
      amount: 1_500,
      deadline: "2026-08-15",
      income_dependent: true,
    });
    recommendation.trace.details.declared_facts = [
      {
        fact_type: "expected_one_off_income",
        label: "Prime annuelle",
        amount: 1_500,
        frequency: null,
        expected_date: "2026-08-15",
        matched_transaction: true,
        state: "active",
        last_confirmed_at: "2026-08-03T12:00:00Z",
        valid_until: "2026-08-15T23:59:59Z",
        can_correct: true,
        can_delete: true,
      },
    ];
    recommendation.trace.details.income_normalizations = [
      {
        fact_type: "expected_one_off_income",
        source_amount: 1_500,
        source_frequency: null,
        period: "2026-08-15",
        conversion: "one_off",
        normalized_amount: 1_500,
      },
    ];
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({ outputs: [recommendation] }),
      generated_at: "2026-08-03T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.type(
      await screen.findByLabelText("Montant de l’entrée exceptionnelle"),
      "1500",
    );
    await user.type(screen.getByLabelText("Libellé attendu"), "Prime annuelle");
    await user.type(screen.getByLabelText("Date attendue"), "2026-08-15");
    await user.click(
      screen.getByRole("button", { name: "Répondre et réutiliser" }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      incomeFact: {
        fact_type: "expected_one_off_income",
        label: "Prime annuelle",
        amount: 1_500,
        expected_date: "2026-08-15",
      },
      rememberFact: true,
    });
    expect(
      await screen.findByText(/Entrée exceptionnelle attendue/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Déjà rapprochée d’une opération observée/),
    ).toBeInTheDocument();
    expect(screen.getByText("Normalisation des revenus")).toBeInTheDocument();
    expect(screen.getByText(/1.*500.*2026-08-15.*one_off/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Corriger ou supprimer" }),
    ).toHaveAttribute("href", "#income-context-expected_one_off_income");
  });

  it("corrects and deletes expired habitual income from declared context", async () => {
    const user = userEvent.setup();
    const fact = {
      fact_type: "usual_disposable_income" as const,
      amount: 3_200,
      frequency: "monthly" as const,
      expected_date: null,
      state: "to_confirm" as const,
      last_confirmed_at: "2026-05-01T12:00:00Z",
      valid_until: "2026-07-30T12:00:00Z",
    };
    mockGetIncomeContext.mockResolvedValue({ facts: [fact] });
    mockGetAdvice.mockResolvedValue(loaded());
    mockPutIncomeFact.mockResolvedValue({
      fact: { ...fact, amount: 3_500, state: "corrected" },
    });
    mockDeleteIncomeFact.mockResolvedValue();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<AdvicePanel year={2025} month={12} />);
    expect(
      await screen.findByText(/Revenu disponible habituel — 3/),
    ).toBeInTheDocument();
    expect(screen.getByText("À confirmer")).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", {
        name: "Corriger Revenu disponible habituel",
      }),
    );
    const amount = screen.getByLabelText(
      "Montant du revenu disponible habituel",
    );
    await user.clear(amount);
    await user.type(amount, "3500");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(mockPutIncomeFact).toHaveBeenCalledWith({
      fact_type: "usual_disposable_income",
      amount: 3_500,
      frequency: "monthly",
    });
    await user.click(
      screen.getByRole("button", {
        name: "Supprimer Revenu disponible habituel",
      }),
    );
    expect(mockDeleteIncomeFact).toHaveBeenCalledWith(
      "usual_disposable_income",
    );
  });

  it("corrects and deletes scoped decision constraints", async () => {
    const user = userEvent.setup();
    const financialLimit = {
      fact_id: 8,
      fact_type: "financial_limit" as const,
      scope_type: "expense" as const,
      scope: "Budget transports",
      limit_type: "sustainable_amount" as const,
      amount: 90,
      state: "active" as const,
      last_confirmed_at: "2026-08-02T12:00:00Z",
      valid_until: "2026-10-31T12:00:00Z",
    };
    const unavailableAction = {
      fact_id: 9,
      fact_type: "action_unavailability" as const,
      action: "Renégocier le loyer",
      review_date: "2026-09-15",
      state: "active" as const,
      last_confirmed_at: "2026-08-02T12:00:00Z",
      valid_until: "2026-09-15T00:00:00Z",
    };
    mockGetConstraintContext.mockResolvedValue({
      facts: [financialLimit, unavailableAction],
    });
    mockGetAdvice.mockResolvedValue(loaded());
    mockPutConstraintFact.mockResolvedValue({
      fact: { ...financialLimit, amount: 75, state: "corrected" },
    });
    mockDeleteConstraintFact.mockResolvedValue();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<AdvicePanel year={2025} month={12} />);

    expect(
      await screen.findByText("Limites et indisponibilités"),
    ).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Corriger Budget transports" }),
    );
    const amount = screen.getByLabelText("Montant en euros");
    await user.clear(amount);
    await user.type(amount, "75");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));
    expect(mockPutConstraintFact).toHaveBeenCalledWith(8, {
      fact_type: "financial_limit",
      scope_type: "expense",
      scope: "Budget transports",
      limit_type: "sustainable_amount",
      amount: 75,
    });

    await user.click(
      screen.getByRole("button", { name: "Supprimer Renégocier le loyer" }),
    );
    expect(mockDeleteConstraintFact).toHaveBeenCalledWith(9);
  });

  it("answers an unavailable-action clarification with exact scope and review date", async () => {
    const user = userEvent.setup();
    const clarification = {
      type: "clarification" as const,
      priority: "medium" as const,
      subject: "Coût du logement",
      observation: "Le logement dépasse le repère générique.",
      possible_effect: "La faisabilité change l’action.",
      question: "Cette action est-elle indisponible jusqu’à une date ?",
      fact_type: "action_unavailability" as const,
      material_effects: ["Reporter le sujet.", "Conserver une action étayée."],
    };
    const trace = createMockRecommendationOutput().trace;
    trace.details.declared_facts = [
      {
        fact_id: 9,
        fact_type: "action_unavailability",
        action: "Renégocier le loyer",
        review_date: "2026-09-15",
        state: "active",
        last_confirmed_at: "2026-08-02T12:00:00Z",
        valid_until: "2026-09-15T00:00:00Z",
        can_correct: true,
        can_delete: true,
      },
    ];
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [clarification] })),
    );
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({
        outputs: [
          {
            type: "unresolved",
            priority: "medium",
            conclusion: "Aucune action faisable n’est étayée.",
            trace,
            conditional_branches: [],
          },
        ],
      }),
      generated_at: "2026-08-02T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.type(
      await screen.findByLabelText("Action indisponible"),
      "Renégocier le loyer",
    );
    await user.type(screen.getByLabelText("Date de réexamen"), "2026-09-15");
    await user.click(
      screen.getByRole("button", { name: "Répondre et réutiliser" }),
    );

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      constraintFact: {
        fact_type: "action_unavailability",
        action: "Renégocier le loyer",
        review_date: "2026-09-15",
      },
      rememberFact: true,
    });
    expect(
      await screen.findByText("Aucune action faisable n’est étayée."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Corriger ou supprimer" }),
    ).toHaveAttribute("href", "#constraint-context-9");
  });
  it("answers exact period coverage without a reuse choice", async () => {
    const user = userEvent.setup();
    mockGetAdvice.mockResolvedValue(
      loaded(
        createMockAdviceData({
          outputs: [
            {
              type: "clarification",
              priority: "high",
              subject: "Couverture de la période",
              observation: "La couverture exacte reste inconnue.",
              possible_effect: "Une absence peut perdre sa valeur probante.",
              question: "Le relevé est-il complet et sans trou ?",
              fact_type: "period_coverage",
              coverage_months: ["2025-11", "2025-12"],
              material_effects: [
                "Conserver la conclusion.",
                "Retirer la conclusion.",
              ],
            },
          ],
        }),
      ),
    );
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData(),
      generated_at: "2026-08-04T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.selectOptions(
      await screen.findByLabelText("Couverture"),
      "false",
    );
    await user.type(
      screen.getByLabelText(/Éléments manquants/),
      "Compte joint, décembre",
    );
    await user.click(screen.getByRole("button", { name: "Confirmer" }));

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      periodCoverage: {
        coverage_months: ["2025-11", "2025-12"],
        complete: false,
        missing_elements: ["Compte joint", "décembre"],
      },
    });
  });

  it("limits a transaction confirmation to the selected occurrence", async () => {
    const user = userEvent.setup();
    mockGetAdvice.mockResolvedValue(
      loaded(
        createMockAdviceData({
          outputs: [
            {
              type: "clarification",
              priority: "high",
              subject: "Nature de la transaction",
              observation: "Une contre-écriture a été importée.",
              possible_effect: "La dépense peut être conservée ou retirée.",
              question: "Quelle est la nature de cette transaction ?",
              fact_type: "transaction_nature",
              transaction_ids: [41, 42],
              linked_transaction_ids: [42],
              material_effects: [
                "Conserver la dépense.",
                "Retirer la dépense.",
              ],
            },
          ],
        }),
      ),
    );
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData(),
      generated_at: "2026-08-04T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);
    await user.click(await screen.findByRole("button", { name: "Confirmer" }));

    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      transactionNature: {
        transaction_ids: [41],
        nature: "expense",
        scope: "occurrence",
      },
    });
  });

  it("links observed evidence to its exact source", async () => {
    const output = createMockRecommendationOutput();
    output.trace.details.observations[0].transaction_ids = [17];
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [output] })),
    );

    render(<AdvicePanel year={2025} month={12} />);

    expect(
      await screen.findByRole("link", { name: "Voir les transactions" }),
    ).toHaveAttribute("href", "/?month=2025-12&transaction=17");
  });
  it("shows and confirms a material contradiction without hiding independent advice", async () => {
    const user = userEvent.setup();
    const independent = createMockRecommendationOutput({
      action: "Conserver la réserve disponible.",
      income_dependent: false,
    });
    const clarification = {
      type: "clarification" as const,
      priority: "high" as const,
      subject: "Montant soutenable",
      observation:
        "2 cycles complets et consécutifs montrent 2300 € contre 3000 € déclarés.",
      possible_effect: "Le montant soutenable doit être recalculé.",
      question: "Votre revenu habituel est-il toujours de 3000 € ?",
      fact_type: "usual_disposable_income" as const,
      material_effects: [
        "Conserver 3 000 € pour le montant soutenable.",
        "Recalculer le montant soutenable depuis 2 300 €.",
      ],
      transaction_ids: [41, 42],
      contradiction: {
        declared_value: 3_000,
        last_confirmed_at: "2026-08-01T12:00:00Z",
        signal: "recurring_income_lower" as const,
        observed_value: 2_300,
        period: ["2026-06", "2026-07"],
        scope: "Revenu disponible habituel mensuel",
        affected_subject: "Montant soutenable",
        transaction_ids: [41, 42],
        observation_keys: ["first", "second"],
        acknowledged_observations: [],
        resolution_options: [
          "confirm" as const,
          "correct" as const,
          "session" as const,
          "unknown" as const,
          "skip" as const,
          "delete" as const,
        ],
        frequency: "monthly" as const,
      },
    };
    mockGetAdvice.mockResolvedValue(
      loaded(createMockAdviceData({ outputs: [independent, clarification] })),
    );
    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: createMockAdviceData({ outputs: [independent] }),
      generated_at: "2026-08-05T12:00:00Z",
      is_valid: true,
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);

    expect(await screen.findByText(independent.action)).toBeInTheDocument();
    expect(screen.getByText("Valeur déclarée")).toBeInTheDocument();
    expect(screen.getByText("Dernière confirmation")).toBeInTheDocument();
    expect(screen.getByText("Signal")).toBeInTheDocument();
    expect(screen.getByText("Période")).toBeInTheDocument();
    expect(screen.getByText("Périmètre")).toBeInTheDocument();
    expect(screen.getByText("Sujet affecté")).toBeInTheDocument();
    const confirm = screen.getByRole("button", {
      name: /Confirmer.*3.*000.*€/,
    });
    expect(confirm).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Corriger" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cette fois seulement" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Supprimer" }),
    ).toBeInTheDocument();

    await user.click(confirm);
    expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, {
      regenerate: true,
      incomeFact: {
        fact_type: "usual_disposable_income",
        amount: 3_000,
        frequency: "monthly",
      },
      rememberFact: true,
    });
  });
});
