// [>]: Pure utility functions for grouping transactions by subcategory.
// Used by GroupedTransactionList component for tab-based transaction display.

import { t } from "@/lib/translations";
import { SUBCATEGORY_OPTIONS } from "@/lib/category-options";
import type { TransactionResponse, MoneyMapType } from "@/types";

// [>]: Grouped subcategory with transactions and calculated metrics.
export interface SubcategoryGroup {
  subcategory: string;
  transactions: TransactionResponse[];
  total: number;
  percentage: number;
  moneyMapType: MoneyMapType | null;
}

// [>]: Result of grouping transactions by flow direction and subcategory.
export interface GroupedTransactions {
  inputs: SubcategoryGroup[];
  outputs: SubcategoryGroup[];
  inputsTotal: number;
  outputsTotal: number;
}

// [>]: Icon name mapping for common subcategories (lucide-react icon names).
// Uses fallback "Circle" for unmapped subcategories.
const SUBCATEGORY_ICONS: Record<string, string> = {
  // INCOME
  Job: "Briefcase",
  // CORE
  Housing: "Home",
  Groceries: "ShoppingCart",
  Utilities: "Zap",
  Healthcare: "Heart",
  Transportation: "Car",
  "Basic clothing": "Shirt",
  "Phone and internet": "Smartphone",
  Insurance: "Shield",
  "Debt payments": "CreditCard",
  // CHOICE
  "Dining out": "Utensils",
  Entertainment: "Music",
  "Travel and vacations": "Plane",
  "Electronics and gadgets": "Laptop",
  "Hobby supplies": "Palette",
  "Fancy clothing": "Gem",
  "Subscription services": "Repeat",
  "Home decor": "Sofa",
  Gifts: "Gift",
  // COMPOUND
  "Emergency Fund": "PiggyBank",
  "Education Fund": "GraduationCap",
  Investments: "TrendingUp",
  Other: "MoreHorizontal",
};

const FALLBACK_ICON = "Circle";

/**
 * Calculates percentage with 1 decimal place precision.
 *
 * Parameters
 * ----------
 * amount : number
 *     Subcategory total (absolute value).
 * total : number
 *     Flow total (inputs or outputs sum).
 *
 * Returns
 * -------
 * number
 *     Percentage rounded to 1 decimal place, or 0 if total is 0.
 */
export function calculatePercentage(amount: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((amount / total) * 1000) / 10;
}

/**
 * Gets the lucide-react icon name for a subcategory.
 *
 * Parameters
 * ----------
 * subcategory : string
 *     Subcategory key (e.g., "Groceries", "Dining out").
 *
 * Returns
 * -------
 * string
 *     Icon name for lucide-react, or "Circle" for unknown subcategories.
 */
export function getSubcategoryIcon(subcategory: string): string {
  return SUBCATEGORY_ICONS[subcategory] ?? FALLBACK_ICON;
}

/**
 * Translates subcategory key to French display text.
 *
 * Parameters
 * ----------
 * subcategory : string
 *     Subcategory key (e.g., "Groceries", "Dining out").
 *
 * Returns
 * -------
 * string
 *     French translation or original if not found.
 */
export function translateSubcategory(subcategory: string): string {
  const translated =
    t.subcategories[subcategory as keyof typeof t.subcategories];
  return translated ?? subcategory;
}

/**
 * Resolves the effective subcategory for a transaction.
 * Handles null/empty subcategories by using type's default subcategory.
 */
function resolveSubcategory(tx: TransactionResponse): string {
  if (tx.money_map_subcategory && tx.money_map_subcategory.trim() !== "") {
    return tx.money_map_subcategory;
  }

  // [>]: Use first subcategory for the transaction's type if available.
  if (tx.money_map_type) {
    const typeSubcategories = SUBCATEGORY_OPTIONS[tx.money_map_type];
    if (typeSubcategories && typeSubcategories.length > 0) {
      return typeSubcategories[0];
    }
  }

  return "Other";
}

/**
 * Groups transactions by flow direction (inputs/outputs) and subcategory.
 *
 * Parameters
 * ----------
 * transactions : TransactionResponse[]
 *     Raw transaction list from API.
 *
 * Returns
 * -------
 * GroupedTransactions
 *     Object with inputs (amount >= 0) and outputs (amount < 0)
 *     grouped by subcategory, sorted by total descending.
 */
export function groupTransactionsBySubcategory(
  transactions: TransactionResponse[],
): GroupedTransactions {
  // [>]: Split transactions by amount sign.
  const inputs = transactions.filter((tx) => tx.amount >= 0);
  const outputs = transactions.filter((tx) => tx.amount < 0);

  // [>]: Calculate totals for percentage calculations.
  const inputsTotal = inputs.reduce((sum, tx) => sum + tx.amount, 0);
  const outputsTotal = Math.abs(
    outputs.reduce((sum, tx) => sum + tx.amount, 0),
  );

  // [>]: Group inputs by subcategory.
  const inputGroups = groupBySubcategory(inputs, inputsTotal);

  // [>]: Group outputs by subcategory.
  const outputGroups = groupBySubcategory(outputs, outputsTotal);

  return {
    inputs: inputGroups,
    outputs: outputGroups,
    inputsTotal,
    outputsTotal,
  };
}

/**
 * Groups an array of transactions by subcategory and calculates metrics.
 */
function groupBySubcategory(
  transactions: TransactionResponse[],
  flowTotal: number,
): SubcategoryGroup[] {
  const groups = new Map<string, TransactionResponse[]>();

  // [>]: Group transactions by resolved subcategory.
  for (const tx of transactions) {
    const subcategory = resolveSubcategory(tx);
    const existing = groups.get(subcategory) ?? [];
    groups.set(subcategory, [...existing, tx]);
  }

  // [>]: Convert to SubcategoryGroup array with calculated metrics.
  const result: SubcategoryGroup[] = [];

  for (const [subcategory, txs] of groups) {
    const total = Math.abs(txs.reduce((sum, tx) => sum + tx.amount, 0));
    const percentage = calculatePercentage(total, flowTotal);
    const moneyMapType = txs[0]?.money_map_type ?? null;

    result.push({
      subcategory,
      transactions: txs,
      total,
      percentage,
      moneyMapType,
    });
  }

  // [>]: Sort by total amount descending.
  return result.sort((a, b) => b.total - a.total);
}
