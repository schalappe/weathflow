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
  compoundDirection?: "positive" | "negative";
}

// [>]: Neutra theme category configuration.
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
    accentBg: "bg-[#6a9bcc]/10",
    accentText: "text-[#6a9bcc] dark:text-[#7aa8d4]",
  },
  Core: {
    icon: <Home className="h-5 w-5" />,
    glowClass: "metric-glow-core",
    accentBg: "bg-[#d97757]/10",
    accentText: "text-[#d97757] dark:text-[#e08363]",
    target: "≤ 50%",
  },
  Choice: {
    icon: <ShoppingBag className="h-5 w-5" />,
    glowClass: "metric-glow-choice",
    accentBg: "bg-[#e8b931]/10",
    accentText: "text-[#c9a02a] dark:text-[#f0c43d]",
    target: "≤ 30%",
  },
  Compound: {
    icon: <PiggyBank className="h-5 w-5" />,
    glowClass: "metric-glow-compound",
    accentBg: "bg-[#788c5d]/10",
    accentText: "text-[#788c5d] dark:text-[#8a9e6a]",
    target: "≥ 20%",
  },
};

export function MetricCard({
  title,
  amount,
  percentage,
  isSuccess,
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

          {/* Threshold indicator - Neutra theme colors */}
          {percentage !== undefined && isSuccess !== undefined && (
            <div
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full",
                isSuccess
                  ? "bg-[#788c5d]/10 text-[#788c5d] dark:text-[#8a9e6a]"
                  : "bg-[#d97757]/10 text-[#d97757] dark:text-[#e08363]",
              )}
            >
              {isSuccess ? (
                <CheckCircle2 className="h-4 w-4" aria-label="Threshold met" />
              ) : (
                <XCircle className="h-4 w-4" aria-label="Threshold exceeded" />
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
                    ? "text-[#788c5d] dark:text-[#8a9e6a]"
                    : "text-[#d97757] dark:text-[#e08363]",
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
                        ? "text-[#788c5d] dark:text-[#8a9e6a]"
                        : "text-[#d97757] dark:text-[#e08363]",
                    )}
                  >
                    {isSuccess ? "On track" : "Over target"}
                  </span>
                )}
              </div>
              {/* Progress bar - Neutra theme */}
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    isSuccess === undefined
                      ? "bg-[#6a9bcc]"
                      : isSuccess
                        ? "bg-[#788c5d]"
                        : "bg-[#d97757]",
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
