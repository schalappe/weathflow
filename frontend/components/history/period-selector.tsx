"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface PeriodSelectorProps {
  value: number;
  onChange: (months: number) => void;
  disabled?: boolean;
}

// [>]: Period options with French labels and numeric values. 12 months max for performance.
const PERIOD_OPTIONS = [
  { label: "3 mois", value: 3 },
  { label: "6 mois", value: 6 },
  { label: "12 mois", value: 12 },
] as const;

export function PeriodSelector({
  value,
  onChange,
  disabled = false,
}: PeriodSelectorProps) {
  return (
    <Select
      value={value.toString()}
      onValueChange={(v) => {
        const numValue = Number(v);
        const isValidPeriod = PERIOD_OPTIONS.some(
          (opt) => opt.value === numValue,
        );
        if (!isValidPeriod) {
          console.warn(`[PeriodSelector] Unexpected value received: "${v}"`);
          return;
        }
        onChange(numValue);
      }}
      disabled={disabled}
    >
      <SelectTrigger className="w-[120px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {PERIOD_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value.toString()}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
