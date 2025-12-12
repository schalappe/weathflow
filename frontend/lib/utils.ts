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
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
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

// [>]: Score colors matching spec: Great=#22c55e, Okay=#eab308, Need Improvement=#f97316, Poor=#ef4444.
export const SCORE_COLORS: Record<number, string> = {
  0: "bg-red-500",
  1: "bg-orange-500",
  2: "bg-yellow-500",
  3: "bg-green-500",
};

// [>]: Score colors as hex values for Recharts (matches SCORE_COLORS).
export const SCORE_COLORS_HEX: Record<number, string> = {
  0: "#ef4444",
  1: "#f97316",
  2: "#eab308",
  3: "#22c55e",
};

// [>]: Category colors for pie chart (hex) - typed with MoneyMapType for compile-time safety.
export const CATEGORY_COLORS: Record<MoneyMapType, string> = {
  INCOME: "#3b82f6",
  CORE: "#8b5cf6",
  CHOICE: "#f59e0b",
  COMPOUND: "#10b981",
  EXCLUDED: "#6b7280",
};

// [>]: Metric card accent Tailwind border classes.
export const CATEGORY_TAILWIND: Record<MoneyMapType, string> = {
  INCOME: "border-l-blue-500",
  CORE: "border-l-violet-500",
  CHOICE: "border-l-amber-500",
  COMPOUND: "border-l-emerald-500",
  EXCLUDED: "border-l-gray-500",
};

// [>]: Badge colors for transaction categories.
export const CATEGORY_BADGE_CLASSES: Record<MoneyMapType, string> = {
  INCOME: "bg-blue-500 text-white",
  CORE: "bg-violet-500 text-white",
  CHOICE: "bg-amber-500 text-white",
  COMPOUND: "bg-emerald-500 text-white",
  EXCLUDED: "bg-gray-500 text-white",
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
export const TRANSACTIONS_PER_PAGE = 50;

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
