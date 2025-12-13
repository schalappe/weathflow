"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  ReferenceArea,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { SCORE_COLORS_HEX } from "@/lib/utils";
import { TrendingUp } from "lucide-react";
import type { MonthHistory } from "@/types";

interface ScoreChartProps {
  months: MonthHistory[];
}

interface ChartDataPoint {
  label: string;
  score: number | null;
  scoreLabel: string | null;
  fullLabel: string;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDataPoint }>;
}) {
  if (!active || !payload?.[0]) return null;

  const data = payload[0].payload;
  if (data.score === null) return null;

  return (
    <div className="rounded-lg border border-border/50 bg-card p-3 shadow-lg">
      <p className="font-medium">{data.fullLabel}</p>
      <p className="text-sm text-muted-foreground">
        Score:{" "}
        <span className="font-semibold text-foreground">{data.score}/3</span> -{" "}
        {data.scoreLabel}
      </p>
    </div>
  );
}

function transformToChartData(months: MonthHistory[]): ChartDataPoint[] {
  if (!Array.isArray(months)) {
    console.warn("[ScoreChart] Invalid months data: expected array");
    return [];
  }

  const now = new Date();
  const result: ChartDataPoint[] = [];

  const monthMap = new Map<string, MonthHistory>();
  for (const m of months) {
    const key = `${m.year}-${m.month}`;
    monthMap.set(key, m);
  }

  for (let i = 11; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const key = `${year}-${month}`;
    const monthData = monthMap.get(key);

    const label = date.toLocaleDateString("en-US", { month: "short" });
    const fullLabel = date.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    });

    result.push({
      label,
      score: monthData?.score ?? null,
      scoreLabel: monthData?.score_label ?? null,
      fullLabel,
    });
  }

  return result;
}

const chartErrorFallback = (
  <div
    className="flex h-[250px] items-center justify-center text-muted-foreground"
    data-testid="chart-error"
  >
    Unable to display chart
  </div>
);

export function ScoreChart({ months }: ScoreChartProps) {
  const chartData = transformToChartData(months);
  const isEmpty = chartData.every((d) => d.score === null);

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/20">
            <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <CardTitle className="text-base">Score Evolution</CardTitle>
            <CardDescription>Last 12 months performance</CardDescription>
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
              No historical data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                {/* Background zones for score thresholds */}
                <ReferenceArea
                  y1={0}
                  y2={1}
                  fill={SCORE_COLORS_HEX[0]}
                  fillOpacity={0.08}
                />
                <ReferenceArea
                  y1={1}
                  y2={2}
                  fill={SCORE_COLORS_HEX[1]}
                  fillOpacity={0.08}
                />
                <ReferenceArea
                  y1={2}
                  y2={3}
                  fill={SCORE_COLORS_HEX[3]}
                  fillOpacity={0.08}
                />

                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 3]}
                  ticks={[0, 1, 2, 3]}
                  width={30}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2.5}
                  dot={{
                    fill: "hsl(var(--primary))",
                    r: 4,
                    strokeWidth: 2,
                    stroke: "hsl(var(--card))",
                  }}
                  activeDot={{
                    r: 6,
                    fill: "hsl(var(--primary))",
                    stroke: "hsl(var(--card))",
                    strokeWidth: 2,
                  }}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
