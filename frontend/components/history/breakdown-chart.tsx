"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { CATEGORY_COLORS, sortMonthsChronologically, cn } from "@/lib/utils";
import type { MonthHistory } from "@/types";

interface SpendingBreakdownChartProps {
  months: MonthHistory[];
  className?: string;
}

// [>]: Chart data point with percentage values for stacked bars.
interface BreakdownChartDataPoint {
  label: string;
  fullLabel: string;
  core: number;
  choice: number;
  compound: number;
  // [>]: Original values preserved for tooltip display.
  originalCore: number;
  originalChoice: number;
  originalCompound: number;
}

// [>]: Map dataKey to original value field for tooltip display.
const ORIGINAL_VALUE_MAP: Record<string, keyof BreakdownChartDataPoint> = {
  core: "originalCore",
  choice: "originalChoice",
  compound: "originalCompound",
};

// [>]: Custom tooltip matching app styling, shows original percentages.
function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    dataKey: string;
    color: string;
    payload: BreakdownChartDataPoint;
  }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  // [>]: Access fullLabel from first payload item's data.
  const displayLabel = payload[0]?.payload.fullLabel ?? label;

  return (
    <div className="rounded-md border bg-background p-2 shadow-md">
      <p className="font-medium">{displayLabel}</p>
      {payload.map((entry) => {
        // [>]: Use original value for display, not normalized value.
        const originalKey = ORIGINAL_VALUE_MAP[entry.dataKey];
        const displayValue = originalKey
          ? (entry.payload[originalKey] as number)
          : entry.value;
        return (
          <div key={entry.name} className="flex items-center gap-2 text-sm">
            <div
              className="h-3 w-3 rounded"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">
              {entry.name}: {displayValue.toFixed(1)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

// [>]: Validate month data has required numeric properties.
function isValidMonthData(m: MonthHistory): boolean {
  return (
    typeof m?.year === "number" &&
    typeof m?.month === "number" &&
    m.month >= 1 &&
    m.month <= 12 &&
    typeof m?.core_percentage === "number" &&
    typeof m?.choice_percentage === "number" &&
    typeof m?.compound_percentage === "number"
  );
}

// [>]: Normalize percentages for stacked bar display when compound is negative.
function normalizePercentages(
  core: number,
  choice: number,
  compound: number,
): { core: number; choice: number; compound: number } {
  // [>]: When compound is negative, spending exceeds income.
  // Normalize to show relative proportions of spending categories.
  if (compound < 0) {
    // [>]: Use absolute values of spending categories only.
    const totalSpending = core + choice;
    if (totalSpending === 0) return { core: 0, choice: 0, compound: 0 };
    return {
      core: (core / totalSpending) * 100,
      choice: (choice / totalSpending) * 100,
      compound: 0,
    };
  }

  // [>]: Normal case: all positive, sum to ~100%.
  const total = core + choice + compound;
  if (total === 0) return { core: 0, choice: 0, compound: 0 };
  return {
    core: (core / total) * 100,
    choice: (choice / total) * 100,
    compound: (compound / total) * 100,
  };
}

// [>]: Filter empty months, sort chronologically, map to chart format.
function transformToChartData(
  months: MonthHistory[],
): BreakdownChartDataPoint[] {
  // [!]: Guard against non-array input.
  if (!Array.isArray(months)) {
    console.warn(
      "[SpendingBreakdownChart] Invalid months data: expected array",
    );
    return [];
  }

  // [>]: Filter out invalid months and months where all percentages are zero.
  const validMonths = months.filter((m) => {
    if (!isValidMonthData(m)) {
      console.warn("[SpendingBreakdownChart] Skipping invalid month data:", m);
      return false;
    }
    return (
      m.core_percentage !== 0 ||
      m.choice_percentage !== 0 ||
      m.compound_percentage !== 0
    );
  });

  const sorted = sortMonthsChronologically(validMonths);

  return sorted.map((m) => {
    const date = new Date(m.year, m.month - 1);
    const normalized = normalizePercentages(
      m.core_percentage,
      m.choice_percentage,
      m.compound_percentage,
    );
    return {
      label: date.toLocaleDateString("en-US", { month: "short" }),
      fullLabel: date.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      }),
      core: normalized.core,
      choice: normalized.choice,
      compound: normalized.compound,
      originalCore: m.core_percentage,
      originalChoice: m.choice_percentage,
      originalCompound: m.compound_percentage,
    };
  });
}

// [>]: Chart error fallback displayed when Recharts encounters an error.
const chartErrorFallback = (
  <div
    className="flex h-[250px] items-center justify-center text-muted-foreground"
    data-testid="chart-error"
  >
    Unable to display chart
  </div>
);

export function SpendingBreakdownChart({
  months,
  className,
}: SpendingBreakdownChartProps) {
  const chartData = transformToChartData(months);
  const isEmpty = chartData.length === 0;

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle>Spending Breakdown by Month</CardTitle>
      </CardHeader>
      <CardContent>
        <ErrorBoundary fallback={chartErrorFallback}>
          {isEmpty ? (
            <div
              className="flex h-[250px] items-center justify-center text-muted-foreground"
              data-testid="empty-state"
            >
              No spending data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 25, 50, 75, 100]}
                  tickFormatter={(v) => `${v}%`}
                  width={40}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar
                  dataKey="core"
                  name="Core"
                  stackId="spending"
                  fill={CATEGORY_COLORS.CORE}
                />
                <Bar
                  dataKey="choice"
                  name="Choice"
                  stackId="spending"
                  fill={CATEGORY_COLORS.CHOICE}
                />
                <Bar
                  dataKey="compound"
                  name="Compound"
                  stackId="spending"
                  fill={CATEGORY_COLORS.COMPOUND}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
