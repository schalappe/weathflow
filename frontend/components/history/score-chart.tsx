"use client";

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
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
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { SCORE_COLORS_HEX } from "@/lib/utils";
import { TrendingUp, Trophy, Target, AlertTriangle, XCircle } from "lucide-react";
import type { MonthHistory } from "@/types";

interface ScoreChartProps {
  months: MonthHistory[];
}

interface ChartDataPoint {
  label: string;
  score: number | null;
  scoreLabel: string | null;
  fullLabel: string;
  fill: string;
}

// [>]: Map score to color for dynamic dot coloring.
function getScoreColor(score: number | null): string {
  if (score === null) return SCORE_COLORS_HEX[0];
  if (score === 3) return SCORE_COLORS_HEX[3];
  if (score === 2) return SCORE_COLORS_HEX[2];
  if (score === 1) return SCORE_COLORS_HEX[1];
  return SCORE_COLORS_HEX[0];
}

// [>]: Map score to icon for tooltip display.
function getScoreIcon(score: number | null) {
  if (score === 3) return Trophy;
  if (score === 2) return Target;
  if (score === 1) return AlertTriangle;
  return XCircle;
}

// [>]: Line color - using a visible blue that works in both light and dark mode.
const LINE_COLOR = "#6a9bcc";

const chartConfig = {
  score: {
    label: "Score",
    color: LINE_COLOR,
  },
} satisfies ChartConfig;

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

    const score = monthData?.score ?? null;

    result.push({
      label,
      score,
      scoreLabel: monthData?.score_label ?? null,
      fullLabel,
      fill: getScoreColor(score),
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

// [>]: Custom tooltip formatter to display score details with icons.
function CustomTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDataPoint }>;
}) {
  if (!active || !payload?.[0]) return null;

  const data = payload[0].payload;
  if (data.score === null) return null;

  const Icon = getScoreIcon(data.score);
  const scoreColor = getScoreColor(data.score);

  return (
    <div className="grid min-w-[10rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="font-medium">{data.fullLabel}</div>
      <div className="flex items-center gap-2">
        <Icon
          className="h-3.5 w-3.5"
          style={{ color: scoreColor }}
        />
        <span className="text-muted-foreground">Score:</span>
        <span
          className="font-mono font-semibold tabular-nums"
          style={{ color: scoreColor }}
        >
          {data.score}/3
        </span>
        <span className="text-muted-foreground">— {data.scoreLabel}</span>
      </div>
    </div>
  );
}

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
            <ChartContainer config={chartConfig} className="aspect-auto h-[250px] w-full">
              <LineChart
                accessibilityLayer
                data={chartData}
                margin={{ left: 12, right: 12, top: 12, bottom: 12 }}
              >
                {/* [>]: Horizontal grid lines only for cleaner look. */}
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                />
                <YAxis
                  domain={[0, 3]}
                  ticks={[0, 1, 2, 3]}
                  width={30}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                />
                <ChartTooltip
                  cursor={false}
                  content={<CustomTooltipContent />}
                />
                <Line
                  dataKey="score"
                  type="natural"
                  stroke="var(--color-score)"
                  strokeWidth={2.5}
                  dot={({ cx, cy, payload }) => {
                    if (payload.score === null) return <g key={payload.label} />;
                    return (
                      <circle
                        key={payload.label}
                        cx={cx}
                        cy={cy}
                        r={5}
                        fill={payload.fill}
                        stroke="hsl(var(--background))"
                        strokeWidth={2}
                      />
                    );
                  }}
                  activeDot={{
                    r: 7,
                    stroke: "hsl(var(--background))",
                    strokeWidth: 2,
                  }}
                  connectNulls={false}
                />
              </LineChart>
            </ChartContainer>
          )}
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
