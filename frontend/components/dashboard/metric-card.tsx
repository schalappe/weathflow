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

interface MetricCardProps {
  title: string;
  amount: number;
  percentage?: number;
  isSuccess?: boolean;
  colorClass: string;
  compoundDirection?: "positive" | "negative";
}

const CATEGORY_CONFIG: Record<
  string,
  {
    icon: React.ReactNode;
    glowClass: string;
    accentBg: string;
    accentText: string;
    target?: string;
  }
> = {
  Income: {
    icon: <Banknote className="h-5 w-5" />,
    glowClass: "metric-glow-income",
    accentBg: "bg-blue-500/10",
    accentText: "text-blue-600 dark:text-blue-400",
  },
  Core: {
    icon: <Home className="h-5 w-5" />,
    glowClass: "metric-glow-core",
    accentBg: "bg-violet-500/10",
    accentText: "text-violet-600 dark:text-violet-400",
    target: "≤ 50%",
  },
  Choice: {
    icon: <ShoppingBag className="h-5 w-5" />,
    glowClass: "metric-glow-choice",
    accentBg: "bg-amber-500/10",
    accentText: "text-amber-600 dark:text-amber-400",
    target: "≤ 30%",
  },
  Compound: {
    icon: <PiggyBank className="h-5 w-5" />,
    glowClass: "metric-glow-compound",
    accentBg: "bg-emerald-500/10",
    accentText: "text-emerald-600 dark:text-emerald-400",
    target: "≥ 20%",
  },
};

export function MetricCard({
  title,
  amount,
  percentage,
  isSuccess,
  colorClass,
  compoundDirection,
}: MetricCardProps) {
  const config = CATEGORY_CONFIG[title] || CATEGORY_CONFIG.Income;

  return (
    <Card
      className={cn(
        "group relative overflow-hidden border-0 transition-all duration-300 hover:scale-[1.02]",
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
                {title}
              </span>
              {config.target && (
                <span className="text-[10px] font-medium text-muted-foreground">
                  Target: {config.target}
                </span>
              )}
            </div>
          </div>

          {/* Threshold indicator */}
          {percentage !== undefined && isSuccess !== undefined && (
            <div
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full",
                isSuccess
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                  : "bg-red-500/10 text-red-600 dark:text-red-400",
              )}
            >
              {isSuccess ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <XCircle className="h-4 w-4" />
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
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-red-600 dark:text-red-400",
                )}
              >
                {compoundDirection === "positive" ? (
                  <>
                    <TrendingUp className="h-3 w-3" />
                    <span>Savings</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-3 w-3" />
                    <span>Withdrawal</span>
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
                  {percentage.toFixed(1)}% of income
                </span>
                {config.target && (
                  <span
                    className={cn(
                      "font-medium",
                      isSuccess
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-red-600 dark:text-red-400",
                    )}
                  >
                    {isSuccess ? "On track" : "Over target"}
                  </span>
                )}
              </div>
              {/* Progress bar */}
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    isSuccess === undefined
                      ? "bg-blue-500"
                      : isSuccess
                        ? "bg-emerald-500"
                        : "bg-red-500",
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
