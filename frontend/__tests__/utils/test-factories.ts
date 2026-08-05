/** @module test-factories Typed fixtures shared by frontend tests. */

import type {
  AdviceData,
  MonthHistory,
  RecommendationOutput,
  Score,
} from "@/types";
import { vi } from "vitest";

// [>]: Mock localStorage for theme and storage-related tests.
export function createLocalStorageMock() {
  let store: Record<string, string> = {};

  const mock = {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    clear: () => {
      store = {};
    },
    reset: () => {
      store = {};
      mock.getItem.mockClear();
      mock.setItem.mockClear();
    },
  };

  Object.defineProperty(window, "localStorage", { value: mock });

  return mock;
}

// [>]: Factory for creating test MonthHistory data with flexible percentages.
export function createMonthHistory(
  year: number,
  month: number,
  score: Score,
  percentages: { core: number; choice: number; compound: number } = {
    core: 50,
    choice: 30,
    compound: 20,
  },
): MonthHistory {
  const scoreLabels = ["Poor", "Need Improvement", "Okay", "Great"] as const;
  const monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  return {
    year,
    month,
    total_income: 5000,
    total_core: (5000 * percentages.core) / 100,
    total_choice: (5000 * percentages.choice) / 100,
    total_compound: (5000 * percentages.compound) / 100,
    core_percentage: percentages.core,
    choice_percentage: percentages.choice,
    compound_percentage: percentages.compound,
    score,
    score_label: scoreLabels[score],
    month_label: `${monthNames[month - 1]} ${year}`,
  };
}

/**
 * Build recommendation fixture.
 * @param overrides - Fields to replace.
 * @returns Recommendation output.
 */
export function createMockRecommendationOutput(
  overrides: Partial<RecommendationOutput> = {},
): RecommendationOutput {
  return {
    type: "recommendation",
    priority: "high",
    action: "Réduire les repas au restaurant à la moyenne récente.",
    income_dependent: false,
    amount: 120,
    deadline: "2026-01-31",
    trace: {
      summary: "Les dépenses de restauration dépassent la moyenne récente.",
      uncertainty: {
        state: "robust_despite_limit",
        effect: "La période courte ne change pas la recommandation.",
      },
      details: {
        observations: [
          {
            fact: "240 € dépensés contre 120 € en moyenne.",
            period: "octobre à décembre 2025",
            scope: "Transactions CHOICE / Dining out",
            source: "observed_data",
            evidence_type: "comparison",
            source_months: ["2025-10", "2025-11", "2025-12"],
            transaction_ids: [],
          },
        ],
        calculations: ["240 € - 120 € = 120 € d'écart mensuel."],
        conventions: ["Écart supérieur à 20 % considéré matériel."],
        limits: ["Trois mois observés seulement."],
        income_normalizations: [],
        declared_facts: [],
      },
    },
    ...overrides,
  };
}

/**
 * Build advice fixture.
 * @param overrides - Fields to replace.
 * @returns Monthly advice.
 */
export function createMockAdviceData(
  overrides: Partial<AdviceData> = {},
): AdviceData {
  return {
    outputs: [createMockRecommendationOutput()],
    clarification_trace: {
      questions_consumed: 0,
      questions: [],
      stop_reason: "no_remaining_decision_impact",
    },
    ...overrides,
  };
}
