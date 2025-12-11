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
}

// [>]: Custom tooltip matching app styling.
function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
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
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-sm">
          <div
            className="h-3 w-3 rounded"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">
            {entry.name}: {entry.value.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}

// [>]: Filter empty months, sort chronologically, map to chart format.
function transformToChartData(
  months: MonthHistory[],
): BreakdownChartDataPoint[] {
  // [>]: Filter out months where all percentages are zero.
  const validMonths = months.filter(
    (m) =>
      m.core_percentage !== 0 ||
      m.choice_percentage !== 0 ||
      m.compound_percentage !== 0,
  );

  // [>]: Sort chronologically (oldest first).
  const sorted = sortMonthsChronologically(validMonths);

  // [>]: Transform to chart data points.
  return sorted.map((m) => {
    const date = new Date(m.year, m.month - 1);
    return {
      label: date.toLocaleDateString("en-US", { month: "short" }),
      fullLabel: date.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      }),
      core: m.core_percentage,
      choice: m.choice_percentage,
      compound: m.compound_percentage,
    };
  });
}

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
      </CardContent>
    </Card>
  );
}
