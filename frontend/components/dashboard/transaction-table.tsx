"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
} from "@/lib/utils";
import type { TransactionResponse, PaginationInfo } from "@/types";

interface TransactionTableProps {
  transactions: TransactionResponse[];
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  isLoading: boolean;
}

export function TransactionTable({
  transactions,
  pagination,
  onPageChange,
  isLoading,
}: TransactionTableProps) {
  const { page, total_pages } = pagination;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
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
      </CardHeader>
      <CardContent className={cn("relative", isLoading && "opacity-50")}>
        {transactions.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No transactions
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
                <TableRow key={tx.id}>
                  <TableCell>{formatTransactionDate(tx.date)}</TableCell>
                  <TableCell className="max-w-[300px] truncate">
                    {tx.description}
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
