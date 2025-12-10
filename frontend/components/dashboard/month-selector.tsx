"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatMonthDisplay, formatMonthKey } from "@/lib/utils";
import type { MonthSummary } from "@/types";

interface MonthSelectorProps {
  months: MonthSummary[];
  selectedYear: number;
  selectedMonth: number;
  onMonthChange: (year: number, month: number) => void;
  isDisabled: boolean;
}

export function MonthSelector({
  months,
  selectedYear,
  selectedMonth,
  onMonthChange,
  isDisabled,
}: MonthSelectorProps) {
  const currentValue = formatMonthKey(selectedYear, selectedMonth);

  const handleValueChange = (value: string) => {
    const parts = value.split("-");
    const year = Number(parts[0]);
    const month = Number(parts[1]);

    // [!]: Guard against malformed values propagating NaN to parent.
    if (isNaN(year) || isNaN(month) || year < 1900 || month < 1 || month > 12) {
      console.error(`[MonthSelector] Invalid month value format: "${value}"`);
      return;
    }

    onMonthChange(year, month);
  };

  return (
    <Select
      value={currentValue}
      onValueChange={handleValueChange}
      disabled={isDisabled}
    >
      <SelectTrigger className="w-[180px]" aria-label="Select month">
        <SelectValue placeholder="Select month" />
      </SelectTrigger>
      <SelectContent>
        {months.map((m) => (
          <SelectItem
            key={formatMonthKey(m.year, m.month)}
            value={formatMonthKey(m.year, m.month)}
          >
            {formatMonthDisplay(m.year, m.month)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
