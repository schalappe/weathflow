"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  formatMonthDisplay,
  SCORE_COLORS,
  sortMonthsChronologically,
} from "@/lib/utils";
import { t } from "@/lib/translations";
import { CheckCircle, AlertTriangle } from "lucide-react";
import type { MonthResult } from "@/types";

interface ResultsSummaryProps {
  results: MonthResult[];
  monthsNotFound: string[];
  totalApiCalls: number;
  onFinish: () => void;
}

export function ResultsSummary({
  results,
  monthsNotFound,
  totalApiCalls,
  onFinish,
}: ResultsSummaryProps) {
  const sortedResults = sortMonthsChronologically(results);

  const totalTransactions = results.reduce(
    (sum, r) => sum + r.transactions_categorized,
    0,
  );

  return (
    <div className="space-y-6">
      {/* Success header */}
      <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950/30">
        <CheckCircle className="h-6 w-6 text-emerald-600" />
        <div>
          <p className="font-medium text-emerald-800 dark:text-emerald-200">
            {t.results.complete}
          </p>
          <p className="text-sm text-emerald-700 dark:text-emerald-300">
            {totalTransactions} {t.results.transactionsCategorized}{" "}
            {results.length} {results.length === 1 ? t.progress.month : t.progress.months} ({totalApiCalls} {t.results.apiCalls})
          </p>
        </div>
      </div>

      {/* Month results grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sortedResults.map((result) => (
          <MonthResultCard
            key={`${result.year}-${result.month}`}
            result={result}
          />
        ))}
      </div>

      {/* Months not found warning */}
      {monthsNotFound.length > 0 && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800 dark:text-amber-200">
              {t.results.monthsNotFound}
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-300">
              {monthsNotFound.join(", ")}
            </p>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-3">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" disabled>
                {t.results.viewTransactions}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t.results.comingSoon}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <Button onClick={onFinish}>{t.results.finish}</Button>
      </div>
    </div>
  );
}

function MonthResultCard({ result }: { result: MonthResult }) {
  const scoreColor = SCORE_COLORS[result.score] || "bg-gray-500";
  const translatedLabel = t.score.labels[result.score_label as keyof typeof t.score.labels] || result.score_label;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {formatMonthDisplay(result.year, result.month)}
          </CardTitle>
          <Badge className={`${scoreColor} text-white`}>
            {translatedLabel}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-lg font-semibold">{t.results.score} : {result.score}/3</div>

        {/* Stats */}
        <div className="flex flex-col gap-1 text-sm text-muted-foreground">
          <span>{result.transactions_categorized} transactions</span>
          {result.low_confidence_count > 0 && (
            <span className="text-amber-600">
              {result.low_confidence_count} {t.results.lowConfidence}
            </span>
          )}
          {result.transactions_skipped > 0 && (
            <span className="text-red-600">
              {result.transactions_skipped} {t.results.skipped}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
