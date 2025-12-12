"use client";

import { Pencil } from "lucide-react";
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
    <Card>
      <CardHeader className="flex flex-col gap-4">
        <div className="flex flex-row items-center justify-between">
          <CardTitle>Transactions</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Page {page} of {total_pages || 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1 || isLoading}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= total_pages || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
        <TransactionFilters
          filters={filters}
          onFiltersChange={onFiltersChange}
          monthBounds={monthBounds}
          disabled={isLoading}
        />
      </CardHeader>
      <CardContent className={cn("relative", isLoading && "opacity-50")}>
        {transactions.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            {hasActiveFilters ? (
              <div className="space-y-2">
                <p>No transactions match your filters</p>
                <button
                  type="button"
                  onClick={() => onFiltersChange(DEFAULT_FILTERS)}
                  className="text-sm text-violet-600 hover:underline"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              "No transactions"
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Category</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((tx) => (
                <TableRow
                  key={tx.id}
                  onClick={() => onTransactionClick(tx)}
                  className="cursor-pointer hover:bg-slate-50"
                >
                  <TableCell>{formatTransactionDate(tx.date)}</TableCell>
                  <TableCell className="max-w-[300px]">
                    <div className="flex items-center gap-2">
                      <span className="truncate">{tx.description}</span>
                      {tx.is_manually_corrected && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Pencil className="h-3 w-3 flex-shrink-0 text-slate-400" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Manually corrected</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                  </TableCell>
                  <TableCell
                    className={cn(
                      "text-right font-medium",
                      tx.amount >= 0 ? "text-green-600" : "text-red-600",
                    )}
                  >
                    {tx.amount >= 0 ? "+" : ""}
                    {formatCurrency(tx.amount)}
                  </TableCell>
                  <TableCell>
                    {tx.money_map_type && (
                      <Badge
                        className={(() => {
                          const badgeClass =
                            CATEGORY_BADGE_CLASSES[tx.money_map_type];
                          // [!]: Log unknown category types for debugging.
                          if (!badgeClass) {
                            console.warn(
                              `[TransactionTable] Unknown category type: ${tx.money_map_type}`,
                            );
                          }
                          return badgeClass || "bg-slate-400 text-white";
                        })()}
                      >
                        {tx.money_map_type}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
