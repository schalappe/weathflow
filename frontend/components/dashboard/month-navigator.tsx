"use client";

import { useMemo } from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatMonthDisplay, formatMonthKey } from "@/lib/utils";
import { t } from "@/lib/translations";
import type { MonthSummary } from "@/types";

interface MonthNavigatorProps {
  months: MonthSummary[];
  selectedYear: number;
  selectedMonth: number;
  onMonthChange: (year: number, month: number) => void;
  isDisabled: boolean;
}

export function MonthNavigator({
  months,
  selectedYear,
  selectedMonth,
  onMonthChange,
  isDisabled,
}: MonthNavigatorProps) {
  const currentKey = formatMonthKey(selectedYear, selectedMonth);
  const displayText = formatMonthDisplay(selectedYear, selectedMonth);

  // [>]: Build index map for O(1) lookup of previous/next months.
  const { prevMonth, nextMonth } = useMemo(() => {
    const currentIndex = months.findIndex(
      (m) => formatMonthKey(m.year, m.month) === currentKey,
    );

    // [>]: Months are sorted descending (newest first).
    // Previous month = next index, next month = previous index.
    const prev =
      currentIndex < months.length - 1 ? months[currentIndex + 1] : null;
    const next = currentIndex > 0 ? months[currentIndex - 1] : null;

    return { prevMonth: prev, nextMonth: next };
  }, [months, currentKey]);

  const handlePrevious = () => {
    if (prevMonth && !isDisabled) {
      onMonthChange(prevMonth.year, prevMonth.month);
    }
  };

  const handleNext = () => {
    if (nextMonth && !isDisabled) {
      onMonthChange(nextMonth.year, nextMonth.month);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={handlePrevious}
        disabled={isDisabled || !prevMonth}
        aria-label={t.monthNavigator.previous}
        className="shrink-0"
      >
        <ChevronLeftIcon className="size-4" />
      </Button>

      <span
        className="min-w-[140px] text-center text-sm font-medium capitalize select-none"
        aria-live="polite"
        aria-label={t.monthNavigator.label}
      >
        {displayText}
      </span>

      <Button
        variant="ghost"
        size="icon-sm"
        onClick={handleNext}
        disabled={isDisabled || !nextMonth}
        aria-label={t.monthNavigator.next}
        className="shrink-0"
      >
        <ChevronRightIcon className="size-4" />
      </Button>
    </div>
  );
}
