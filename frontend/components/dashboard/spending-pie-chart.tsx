"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CATEGORY_COLORS, formatCurrency, cn } from "@/lib/utils";
import { Home, ShoppingBag, PiggyBank } from "lucide-react";

interface SpendingPieChartProps {
  core: number;
  choice: number;
  compound: number;
}

const CATEGORY_ICONS = {
  Core: Home,
  Choice: ShoppingBag,
  Compound: PiggyBank,
};

export function SpendingPieChart({
  core,
  choice,
  compound,
}: SpendingPieChartProps) {
  const data = [
    { name: "Core", value: Math.abs(core), color: CATEGORY_COLORS.CORE },
    { name: "Choice", value: Math.abs(choice), color: CATEGORY_COLORS.CHOICE },
    {
      name: "Compound",
      value: Math.abs(compound),
      color: CATEGORY_COLORS.COMPOUND,
    },
  ];

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const isEmpty = total === 0;

  return (
    <Card className="border-0 metric-glow-core h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">
          Spending Distribution
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <div
            className="flex h-[280px] items-center justify-center text-muted-foreground"
            data-testid="empty-state"
          >
            No spending data available
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {/* Chart */}
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  cornerRadius={4}
                >
                  {data.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      className="transition-all duration-300 hover:opacity-80"
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                  itemStyle={{
                    color: "hsl(var(--foreground))",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>

            {/* Custom Legend */}
            <div className="flex flex-col gap-2">
              {data.map((item) => {
                const Icon =
                  CATEGORY_ICONS[item.name as keyof typeof CATEGORY_ICONS];
                const percentage =
                  total > 0 ? ((item.value / total) * 100).toFixed(1) : "0";
                return (
                  <div
                    key={item.name}
                    className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2 transition-colors hover:bg-muted"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="flex h-6 w-6 items-center justify-center rounded"
                        style={{ backgroundColor: `${item.color}20` }}
                      >
                        <Icon
                          className="h-3.5 w-3.5"
                          style={{ color: item.color }}
                        />
                      </div>
                      <span className="text-sm font-medium">{item.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm tabular-nums text-muted-foreground">
                        {percentage}%
                      </span>
                      <span className="text-sm font-semibold tabular-nums">
                        {formatCurrency(item.value)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
