"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, X, TrendingUp, TrendingDown } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  amount: number;
  percentage?: number;
  isSuccess?: boolean;
  colorClass: string;
  // [>]: Optional indicator for Compound category to show savings vs withdrawal.
  compoundDirection?: "positive" | "negative";
}

export function MetricCard({
  title,
  amount,
  percentage,
  isSuccess,
  colorClass,
  compoundDirection,
}: MetricCardProps) {
  return (
    <Card className={cn("border-l-4", colorClass)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold">{formatCurrency(amount)}</span>
          {compoundDirection && (
            <span
              className={cn(
                "flex items-center gap-1 text-xs font-medium",
                compoundDirection === "positive"
                  ? "text-green-600"
                  : "text-red-600",
              )}
            >
              {compoundDirection === "positive" ? (
                <>
                  <TrendingUp className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Savings</span>
                </>
              ) : (
                <>
                  <TrendingDown className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Withdrawal</span>
                </>
              )}
            </span>
          )}
        </div>
        {percentage !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {percentage.toFixed(1)}%
            </span>
            {isSuccess !== undefined &&
              (isSuccess ? (
                <Check
                  className="h-4 w-4 text-green-500"
                  aria-label="Threshold met"
                />
              ) : (
                <X
                  className="h-4 w-4 text-red-500"
                  aria-label="Threshold exceeded"
                />
              ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
