"use client";

import { Loader2, Receipt, ChevronRight, Pencil } from "lucide-react";
import { formatCurrency, formatTransactionDate, cn } from "@/lib/utils";
import { t } from "@/lib/translations";
import type { TransactionResponse } from "@/types";

interface TransactionReviewListProps {
  transactions: TransactionResponse[];
  lowConfidenceCount: number;
  isLoading: boolean;
  onTransactionClick: (transaction: TransactionResponse) => void;
}

// [>]: Category styling with semantic colors matching the Money Map system.
const CATEGORY_CONFIG: Record<
  string,
  { bg: string; text: string; border: string; icon: string }
> = {
  INCOME: {
    bg: "bg-income/10",
    text: "text-income-text",
    border: "border-income/20",
    icon: "bg-income/20",
  },
  CORE: {
    bg: "bg-core/10",
    text: "text-core-text",
    border: "border-core/20",
    icon: "bg-core/20",
  },
  CHOICE: {
    bg: "bg-choice/10",
    text: "text-choice-text",
    border: "border-choice/20",
    icon: "bg-choice/20",
  },
  COMPOUND: {
    bg: "bg-compound/10",
    text: "text-compound-text",
    border: "border-compound/20",
    icon: "bg-compound/20",
  },
  EXCLUDED: {
    bg: "bg-excluded/10",
    text: "text-excluded-text",
    border: "border-excluded/20",
    icon: "bg-excluded/20",
  },
};

export function TransactionReviewList({
  transactions,
  isLoading,
  onTransactionClick,
}: TransactionReviewListProps) {
  if (isLoading) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <div className="relative">
          <div className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
          <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        </div>
        <p className="text-sm text-muted-foreground">{t.review.loading}</p>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <Receipt className="h-8 w-8 text-muted-foreground" />
        </div>
        <div className="text-center">
          <p className="font-medium text-foreground">Aucune transaction</p>
          <p className="text-sm text-muted-foreground">
            {t.review.noTransactions}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="review-list-container h-[calc(100vh-380px)] overflow-y-auto pr-1">
      <div className="space-y-2">
        {transactions.map((tx, index) => {
          const category = tx.money_map_type || "EXCLUDED";
          const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.EXCLUDED;

          return (
            <button
              key={tx.id}
              onClick={() => onTransactionClick(tx)}
              className={cn(
                "review-transaction-card group relative w-full rounded-xl border bg-card p-4 text-left transition-all duration-200",
                "hover:border-primary/30 hover:bg-muted/30 hover:shadow-md",
                "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:ring-offset-2",
                "animate-fade-in-up",
              )}
              style={{ animationDelay: `${Math.min(index * 30, 300)}ms` }}
            >
              <div className="flex items-center gap-4">
                {/* [>]: Category indicator bar. */}
                <div
                  className={cn(
                    "h-12 w-1 shrink-0 rounded-full transition-all duration-200",
                    config.bg,
                    "group-hover:h-14",
                  )}
                />

                {/* [>]: Main content. */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="truncate font-medium text-foreground">
                          {tx.description}
                        </p>
                        {tx.is_manually_corrected && (
                          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-choice/10">
                            <Pencil className="h-3 w-3 text-choice-text" />
                          </div>
                        )}
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-sm">
                        <span className="font-mono text-xs text-muted-foreground">
                          {formatTransactionDate(tx.date)}
                        </span>
                        <span className="text-muted-foreground/50">·</span>
                        <span
                          className={cn(
                            "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                            config.bg,
                            config.text,
                          )}
                        >
                          {t.categories[category as keyof typeof t.categories]}
                        </span>
                      </div>
                    </div>

                    {/* [>]: Amount and action indicator. */}
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p
                          className={cn(
                            "font-mono text-base font-semibold tabular-nums",
                            tx.amount >= 0
                              ? "text-compound-text"
                              : "text-foreground",
                          )}
                        >
                          {tx.amount >= 0 ? "+" : ""}
                          {formatCurrency(tx.amount)}
                        </p>
                        {tx.money_map_subcategory && (
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {t.subcategories[
                              tx.money_map_subcategory as keyof typeof t.subcategories
                            ] || tx.money_map_subcategory}
                          </p>
                        )}
                      </div>

                      {/* [>]: Chevron indicator. */}
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted/50 opacity-0 transition-all duration-200 group-hover:opacity-100">
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* [>]: Bottom fade gradient for scroll indication. */}
      <div className="pointer-events-none sticky bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background to-transparent" />
    </div>
  );
}
