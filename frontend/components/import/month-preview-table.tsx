"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  formatCurrency,
  formatMonthDisplay,
  formatMonthKey,
  sortMonthsChronologically,
} from "@/lib/utils";
import type { MonthSummaryResponse } from "@/types";

interface MonthPreviewTableProps {
  months: MonthSummaryResponse[];
  selectedMonths: Set<string>;
  onToggleMonth: (monthKey: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  isDisabled: boolean;
}

export function MonthPreviewTable({
  months,
  selectedMonths,
  onToggleMonth,
  onSelectAll,
  onDeselectAll,
  isDisabled,
}: MonthPreviewTableProps) {
  const sortedMonths = sortMonthsChronologically(months);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-12"></TableHead>
              <TableHead>Month</TableHead>
              <TableHead className="text-right">Transactions</TableHead>
              <TableHead className="text-right">Income</TableHead>
              <TableHead className="text-right">Expenses</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedMonths.map((month) => {
              const monthKey = formatMonthKey(month.year, month.month);
              const isSelected = selectedMonths.has(monthKey);

              return (
                <TableRow
                  key={monthKey}
                  className={isSelected ? "bg-muted/50" : ""}
                >
                  <TableCell>
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => onToggleMonth(monthKey)}
                      disabled={isDisabled}
                      aria-label={`Select ${formatMonthDisplay(month.year, month.month)}`}
                    />
                  </TableCell>
                  <TableCell className="font-medium">
                    {formatMonthDisplay(month.year, month.month)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {month.transaction_count}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-blue-600 dark:text-blue-400">
                    {formatCurrency(month.total_income)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-muted-foreground">
                    {formatCurrency(-month.total_expenses)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Selection controls */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onSelectAll}
          disabled={isDisabled}
        >
          Select All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onDeselectAll}
          disabled={isDisabled}
        >
          Deselect All
        </Button>
        <span className="ml-auto text-sm text-muted-foreground">
          {selectedMonths.size} of {months.length} months selected
        </span>
      </div>
    </div>
  );
}
