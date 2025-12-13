"use client";

import { Pencil, ChevronLeft, ChevronRight, Receipt } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
  cn,
  getActiveFilterCount,
} from "@/lib/utils";
import { t } from "@/lib/translations";
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

// [>]: Neutra theme category styles.
const CATEGORY_STYLES: Record<string, { bg: string; text: string }> = {
  INCOME: {
    bg: "bg-[#6a9bcc]/10 hover:bg-[#6a9bcc]/20",
    text: "text-[#5a8ab8] dark:text-[#7aa8d4]",
  },
  CORE: {
    bg: "bg-[#d97757]/10 hover:bg-[#d97757]/20",
    text: "text-[#c46647] dark:text-[#e08363]",
  },
  CHOICE: {
    bg: "bg-[#e8b931]/10 hover:bg-[#e8b931]/20",
    text: "text-[#c9a02a] dark:text-[#f0c43d]",
  },
  COMPOUND: {
    bg: "bg-[#788c5d]/10 hover:bg-[#788c5d]/20",
    text: "text-[#6a7d50] dark:text-[#8a9e6a]",
  },
  EXCLUDED: {
    bg: "bg-[#b0aea5]/10 hover:bg-[#b0aea5]/20",
    text: "text-[#8a8880] dark:text-[#b0aea5]",
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
      <CardHeader className="pb-4">
        {/* [>]: Three-column grid layout for perfect centering: Title (left) | Filters (center) | Pagination (right). */}
        <div className="flex flex-col gap-4 lg:grid lg:grid-cols-[auto_1fr_auto] lg:items-center lg:gap-4">
          {/* [>]: Left section - Title with icon and count. */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <Receipt className="h-4.5 w-4.5 text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">
                {t.transactions.title}
              </CardTitle>
              <span className="text-xs text-muted-foreground">
                {pagination.total_items || 0} {t.transactions.total}
              </span>
            </div>
          </div>

          {/* [>]: Center section - Filters (perfectly centered in the grid). */}
          <div className="flex justify-center">
            <TransactionFilters
              filters={filters}
              onFiltersChange={onFiltersChange}
              monthBounds={monthBounds}
              disabled={isLoading}
            />
          </div>

          {/* [>]: Right section - Pagination controls (aligned to the far right). */}
          <div className="flex items-center justify-end gap-2">
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
                  {t.transactions.noMatch}
                </p>
                <button
                  type="button"
                  onClick={() => onFiltersChange(DEFAULT_FILTERS)}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  {t.transactions.clearFilters}
                </button>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">{t.transactions.empty}</p>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
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
                                <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded bg-[#e8b931]/10">
                                  <Pencil className="h-3 w-3 text-[#c9a02a] dark:text-[#f0c43d]" />
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{t.transactions.manuallyCorrected}</p>
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
                            ? "text-[#788c5d] dark:text-[#8a9e6a]"
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
                          {t.categories[tx.money_map_type as keyof typeof t.categories]}
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
