"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, X } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  amount: number;
  percentage?: number;
  isSuccess?: boolean;
  colorClass: string;
}

export function MetricCard({
  title,
  amount,
  percentage,
  isSuccess,
  colorClass,
}: MetricCardProps) {
  return (
    <Card className={cn("border-l-4", colorClass)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <div className="text-2xl font-bold">{formatCurrency(amount)}</div>
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
