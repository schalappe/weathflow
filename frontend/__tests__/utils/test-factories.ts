import type { MonthHistory, Score } from "@/types";

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
