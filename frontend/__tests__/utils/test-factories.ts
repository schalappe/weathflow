import type {
  AdviceData,
  MonthHistory,
  ProblemArea,
  Recommendation,
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

// [>]: Factory for creating test ProblemArea with sensible defaults.
export function createMockProblemArea(
  overrides: Partial<ProblemArea> = {},
): ProblemArea {
  return {
    category: "Abonnements",
    amount: 85,
    trend: "+20%",
    root_cause: null,
    impact: null,
    ...overrides,
  };
}

// [>]: Factory for creating test Recommendation with sensible defaults.
export function createMockRecommendation(
  overrides: Partial<Recommendation> = {},
): Recommendation {
  return {
    priority: 1,
    action: "Audite tes abonnements",
    details: "Certains ne sont peut-etre plus utilises.",
    expected_savings: "30€/mois",
    difficulty: "Facile",
    quick_win: true,
    ...overrides,
  };
}

// [>]: Factory for creating test AdviceData with sensible defaults.
export function createMockAdviceData(
  overrides: Partial<AdviceData> = {},
): AdviceData {
  return {
    analysis:
      "Tes depenses 'Choice' ont augmente de 15% sur les 3 derniers mois, principalement dans les abonnements.",
    spending_patterns: [],
    problem_areas: [
      createMockProblemArea({
        category: "Abonnements",
        amount: 85,
        trend: "+20%",
      }),
      createMockProblemArea({
        category: "Restaurants",
        amount: 120,
        trend: "+10%",
      }),
    ],
    recommendations: [
      createMockRecommendation({
        priority: 1,
        action:
          "Audite tes abonnements: certains ne sont peut-etre plus utilises.",
        details: "Netflix, Spotify, Disney+ totalisant 35€/mois.",
        expected_savings: "10€/mois",
        difficulty: "Facile",
        quick_win: true,
      }),
      createMockRecommendation({
        priority: 2,
        action:
          "Prepare tes repas le dimanche pour reduire les sorties au restaurant.",
        details: "6 commandes Uber Eats ce mois.",
        expected_savings: "45€/mois",
        difficulty: "Modéré",
        quick_win: false,
      }),
      createMockRecommendation({
        priority: 3,
        action: "Tu es proche du score 'Great'! Continue ainsi.",
        details: "Maintiens ton taux d'epargne actuel.",
        expected_savings: "0€",
        difficulty: "Facile",
        quick_win: false,
      }),
    ],
    progress_review: null,
    monthly_goal: null,
    encouragement:
      "Tu as fait des progres ce mois-ci! Continue sur cette lancee.",
    ...overrides,
  };
}
