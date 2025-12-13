"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { CATEGORY_COLORS, sortMonthsChronologically, cn } from "@/lib/utils";
import { BarChart3, Home, ShoppingBag, PiggyBank } from "lucide-react";
import type { MonthHistory } from "@/types";

interface SpendingBreakdownChartProps {
  months: MonthHistory[];
  className?: string;
}

interface BreakdownChartDataPoint {
  label: string;
  fullLabel: string;
  core: number;
  choice: number;
  compound: number;
  originalCore: number;
  originalChoice: number;
  originalCompound: number;
}

const ORIGINAL_VALUE_MAP: Record<string, keyof BreakdownChartDataPoint> = {
  core: "originalCore",
  choice: "originalChoice",
  compound: "originalCompound",
};

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

  const displayLabel = payload[0]?.payload.fullLabel ?? label;

  return (
    <div className="rounded-lg border border-border/50 bg-card p-3 shadow-lg">
      <p className="font-medium mb-2">{displayLabel}</p>
      {payload.map((entry) => {
        const originalKey = ORIGINAL_VALUE_MAP[entry.dataKey];
        const displayValue = originalKey
          ? (entry.payload[originalKey] as number)
          : entry.value;
        return (
          <div key={entry.name} className="flex items-center gap-2 text-sm">
            <div
              className="h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">{entry.name}:</span>
            <span className="font-medium">{displayValue.toFixed(1)}%</span>
          </div>
        );
      })}
    </div>
  );
}

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

function normalizePercentages(
  core: number,
  choice: number,
  compound: number,
): { core: number; choice: number; compound: number } {
  if (compound < 0) {
    const totalSpending = core + choice;
    if (totalSpending === 0) return { core: 0, choice: 0, compound: 0 };
    return {
      core: (core / totalSpending) * 100,
      choice: (choice / totalSpending) * 100,
      compound: 0,
    };
  }

  const total = core + choice + compound;
  if (total === 0) return { core: 0, choice: 0, compound: 0 };
  return {
    core: (core / total) * 100,
    choice: (choice / total) * 100,
    compound: (compound / total) * 100,
  };
}

function transformToChartData(
  months: MonthHistory[],
): BreakdownChartDataPoint[] {
  if (!Array.isArray(months)) {
    console.warn(
      "[SpendingBreakdownChart] Invalid months data: expected array",
    );
    return [];
  }

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

const chartErrorFallback = (
  <div
    className="flex h-[250px] items-center justify-center text-muted-foreground"
    data-testid="chart-error"
  >
    Unable to display chart
  </div>
);

const LEGEND_ITEMS = [
  { name: "Core", color: CATEGORY_COLORS.CORE, icon: Home },
  { name: "Choice", color: CATEGORY_COLORS.CHOICE, icon: ShoppingBag },
  { name: "Compound", color: CATEGORY_COLORS.COMPOUND, icon: PiggyBank },
];

export function SpendingBreakdownChart({
  months,
  className,
}: SpendingBreakdownChartProps) {
  const chartData = transformToChartData(months);
  const isEmpty = chartData.length === 0;

  return (
    <Card className={cn("border-0 shadow-lg", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/10 to-purple-500/20">
              <BarChart3 className="h-5 w-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <CardTitle className="text-base">Spending Breakdown</CardTitle>
              <CardDescription>Monthly category distribution</CardDescription>
            </div>
          </div>
          {/* Custom Legend */}
          <div className="flex items-center gap-4">
            {LEGEND_ITEMS.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <div
                  className="h-2.5 w-2.5 rounded-sm"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-muted-foreground">
                  {item.name}
                </span>
              </div>
            ))}
          </div>
        </div>
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
              <BarChart data={chartData} barCategoryGap="20%">
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 25, 50, 75, 100]}
                  tickFormatter={(v) => `${v}%`}
                  width={40}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="core"
                  name="Core"
                  stackId="spending"
                  fill={CATEGORY_COLORS.CORE}
                  radius={[0, 0, 0, 0]}
                />
                <Bar
                  dataKey="choice"
                  name="Choice"
                  stackId="spending"
                  fill={CATEGORY_COLORS.CHOICE}
                  radius={[0, 0, 0, 0]}
                />
                <Bar
                  dataKey="compound"
                  name="Compound"
                  stackId="spending"
                  fill={CATEGORY_COLORS.COMPOUND}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
