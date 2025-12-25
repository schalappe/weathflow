// [>]: Valid subcategories per Money Map type - mirrors backend/app/services/transactions.py:16-42.

import type { MoneyMapType } from "@/types";

export const MONEY_MAP_TYPES: MoneyMapType[] = [
  "INCOME",
  "CORE",
  "CHOICE",
  "COMPOUND",
  "EXCLUDED",
];

export const SUBCATEGORY_OPTIONS: Record<MoneyMapType, string[]> = {
  INCOME: ["Job", "Investments", "Reimbursements", "Other"],
  CORE: [
    "Housing",
    "Groceries",
    "Utilities",
    "Healthcare",
    "Transportation",
    "Basic clothing",
    "Phone and internet",
    "Insurance",
    "Debt payments",
  ],
  CHOICE: [
    "Dining out",
    "Entertainment",
    "Travel and vacations",
    "Electronics and gadgets",
    "Hobby supplies",
    "Fancy clothing",
    "Subscription services",
    "Home decor",
    "Gifts",
  ],
  COMPOUND: ["Emergency Fund", "Education Fund", "Investments", "Other"],
  EXCLUDED: [],
};
