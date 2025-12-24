"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Banknote,
  Home,
  ShoppingBag,
  PiggyBank,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { t } from "@/lib/translations";

// [>]: Union type ensures only valid category keys are accepted at compile time.
export type CategoryKey = "Income" | "Core" | "Choice" | "Compound";

interface MetricCardProps {
  category: CategoryKey;
  amount: number;
  percentage?: number;
  isSuccess?: boolean;
  compoundDirection?: "positive" | "negative";
}

// [>]: Neutra theme category configuration with French labels.
const CATEGORY_CONFIG: Record<
  CategoryKey,
  {
    icon: React.ReactNode;
    glowClass: string;
    accentBg: string;
    accentText: string;
    target?: string;
    label: string;
  }
> = {
  Income: {
    icon: <Banknote className="h-5 w-5" />,
    glowClass: "metric-glow-income",
    accentBg: "bg-income/10",
    accentText: "text-income-text",
    label: t.metrics.Income,
  },
  Core: {
    icon: <Home className="h-5 w-5" />,
    glowClass: "metric-glow-core",
    accentBg: "bg-core/10",
    accentText: "text-core-text",
    target: "≤ 50%",
    label: t.metrics.Core,
  },
  Choice: {
    icon: <ShoppingBag className="h-5 w-5" />,
    glowClass: "metric-glow-choice",
    accentBg: "bg-choice/10",
    accentText: "text-choice-text",
    target: "≤ 30%",
    label: t.metrics.Choice,
  },
  Compound: {
    icon: <PiggyBank className="h-5 w-5" />,
    glowClass: "metric-glow-compound",
    accentBg: "bg-compound/10",
    accentText: "text-compound-text",
    target: "≥ 20%",
    label: t.metrics.Compound,
  },
};

export function MetricCard({
  category,
  amount,
  percentage,
  isSuccess,
  compoundDirection,
}: MetricCardProps) {
  const config = CATEGORY_CONFIG[category];

  return (
    <Card
      className={cn(
        "group relative overflow-hidden border-0 transition-all duration-300 hover:scale-[1.02] h-full",
        config.glowClass,
      )}
    >
      {/* Subtle gradient overlay on hover */}
      <div
        className={cn(
          "absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100",
          config.accentBg,
        )}
      />

      <CardContent className="relative p-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-lg",
                config.accentBg,
                config.accentText,
              )}
            >
              {config.icon}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-foreground">
                {config.label}
              </span>
              {config.target && (
                <span className="text-[10px] font-medium text-muted-foreground">
                  {t.metrics.target} : {config.target}
                </span>
              )}
            </div>
          </div>

          {/* Threshold indicator - Neutra theme colors */}
          {percentage !== undefined && isSuccess !== undefined && (
            <div
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full",
                isSuccess
                  ? "bg-compound/10 text-compound-text"
                  : "bg-core/10 text-core-text",
              )}
            >
              {isSuccess ? (
                <CheckCircle2
                  className="h-4 w-4"
                  aria-label={t.metrics.thresholdMet}
                />
              ) : (
                <XCircle
                  className="h-4 w-4"
                  aria-label={t.metrics.thresholdExceeded}
                />
              )}
            </div>
          )}
        </div>

        {/* Amount */}
        <div className="mt-4">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tabular-nums tracking-tight">
              {formatCurrency(amount)}
            </span>
            {compoundDirection && (
              <span
                className={cn(
                  "flex items-center gap-1 text-xs font-medium",
                  compoundDirection === "positive"
                    ? "text-compound-text"
                    : "text-core-text",
                )}
              >
                {compoundDirection === "positive" ? (
                  <>
                    <TrendingUp className="h-3 w-3" />
                    <span>{t.metrics.savings}</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-3 w-3" />
                    <span>{t.metrics.withdrawal}</span>
                  </>
                )}
              </span>
            )}
          </div>

          {/* Percentage with progress bar */}
          {percentage !== undefined && (
            <div className="mt-3 space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {percentage.toFixed(1)}% {t.metrics.ofIncome}
                </span>
                {config.target && (
                  <span
                    className={cn(
                      "font-medium",
                      isSuccess ? "text-compound-text" : "text-core-text",
                    )}
                  >
                    {isSuccess ? t.metrics.onTrack : t.metrics.overTarget}
                  </span>
                )}
              </div>
              {/* Progress bar - Neutra theme */}
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    isSuccess === undefined
                      ? "bg-income"
                      : isSuccess
                        ? "bg-compound"
                        : "bg-core",
                  )}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
