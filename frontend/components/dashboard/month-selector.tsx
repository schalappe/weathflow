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
    const [year, month] = value.split("-").map(Number);
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
