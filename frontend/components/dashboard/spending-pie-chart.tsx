"use client";

import * as React from "react";
import { Label, Pie, PieChart, Sector } from "recharts";
import { type PieSectorDataItem } from "recharts/types/polar/Pie";
import { Home, ShoppingBag, PiggyBank } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartStyle,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CATEGORY_COLORS, formatCurrency } from "@/lib/utils";
import { t } from "@/lib/translations";

interface SpendingPieChartProps {
  core: number;
  choice: number;
  compound: number;
}

// [>]: Chart configuration with Money Map category colors and icons.
const chartConfig = {
  amount: {
    label: t.spendingChart.amount,
  },
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

type CategoryKey = "core" | "choice" | "compound";

export function SpendingPieChart({
  core,
  choice,
  compound,
}: SpendingPieChartProps) {
  const id = "spending-distribution";

  // [>]: Build chart data with absolute values and fill colors.
  const chartData = React.useMemo(
    () => [
      {
        category: "core" as CategoryKey,
        amount: Math.abs(core),
        fill: "var(--color-core)",
      },
      {
        category: "choice" as CategoryKey,
        amount: Math.abs(choice),
        fill: "var(--color-choice)",
      },
      {
        category: "compound" as CategoryKey,
        amount: Math.abs(compound),
        fill: "var(--color-compound)",
      },
    ],
    [core, choice, compound],
  );

  const total = chartData.reduce((sum, item) => sum + item.amount, 0);
  const isEmpty = total === 0;

  // [>]: Default to the category with the highest amount.
  const defaultCategory = React.useMemo(() => {
    if (isEmpty) return "core";
    const maxItem = chartData.reduce((max, item) =>
      item.amount > max.amount ? item : max,
    );
    return maxItem.category;
  }, [chartData, isEmpty]);

  const [activeCategory, setActiveCategory] =
    React.useState<CategoryKey>(defaultCategory);

  const activeIndex = React.useMemo(
    () => chartData.findIndex((item) => item.category === activeCategory),
    [activeCategory, chartData],
  );

  const categories = React.useMemo(
    () => chartData.map((item) => item.category),
    [chartData],
  );

  // [>]: Calculate percentage for center label.
  const activePercentage = React.useMemo(() => {
    if (total === 0) return "0";
    return (((chartData[activeIndex]?.amount || 0) / total) * 100).toFixed(1);
  }, [chartData, activeIndex, total]);

  return (
    <Card
      data-chart={id}
      className="flex flex-col border-0 metric-glow-core h-full"
    >
      <ChartStyle id={id} config={chartConfig} />
      <CardHeader className="flex-row items-start space-y-0 pb-0">
        <div className="grid gap-1">
          <CardTitle className="text-base font-semibold">
            {t.spendingChart.title}
          </CardTitle>
        </div>
        {!isEmpty && (
          <Select
            value={activeCategory}
            onValueChange={(value) => setActiveCategory(value as CategoryKey)}
          >
            <SelectTrigger
              className="ml-auto h-7 w-[120px] rounded-lg pl-2.5"
              aria-label={t.spendingChart.selectCategory}
            >
              <SelectValue placeholder={t.spendingChart.selectCategory} />
            </SelectTrigger>
            <SelectContent align="end" className="rounded-xl">
              {categories.map((key) => {
                const config = chartConfig[key];
                if (!config) return null;

                return (
                  <SelectItem
                    key={key}
                    value={key}
                    className="rounded-lg [&_span]:flex"
                  >
                    <div className="flex items-center gap-2 text-xs">
                      <span
                        className="flex h-3 w-3 shrink-0 rounded-sm"
                        style={{
                          backgroundColor: config.color,
                        }}
                      />
                      {config.label}
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        )}
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-center pb-4">
        {isEmpty ? (
          <div
            className="flex h-[280px] items-center justify-center text-muted-foreground"
            data-testid="empty-state"
          >
            {t.spendingChart.empty}
          </div>
        ) : (
          <ChartContainer
            id={id}
            config={chartConfig}
            className="mx-auto aspect-square w-full max-w-[280px] min-h-[250px]"
          >
            <PieChart>
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    hideLabel
                    formatter={(value) => formatCurrency(value as number)}
                  />
                }
              />
              <Pie
                data={chartData}
                dataKey="amount"
                nameKey="category"
                innerRadius={60}
                outerRadius={85}
                strokeWidth={5}
                activeIndex={activeIndex}
                activeShape={({
                  outerRadius = 0,
                  ...props
                }: PieSectorDataItem) => (
                  <g>
                    <Sector {...props} outerRadius={outerRadius + 10} />
                    <Sector
                      {...props}
                      outerRadius={outerRadius + 22}
                      innerRadius={outerRadius + 12}
                    />
                  </g>
                )}
              >
                <Label
                  content={({ viewBox }) => {
                    if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                      return (
                        <text
                          x={viewBox.cx}
                          y={viewBox.cy}
                          textAnchor="middle"
                          dominantBaseline="middle"
                        >
                          <tspan
                            x={viewBox.cx}
                            y={viewBox.cy}
                            className="fill-foreground text-2xl font-bold"
                          >
                            {activePercentage}%
                          </tspan>
                          <tspan
                            x={viewBox.cx}
                            y={(viewBox.cy || 0) + 22}
                            className="fill-muted-foreground text-sm"
                          >
                            {chartConfig[activeCategory]?.label}
                          </tspan>
                        </text>
                      );
                    }
                  }}
                />
              </Pie>
            </PieChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
