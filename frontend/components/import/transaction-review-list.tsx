"use client";

import { Loader2, Receipt } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatTransactionDate, cn } from "@/lib/utils";
import { t } from "@/lib/translations";
import type { TransactionResponse } from "@/types";

interface TransactionReviewListProps {
  transactions: TransactionResponse[];
  lowConfidenceCount: number;
  isLoading: boolean;
  onTransactionClick: (transaction: TransactionResponse) => void;
}

// [>]: Category badge styles matching dashboard/transaction-table.tsx.
const CATEGORY_STYLES: Record<string, { bg: string; text: string }> = {
  INCOME: {
    bg: "bg-income/10 hover:bg-income/20",
    text: "text-income-text",
  },
  CORE: {
    bg: "bg-core/10 hover:bg-core/20",
    text: "text-core-text",
  },
  CHOICE: {
    bg: "bg-choice/10 hover:bg-choice/20",
    text: "text-choice-text",
  },
  COMPOUND: {
    bg: "bg-compound/10 hover:bg-compound/20",
    text: "text-compound-text",
  },
  EXCLUDED: {
    bg: "bg-excluded/10 hover:bg-excluded/20",
    text: "text-excluded-text",
  },
};

export function TransactionReviewList({
  transactions,
  lowConfidenceCount,
  isLoading,
  onTransactionClick,
}: TransactionReviewListProps) {
  if (isLoading) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">{t.review.loading}</p>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <Receipt className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground">
          {t.review.noTransactions}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header with counts */}
      <div className="text-sm text-muted-foreground">
        {transactions.length} {t.review.transactions}
        {lowConfidenceCount > 0 && (
          <span className="text-amber-600">
            {" "}
            {t.review.of} {lowConfidenceCount} {t.review.lowConfidence}
          </span>
        )}
      </div>

      {/* Transaction table */}
      <div className="max-h-[60vh] overflow-auto rounded-lg border">
        <Table>
          <TableHeader className="sticky top-0 bg-background">
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[70px] text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {t.transactions.headers.date}
              </TableHead>
              <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {t.transactions.headers.description}
              </TableHead>
              <TableHead className="w-[100px] text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {t.transactions.headers.amount}
              </TableHead>
              <TableHead className="w-[110px] text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {t.transactions.headers.category}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx) => {
              const categoryStyle = tx.money_map_type
                ? CATEGORY_STYLES[tx.money_map_type] || CATEGORY_STYLES.EXCLUDED
                : CATEGORY_STYLES.EXCLUDED;

              return (
                <TableRow
                  key={tx.id}
                  onClick={() => onTransactionClick(tx)}
                  className="cursor-pointer transition-colors hover:bg-muted/50"
                >
                  <TableCell className="py-3 font-mono text-xs text-muted-foreground">
                    {formatTransactionDate(tx.date)}
                  </TableCell>
                  <TableCell className="max-w-[280px] py-3">
                    <span className="truncate text-sm">{tx.description}</span>
                  </TableCell>
                  <TableCell className="py-3 text-right">
                    <span
                      className={cn(
                        "font-mono text-sm font-semibold tabular-nums",
                        tx.amount >= 0
                          ? "text-compound-text"
                          : "text-foreground",
                      )}
                    >
                      {tx.amount >= 0 ? "+" : ""}
                      {formatCurrency(tx.amount)}
                    </span>
                  </TableCell>
                  <TableCell className="py-3">
                    {tx.money_map_type && (
                      <span
                        className={cn(
                          "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium transition-colors",
                          categoryStyle.bg,
                          categoryStyle.text,
                        )}
                      >
                        {
                          t.categories[
                            tx.money_map_type as keyof typeof t.categories
                          ]
                        }
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
