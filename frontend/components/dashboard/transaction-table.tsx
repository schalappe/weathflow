"use client";

import { Pencil, ChevronLeft, ChevronRight, Receipt } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  formatCurrency,
  formatTransactionDate,
  CATEGORY_BADGE_CLASSES,
  cn,
  getActiveFilterCount,
} from "@/lib/utils";
import {
  TransactionFilters,
  getMonthBounds,
} from "@/components/dashboard/transaction-filters";
import type {
  TransactionResponse,
  PaginationInfo,
  TransactionFilters as TFilters,
} from "@/types";
import { DEFAULT_FILTERS } from "@/types";

interface TransactionTableProps {
  transactions: TransactionResponse[];
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  onTransactionClick: (transaction: TransactionResponse) => void;
  isLoading: boolean;
  filters: TFilters;
  onFiltersChange: (filters: TFilters) => void;
  selectedMonth: { year: number; month: number };
}

const CATEGORY_STYLES: Record<string, { bg: string; text: string }> = {
  INCOME: {
    bg: "bg-blue-500/10 hover:bg-blue-500/20",
    text: "text-blue-700 dark:text-blue-300",
  },
  CORE: {
    bg: "bg-violet-500/10 hover:bg-violet-500/20",
    text: "text-violet-700 dark:text-violet-300",
  },
  CHOICE: {
    bg: "bg-amber-500/10 hover:bg-amber-500/20",
    text: "text-amber-700 dark:text-amber-300",
  },
  COMPOUND: {
    bg: "bg-emerald-500/10 hover:bg-emerald-500/20",
    text: "text-emerald-700 dark:text-emerald-300",
  },
  EXCLUDED: {
    bg: "bg-gray-500/10 hover:bg-gray-500/20",
    text: "text-gray-600 dark:text-gray-400",
  },
};

export function TransactionTable({
  transactions,
  pagination,
  onPageChange,
  onTransactionClick,
  isLoading,
  filters,
  onFiltersChange,
  selectedMonth,
}: TransactionTableProps) {
  const { page, total_pages } = pagination;
  const monthBounds = getMonthBounds(selectedMonth.year, selectedMonth.month);
  const hasActiveFilters = getActiveFilterCount(filters) > 0;

  return (
    <Card className="border-0 shadow-sm h-full flex flex-col">
      <CardHeader className="flex flex-col gap-4 pb-4">
        <div className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <Receipt className="h-4.5 w-4.5 text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">
                Transactions
              </CardTitle>
              <span className="text-xs text-muted-foreground">
                {pagination.total || 0} total
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground tabular-nums">
              {page} / {total_pages || 1}
            </span>
            <div className="flex items-center rounded-lg border border-border/50 bg-muted/30">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-r-none"
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1 || isLoading}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="h-4 w-px bg-border/50" />
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-l-none"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= total_pages || isLoading}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <TransactionFilters
          filters={filters}
          onFiltersChange={onFiltersChange}
          monthBounds={monthBounds}
          disabled={isLoading}
        />
      </CardHeader>
      <CardContent
        className={cn(
          "relative flex-1 overflow-auto",
          isLoading && "opacity-50",
        )}
      >
        {transactions.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Receipt className="h-6 w-6 text-muted-foreground" />
            </div>
            {hasActiveFilters ? (
              <>
                <p className="text-sm text-muted-foreground">
                  No transactions match your filters
                </p>
                <button
                  type="button"
                  onClick={() => onFiltersChange(DEFAULT_FILTERS)}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  Clear all filters
                </button>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No transactions</p>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[70px] text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Date
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Description
                </TableHead>
                <TableHead className="w-[100px] text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Amount
                </TableHead>
                <TableHead className="w-[110px] text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Category
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((tx) => {
                const categoryStyle = tx.money_map_type
                  ? CATEGORY_STYLES[tx.money_map_type] ||
                    CATEGORY_STYLES.EXCLUDED
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
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm">
                          {tx.description}
                        </span>
                        {tx.is_manually_corrected && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded bg-amber-500/10">
                                  <Pencil className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Manually corrected</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="py-3 text-right">
                      <span
                        className={cn(
                          "font-mono text-sm font-semibold tabular-nums",
                          tx.amount >= 0
                            ? "text-emerald-600 dark:text-emerald-400"
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
                          {tx.money_map_type}
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
