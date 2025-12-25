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
  type ChartConfig,
} from "@/components/ui/chart";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { SCORE_COLORS_HEX, sortMonthsChronologically } from "@/lib/utils";
import { t } from "@/lib/translations";
import {
  TrendingUp,
  Trophy,
  Target,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import type { MonthHistory } from "@/types";

interface ScoreChartProps {
  months: MonthHistory[];
  period: number;
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

// [>]: Render score icon based on score value.
function ScoreIcon({
  score,
  className,
  style,
}: {
  score: number | null;
  className?: string;
  style?: React.CSSProperties;
}) {
  if (score === 3) return <Trophy className={className} style={style} />;
  if (score === 2) return <Target className={className} style={style} />;
  if (score === 1) return <AlertTriangle className={className} style={style} />;
  return <XCircle className={className} style={style} />;
}

// [>]: Line color - neutral slate that doesn't compete with score-colored dots.
// The dots provide the meaningful color (green=great, red=poor), line is just connective tissue.
const LINE_COLOR = "#64748b";

const chartConfig = {
  score: {
    label: t.scoreChart.tooltipScore,
    color: LINE_COLOR,
  },
} satisfies ChartConfig;

// [>]: Validate month data has required fields for score chart.
function isValidMonthData(m: MonthHistory): boolean {
  return (
    typeof m?.year === "number" &&
    typeof m?.month === "number" &&
    m.month >= 1 &&
    m.month <= 12 &&
    typeof m?.score === "number"
  );
}

// [>]: Data-driven transformation - only display months that exist in the data.
function transformToChartData(months: MonthHistory[]): ChartDataPoint[] {
  if (!Array.isArray(months)) {
    console.warn("[ScoreChart] Invalid months data: expected array");
    return [];
  }

  const validMonths = months.filter((m) => {
    if (!isValidMonthData(m)) {
      console.warn("[ScoreChart] Skipping invalid month data:", m);
      return false;
    }
    return true;
  });

  const sorted = sortMonthsChronologically(validMonths);

  return sorted.map((m) => {
    const date = new Date(m.year, m.month - 1);
    const label = date.toLocaleDateString("fr-FR", { month: "short" });
    const fullLabel = date.toLocaleDateString("fr-FR", {
      month: "long",
      year: "numeric",
    });

    return {
      label,
      score: m.score,
      scoreLabel: m.score_label ?? null,
      fullLabel,
      fill: getScoreColor(m.score),
    };
  });
}

const chartErrorFallback = (
  <div
    className="flex h-[250px] items-center justify-center text-muted-foreground"
    data-testid="chart-error"
  >
    {t.scoreChart.error}
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

  const scoreColor = getScoreColor(data.score);

  return (
    <div className="grid min-w-[10rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="font-medium">{data.fullLabel}</div>
      <div className="flex items-center gap-2">
        <ScoreIcon
          score={data.score}
          className="h-3.5 w-3.5"
          style={{ color: scoreColor }}
        />
        <span className="text-muted-foreground">
          {t.scoreChart.tooltipScore} :
        </span>
        <span
          className="font-mono font-semibold tabular-nums"
          style={{ color: scoreColor }}
        >
          {data.score}/3
        </span>
        <span className="text-muted-foreground">
          —{" "}
          {t.score.labels[data.scoreLabel as keyof typeof t.score.labels] ||
            data.scoreLabel}
        </span>
      </div>
    </div>
  );
}

// [>]: Generate subtitle based on period selection. Valid periods: 3, 6, 12.
function getPeriodDescription(period: number): string {
  return t.scoreChart.lastMonths.replace("{n}", String(period));
}

export function ScoreChart({ months, period }: ScoreChartProps) {
  const chartData = transformToChartData(months);
  const isEmpty = chartData.length === 0;

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-500/10 to-slate-600/20">
            <TrendingUp className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </div>
          <div>
            <CardTitle className="text-base">{t.scoreChart.title}</CardTitle>
            <CardDescription>{getPeriodDescription(period)}</CardDescription>
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
              {t.scoreChart.empty}
            </div>
          ) : (
            <ChartContainer
              config={chartConfig}
              className="aspect-auto h-[250px] w-full"
            >
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
                  type="monotone"
                  stroke="var(--color-score)"
                  strokeWidth={2}
                  dot={({ cx, cy, payload }) => {
                    if (payload.score === null)
                      return <g key={payload.label} />;
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
