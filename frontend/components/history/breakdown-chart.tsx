"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  type ChartConfig,
} from "@/components/ui/chart";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { CATEGORY_COLORS, sortMonthsChronologically, cn } from "@/lib/utils";
import { t } from "@/lib/translations";
import { TrendingDown, Home, ShoppingBag, PiggyBank } from "lucide-react";
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

// [>]: Chart config with icons for tooltip display.
const chartConfig = {
  core: {
    label: t.metrics.Core,
    color: CATEGORY_COLORS.CORE,
    icon: Home,
  },
  choice: {
    label: t.metrics.Choice,
    color: CATEGORY_COLORS.CHOICE,
    icon: ShoppingBag,
  },
  compound: {
    label: t.metrics.Compound,
    color: CATEGORY_COLORS.COMPOUND,
    icon: PiggyBank,
  },
} satisfies ChartConfig;

const LEGEND_ITEMS = [
  { name: t.metrics.Core, color: CATEGORY_COLORS.CORE, icon: Home },
  { name: t.metrics.Choice, color: CATEGORY_COLORS.CHOICE, icon: ShoppingBag },
  {
    name: t.metrics.Compound,
    color: CATEGORY_COLORS.COMPOUND,
    icon: PiggyBank,
  },
];

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
      label: date.toLocaleDateString("fr-FR", { month: "short" }),
      fullLabel: date.toLocaleDateString("fr-FR", {
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
    {t.breakdownChart.error}
  </div>
);

// [>]: Custom tooltip with icons matching the category colors.
function CustomTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    dataKey: string;
    color: string;
    payload: BreakdownChartDataPoint;
  }>;
}) {
  if (!active || !payload?.length) return null;

  const data = payload[0]?.payload;
  if (!data) return null;

  const categories = [
    {
      key: "core",
      label: t.metrics.Core,
      icon: Home,
      color: CATEGORY_COLORS.CORE,
      value: data.originalCore,
    },
    {
      key: "choice",
      label: t.metrics.Choice,
      icon: ShoppingBag,
      color: CATEGORY_COLORS.CHOICE,
      value: data.originalChoice,
    },
    {
      key: "compound",
      label: t.metrics.Compound,
      icon: PiggyBank,
      color: CATEGORY_COLORS.COMPOUND,
      value: data.originalCompound,
    },
  ];

  return (
    <div className="grid min-w-[10rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="font-medium">{data.fullLabel}</div>
      <div className="grid gap-1">
        {categories.map(({ key, label, icon: Icon, color, value }) => (
          <div key={key} className="flex items-center gap-2">
            <Icon className="h-3.5 w-3.5" style={{ color }} />
            <span className="text-muted-foreground">{label}:</span>
            <span className="font-mono font-medium tabular-nums text-foreground">
              {value.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

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
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#d97757]/10 to-[#e8b931]/20">
              <TrendingDown className="h-5 w-5 text-core-text" />
            </div>
            <div>
              <CardTitle className="text-base">
                {t.breakdownChart.title}
              </CardTitle>
              <CardDescription>{t.breakdownChart.subtitle}</CardDescription>
            </div>
          </div>
          {/* [>]: Custom legend with icons matching the chart. */}
          <div className="flex items-center gap-4">
            {LEGEND_ITEMS.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <item.icon
                  className="h-3.5 w-3.5"
                  style={{ color: item.color }}
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
              {t.breakdownChart.empty}
            </div>
          ) : (
            <ChartContainer
              config={chartConfig}
              className="aspect-auto h-[250px] w-full"
            >
              <AreaChart
                accessibilityLayer
                data={chartData}
                margin={{ left: 12, right: 12, top: 12, bottom: 12 }}
                stackOffset="expand"
              >
                {/* [>]: Horizontal grid lines only for cleaner look. */}
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                />
                <YAxis
                  domain={[0, 1]}
                  ticks={[0, 0.25, 0.5, 0.75, 1]}
                  tickFormatter={(v) => `${Math.round(v * 100)}%`}
                  width={40}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                />
                <ChartTooltip
                  cursor={{
                    stroke: "hsl(var(--muted-foreground))",
                    strokeDasharray: "3 3",
                  }}
                  content={<CustomTooltipContent />}
                />
                <Area
                  dataKey="core"
                  name="Core"
                  stackId="spending"
                  type="monotone"
                  fill="var(--color-core)"
                  fillOpacity={0.7}
                  stroke="var(--color-core)"
                  strokeWidth={2}
                />
                <Area
                  dataKey="choice"
                  name="Choice"
                  stackId="spending"
                  type="monotone"
                  fill="var(--color-choice)"
                  fillOpacity={0.7}
                  stroke="var(--color-choice)"
                  strokeWidth={2}
                />
                <Area
                  dataKey="compound"
                  name="Compound"
                  stackId="spending"
                  type="monotone"
                  fill="var(--color-compound)"
                  fillOpacity={0.7}
                  stroke="var(--color-compound)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ChartContainer>
          )}
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
