import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { MoneyMapType } from "@/types";

// [>]: Merge Tailwind classes with clsx for conditional styling.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// [>]: Using French locale for Euro formatting with space separators.
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatMonthDisplay(year: number, month: number): string {
  const date = new Date(year, month - 1);
  return date.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
}

export function formatMonthKey(year: number, month: number): string {
  return `${year}-${month.toString().padStart(2, "0")}`;
}

// [>]: Sort month objects chronologically by year and month (oldest first).
export function sortMonthsChronologically<
  T extends { year: number; month: number },
>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return a.month - b.month;
  });
}

// [>]: Get month keys from an array of month objects.
export function getMonthKeys(
  months: { year: number; month: number }[],
): string[] {
  return months.map((m) => formatMonthKey(m.year, m.month));
}

// [>]: Pluralize a word based on count.
export function pluralize(
  count: number,
  singular: string,
  plural?: string,
): string {
  return `${count} ${count === 1 ? singular : plural || singular + "s"}`;
}

// [>]: Score colors - Neutra theme: Great=green, Okay=yellow, Need Improvement=orange, Poor=red.
export const SCORE_COLORS: Record<number, string> = {
  0: "bg-[#c45a3b]",
  1: "bg-[#d97757]",
  2: "bg-[#e8b931]",
  3: "bg-[#788c5d]",
};

// [>]: Score colors as hex values for Recharts - Neutra theme.
export const SCORE_COLORS_HEX: Record<number, string> = {
  0: "#c45a3b",
  1: "#d97757",
  2: "#e8b931",
  3: "#788c5d",
};

// [>]: Category colors for pie chart (hex) - Neutra theme palette.
export const CATEGORY_COLORS: Record<MoneyMapType, string> = {
  INCOME: "#6a9bcc",
  CORE: "#d97757",
  CHOICE: "#e8b931",
  COMPOUND: "#788c5d",
  EXCLUDED: "#b0aea5",
};

// [>]: Metric card accent Tailwind border classes - Neutra theme.
export const CATEGORY_TAILWIND: Record<MoneyMapType, string> = {
  INCOME: "border-l-[#6a9bcc]",
  CORE: "border-l-[#d97757]",
  CHOICE: "border-l-[#e8b931]",
  COMPOUND: "border-l-[#788c5d]",
  EXCLUDED: "border-l-[#b0aea5]",
};

// [>]: Badge colors for transaction categories - Neutra theme.
export const CATEGORY_BADGE_CLASSES: Record<MoneyMapType, string> = {
  INCOME: "bg-[#6a9bcc] text-white",
  CORE: "bg-[#d97757] text-white",
  CHOICE: "bg-[#e8b931] text-[#141413]",
  COMPOUND: "bg-[#788c5d] text-white",
  EXCLUDED: "bg-[#b0aea5] text-[#141413]",
};

// [>]: Money Map thresholds. Core/Choice must be <= target, Compound must be >= target.
export const THRESHOLDS = {
  CORE: 50,
  CHOICE: 30,
  COMPOUND: 20,
} as const;

export function meetsThreshold(
  category: "CORE" | "CHOICE" | "COMPOUND",
  percentage: number,
): boolean {
  if (category === "COMPOUND") {
    return percentage >= THRESHOLDS.COMPOUND;
  }
  return percentage <= THRESHOLDS[category];
}

export function formatTransactionDate(dateString: string): string {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    // [!]: Log invalid dates for debugging data quality issues.
    console.warn(
      `[formatTransactionDate] Invalid date string: "${dateString}"`,
    );
    return "--/--";
  }
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  return `${day}/${month}`;
}

// [>]: Extract error message from unknown error, with fallback.
export function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

// [>]: Pagination constants.
export const TRANSACTIONS_PER_PAGE = 25;

// [>]: Count active filters for badge display.
export function getActiveFilterCount(filters: {
  categoryTypes: string[];
  dateFrom: string | null;
  dateTo: string | null;
  searchQuery: string;
}): number {
  let count = 0;
  if (filters.categoryTypes.length > 0) count++;
  if (filters.dateFrom) count++;
  if (filters.dateTo) count++;
  if (filters.searchQuery.trim()) count++;
  return count;
}

// [>]: Format advice timestamp with French locale.
// Uses relative time for <24h, absolute date otherwise.
export function formatAdviceTimestamp(isoString: string): string {
  const date = new Date(isoString);
  if (isNaN(date.getTime())) {
    console.warn(`[formatAdviceTimestamp] Invalid date string: "${isoString}"`);
    return "date inconnue";
  }

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  // [!]: Future timestamp indicates clock skew or data corruption.
  // Show actual date instead of misleading "just now" text.
  if (diffMs < 0) {
    console.error(
      `[formatAdviceTimestamp] Future timestamp detected: "${isoString}". ` +
        `Client: ${now.toISOString()}. Diff: ${Math.abs(diffMs / 1000)}s in future.`,
    );
    return date.toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  const diffHours = diffMs / (1000 * 60 * 60);

  // [>]: Use relative time for recent advice (<24h).
  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    if (diffMinutes < 1) return "a l'instant";
    return `il y a ${diffMinutes} minute${diffMinutes > 1 ? "s" : ""}`;
  }

  if (diffHours < 24) {
    const hours = Math.floor(diffHours);
    return `il y a ${hours} heure${hours > 1 ? "s" : ""}`;
  }

  // [>]: Absolute date for older advice (French locale).
  return date.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
