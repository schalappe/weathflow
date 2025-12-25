import { describe, it, expect } from "vitest";
import {
  groupTransactionsBySubcategory,
  calculatePercentage,
  getSubcategoryIcon,
  translateSubcategory,
} from "@/lib/transaction-grouping";
import type { TransactionResponse } from "@/types";

// [>]: Factory for creating test transactions with minimal required fields.
function createTransaction(
  overrides: Partial<TransactionResponse> = {},
): TransactionResponse {
  return {
    id: 1,
    date: "2024-01-15",
    description: "Test transaction",
    account: "Main",
    amount: -50,
    bankin_category: null,
    bankin_subcategory: null,
    money_map_type: "CORE",
    money_map_subcategory: "Groceries",
    is_manually_corrected: false,
    ...overrides,
  };
}

describe("groupTransactionsBySubcategory", () => {
  it("splits transactions by amount sign (positive/negative)", () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: 3000,
        money_map_type: "INCOME",
        money_map_subcategory: "Job",
      }),
      createTransaction({
        id: 2,
        amount: -100,
        money_map_type: "CORE",
        money_map_subcategory: "Groceries",
      }),
      createTransaction({
        id: 3,
        amount: -50,
        money_map_type: "CHOICE",
        money_map_subcategory: "Dining out",
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    expect(result.inputs).toHaveLength(1);
    expect(result.outputs).toHaveLength(2);
    expect(result.inputsTotal).toBe(3000);
    expect(result.outputsTotal).toBe(150);
  });

  it("groups transactions by subcategory within each flow", () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: -100,
        money_map_subcategory: "Groceries",
      }),
      createTransaction({
        id: 2,
        amount: -50,
        money_map_subcategory: "Groceries",
      }),
      createTransaction({
        id: 3,
        amount: -200,
        money_map_subcategory: "Dining out",
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    expect(result.outputs).toHaveLength(2);
    const groceries = result.outputs.find((g) => g.subcategory === "Groceries");
    expect(groceries).toBeDefined();
    expect(groceries!.transactions).toHaveLength(2);
    expect(groceries!.total).toBe(150);
  });

  it("handles null subcategory by using first subcategory for that type", () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: 3000,
        money_map_type: "INCOME",
        money_map_subcategory: null,
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    // [>]: INCOME with null subcategory defaults to "Job" (first INCOME subcategory).
    expect(result.inputs).toHaveLength(1);
    expect(result.inputs[0].subcategory).toBe("Job");
  });

  it("handles empty subcategory by using type's default", () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: -100,
        money_map_type: "CORE",
        money_map_subcategory: "",
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    // [>]: CORE with empty subcategory defaults to "Housing" (first CORE subcategory).
    expect(result.outputs[0].subcategory).toBe("Housing");
  });

  it('handles null type with empty subcategory as "Other"', () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: -100,
        money_map_type: null,
        money_map_subcategory: "",
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    // [>]: "Other" is the translation key that maps to "Autre" in French.
    expect(result.outputs[0].subcategory).toBe("Other");
  });

  it("calculates percentage relative to flow total", () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: -100,
        money_map_subcategory: "Groceries",
      }),
      createTransaction({
        id: 2,
        amount: -100,
        money_map_subcategory: "Dining out",
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    // [>]: Each subcategory is 50% of total outputs.
    expect(result.outputs[0].percentage).toBe(50);
    expect(result.outputs[1].percentage).toBe(50);
  });

  it("sorts subcategories by total amount descending", () => {
    const transactions = [
      createTransaction({
        id: 1,
        amount: -50,
        money_map_subcategory: "Groceries",
      }),
      createTransaction({
        id: 2,
        amount: -200,
        money_map_subcategory: "Dining out",
      }),
      createTransaction({
        id: 3,
        amount: -100,
        money_map_subcategory: "Entertainment",
      }),
    ];

    const result = groupTransactionsBySubcategory(transactions);

    expect(result.outputs[0].subcategory).toBe("Dining out");
    expect(result.outputs[1].subcategory).toBe("Entertainment");
    expect(result.outputs[2].subcategory).toBe("Groceries");
  });

  it("handles empty transaction array", () => {
    const result = groupTransactionsBySubcategory([]);

    expect(result.inputs).toHaveLength(0);
    expect(result.outputs).toHaveLength(0);
    expect(result.inputsTotal).toBe(0);
    expect(result.outputsTotal).toBe(0);
  });
});

describe("calculatePercentage", () => {
  it("calculates percentage with 1 decimal place", () => {
    expect(calculatePercentage(325, 1000)).toBe(32.5);
    expect(calculatePercentage(333, 1000)).toBe(33.3);
  });

  it("returns 0 when total is 0", () => {
    expect(calculatePercentage(100, 0)).toBe(0);
  });

  it("handles 100% case", () => {
    expect(calculatePercentage(1000, 1000)).toBe(100);
  });
});

describe("getSubcategoryIcon", () => {
  it("returns correct icon for mapped subcategories", () => {
    expect(getSubcategoryIcon("Job")).toBe("Briefcase");
    expect(getSubcategoryIcon("Housing")).toBe("Home");
    expect(getSubcategoryIcon("Groceries")).toBe("ShoppingCart");
    expect(getSubcategoryIcon("Dining out")).toBe("Utensils");
  });

  it("returns fallback icon for unknown subcategories", () => {
    expect(getSubcategoryIcon("Unknown Category")).toBe("Circle");
    expect(getSubcategoryIcon("Autre")).toBe("Circle");
  });

  it("is case-sensitive", () => {
    expect(getSubcategoryIcon("job")).toBe("Circle");
    expect(getSubcategoryIcon("JOB")).toBe("Circle");
  });
});

describe("translateSubcategory", () => {
  it("translates known subcategories to French", () => {
    expect(translateSubcategory("Job")).toBe("Salaire");
    expect(translateSubcategory("Housing")).toBe("Logement");
    expect(translateSubcategory("Dining out")).toBe("Restaurant");
  });

  it("returns original for unknown subcategories", () => {
    expect(translateSubcategory("Unknown")).toBe("Unknown");
  });

  it("handles Other subcategory", () => {
    expect(translateSubcategory("Other")).toBe("Autre");
  });
});
