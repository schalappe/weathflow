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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { SCORE_COLORS_HEX } from "@/lib/utils";
import type { MonthHistory } from "@/types";

interface ScoreChartProps {
  months: MonthHistory[];
}

// [>]: Chart data point with null score for missing months.
interface ChartDataPoint {
  label: string;
  score: number | null;
  scoreLabel: string | null;
  fullLabel: string;
}

// [>]: Custom tooltip matching app styling.
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
    <div className="rounded-md border bg-background p-2 shadow-md">
      <p className="font-medium">{data.fullLabel}</p>
      <p className="text-sm text-muted-foreground">
        Score: {data.score}/3 - {data.scoreLabel}
      </p>
    </div>
  );
}

// [>]: Generate last 12 months range and fill gaps with null.
function transformToChartData(months: MonthHistory[]): ChartDataPoint[] {
  // [!]: Guard against non-array input.
  if (!Array.isArray(months)) {
    console.warn("[ScoreChart] Invalid months data: expected array");
    return [];
  }

  const now = new Date();
  const result: ChartDataPoint[] = [];

  // [>]: Build lookup map for O(1) access.
  const monthMap = new Map<string, MonthHistory>();
  for (const m of months) {
    const key = `${m.year}-${m.month}`;
    monthMap.set(key, m);
  }

  // [>]: Generate 12 months going backwards from current month.
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

// [>]: Chart error fallback displayed when Recharts encounters an error.
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
    <Card>
      <CardHeader>
        <CardTitle>Score Evolution (Last 12 Months)</CardTitle>
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
                {/* [>]: Background zones for score thresholds (10% opacity). */}
                <ReferenceArea
                  y1={0}
                  y2={1}
                  fill={SCORE_COLORS_HEX[0]}
                  fillOpacity={0.1}
                />
                <ReferenceArea
                  y1={1}
                  y2={2}
                  fill={SCORE_COLORS_HEX[1]}
                  fillOpacity={0.1}
                />
                <ReferenceArea
                  y1={2}
                  y2={3}
                  fill={SCORE_COLORS_HEX[3]}
                  fillOpacity={0.1}
                />

                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 3]} ticks={[0, 1, 2, 3]} width={30} />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6", r: 4 }}
                  activeDot={{ r: 6 }}
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
