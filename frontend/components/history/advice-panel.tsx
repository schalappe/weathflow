"use client";

import { useReducer, useCallback, useEffect } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Sparkles,
  Upload,
  Lightbulb,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { getAdvice, generateAdvice } from "@/lib/api-client";
import {
  cn,
  formatAdviceTimestamp,
  formatCurrency,
  getErrorMessage,
} from "@/lib/utils";
import { t } from "@/lib/translations";
import type { AdviceData, ProblemArea } from "@/types";

type AdvicePanelState = "loading" | "loaded" | "empty" | "error";

interface AdviceState {
  panelState: AdvicePanelState;
  advice: AdviceData | null;
  generatedAt: string | null;
  isRegenerating: boolean;
  error: string | null;
}

type AdviceAction =
  | { type: "FETCH_START" }
  | {
      type: "FETCH_SUCCESS";
      payload: { advice: AdviceData; generatedAt: string };
    }
  | { type: "FETCH_EMPTY" }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "REGENERATE_START" }
  | {
      type: "REGENERATE_SUCCESS";
      payload: { advice: AdviceData; generatedAt: string };
    }
  | { type: "REGENERATE_ERROR"; payload: string };

const initialState: AdviceState = {
  panelState: "loading",
  advice: null,
  generatedAt: null,
  isRegenerating: false,
  error: null,
};

function adviceReducer(state: AdviceState, action: AdviceAction): AdviceState {
  switch (action.type) {
    case "FETCH_START":
      return { ...initialState, panelState: "loading" };

    case "FETCH_SUCCESS":
      return {
        ...state,
        panelState: "loaded",
        advice: action.payload.advice,
        generatedAt: action.payload.generatedAt,
        error: null,
      };

    case "FETCH_EMPTY":
      return { ...state, panelState: "empty", error: null };

    case "FETCH_ERROR":
      return { ...state, panelState: "error", error: action.payload };

    case "REGENERATE_START":
      return { ...state, isRegenerating: true, error: null };

    case "REGENERATE_SUCCESS":
      return {
        ...state,
        panelState: "loaded",
        advice: action.payload.advice,
        generatedAt: action.payload.generatedAt,
        isRegenerating: false,
      };

    case "REGENERATE_ERROR":
      return { ...state, isRegenerating: false, error: action.payload };

    default:
      return state;
  }
}

function isTrendPositive(trend: string): boolean {
  return trend.startsWith("+");
}

function isTrendNegative(trend: string): boolean {
  return trend.startsWith("-");
}

interface AdvicePanelProps {
  year: number;
  month: number;
  className?: string;
}

export function AdvicePanel({ year, month, className }: AdvicePanelProps) {
  const [state, dispatch] = useReducer(adviceReducer, initialState);

  useEffect(() => {
    dispatch({ type: "FETCH_START" });
  }, [year, month]);

  useEffect(() => {
    let isMounted = true;

    async function loadAdvice() {
      try {
        const response = await getAdvice(year, month);
        if (!isMounted) return;

        if (response.exists) {
          dispatch({
            type: "FETCH_SUCCESS",
            payload: {
              advice: response.advice,
              generatedAt: response.generated_at,
            },
          });
        } else {
          dispatch({ type: "FETCH_EMPTY" });
        }
      } catch (error) {
        console.error("[AdvicePanel] Failed to load advice:", error);
        if (isMounted) {
          dispatch({
            type: "FETCH_ERROR",
            payload: getErrorMessage(
              error,
              t.advice.loadError,
            ),
          });
        }
      }
    }

    if (state.panelState === "loading") {
      loadAdvice();
    }

    return () => {
      isMounted = false;
    };
  }, [year, month, state.panelState]);

  const handleGenerate = useCallback(async () => {
    const isRegenerate = state.panelState === "loaded";
    dispatch({ type: "REGENERATE_START" });

    try {
      const response = await generateAdvice(year, month, isRegenerate);
      dispatch({
        type: "REGENERATE_SUCCESS",
        payload: {
          advice: response.advice,
          generatedAt: response.generated_at,
        },
      });
    } catch (error) {
      console.error("[AdvicePanel] Failed to generate advice:", error);
      dispatch({
        type: "REGENERATE_ERROR",
        payload: getErrorMessage(error, t.advice.generateError),
      });
    }
  }, [year, month, state.panelState]);

  const handleRetry = useCallback(() => {
    dispatch({ type: "FETCH_START" });
  }, []);

  return (
    <Card className={cn("border-0 shadow-lg", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/10 to-orange-500/20">
            <Lightbulb className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <CardTitle className="text-lg">{t.advice.title}</CardTitle>
            <CardDescription>
              {t.advice.subtitle}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Loading State */}
        {state.panelState === "loading" && <AdviceSkeletonLoader />}

        {/* Empty State */}
        {state.panelState === "empty" && (
          <EmptyState
            onGenerate={handleGenerate}
            isLoading={state.isRegenerating}
          />
        )}

        {/* Error State */}
        {state.panelState === "error" && (
          <ErrorState error={state.error} onRetry={handleRetry} />
        )}

        {/* Loaded State */}
        {state.panelState === "loaded" && state.advice && (
          <AdviceContent
            advice={state.advice}
            generatedAt={state.generatedAt}
            onRegenerate={handleGenerate}
            isRegenerating={state.isRegenerating}
            regenerateError={state.error}
          />
        )}
      </CardContent>
    </Card>
  );
}

function AdviceSkeletonLoader() {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-5 w-36" />
        <Skeleton className="h-12 w-full rounded-lg" />
        <Skeleton className="h-12 w-full rounded-lg" />
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    </div>
  );
}

interface EmptyStateProps {
  onGenerate: () => void;
  isLoading: boolean;
}

function EmptyState({ onGenerate, isLoading }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-5 py-8 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/20">
        <Sparkles className="h-7 w-7 text-violet-600 dark:text-violet-400" />
      </div>
      <div className="space-y-1.5">
        <h3 className="font-semibold">{t.advice.empty.title}</h3>
        <p className="text-sm text-muted-foreground max-w-xs mx-auto">
          {t.advice.empty.description}
        </p>
      </div>
      <Button onClick={onGenerate} disabled={isLoading} className="gap-2">
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            {t.advice.generating}
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            {t.advice.empty.button}
          </>
        )}
      </Button>
    </div>
  );
}

function isDataRelatedError(error: string | null): boolean {
  if (!error) return false;
  const lowerError = error.toLowerCase();
  return (
    lowerError.includes("mois") ||
    lowerError.includes("month") ||
    lowerError.includes("donnees") ||
    lowerError.includes("data") ||
    lowerError.includes("not found") ||
    lowerError.includes("insufficient")
  );
}

interface ErrorStateProps {
  error: string | null;
  onRetry: () => void;
}

function ErrorState({ error, onRetry }: ErrorStateProps) {
  const needsImport = isDataRelatedError(error);

  return (
    <Alert
      variant="destructive"
      className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
    >
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span>{error}</span>
        {needsImport ? (
          <Button variant="outline" size="sm" asChild className="gap-2">
            <Link href="/import">
              <Upload className="h-4 w-4" />
              {t.advice.importData}
            </Link>
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="gap-2"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            {t.advice.retry}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

interface ProblemAreaItemProps {
  area: ProblemArea;
  index: number;
}

function ProblemAreaItem({ area, index }: ProblemAreaItemProps) {
  const isUp = isTrendPositive(area.trend);
  const isDown = isTrendNegative(area.trend);

  return (
    <li className="flex items-center justify-between rounded-xl bg-muted/50 px-4 py-3 transition-colors hover:bg-muted">
      <span className="text-sm font-medium">
        {index + 1}. {area.category}
      </span>
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold tabular-nums">
          {formatCurrency(area.amount)}
        </span>
        <span
          className={cn(
            "flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
            isUp && "bg-red-500/10 text-red-700 dark:text-red-400",
            isDown &&
              "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
            !isUp &&
              !isDown &&
              "bg-gray-500/10 text-gray-600 dark:text-gray-400",
          )}
        >
          {isUp && <TrendingUp className="h-3 w-3" />}
          {isDown && <TrendingDown className="h-3 w-3" />}
          {area.trend}
        </span>
      </div>
    </li>
  );
}

interface AdviceContentProps {
  advice: AdviceData;
  generatedAt: string | null;
  onRegenerate: () => void;
  isRegenerating: boolean;
  regenerateError: string | null;
}

function AdviceContent({
  advice,
  generatedAt,
  onRegenerate,
  isRegenerating,
  regenerateError,
}: AdviceContentProps) {
  return (
    <div className="space-y-6">
      {/* Regenerate error banner */}
      {regenerateError && (
        <Alert
          variant="destructive"
          className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{regenerateError}</AlertDescription>
        </Alert>
      )}

      {/* Analysis Section */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4.5 w-4.5 text-violet-600 dark:text-violet-400" />
          <h4 className="font-semibold">{t.advice.sections.analysis}</h4>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {advice.analysis}
        </p>
      </section>

      {/* Problem Areas Section */}
      {advice.problem_areas.length > 0 && (
        <>
          <Separator />
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4.5 w-4.5 text-amber-600 dark:text-amber-400" />
              <h4 className="font-semibold">{t.advice.sections.problems}</h4>
            </div>
            <ul className="space-y-2">
              {advice.problem_areas.map((area, index) => (
                <ProblemAreaItem key={index} area={area} index={index} />
              ))}
            </ul>
          </section>
        </>
      )}

      {/* Recommendations Section */}
      {advice.recommendations.length > 0 && (
        <>
          <Separator />
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600 dark:text-emerald-400" />
              <h4 className="font-semibold">{t.advice.sections.recommendations}</h4>
            </div>
            <ol className="space-y-2 text-sm text-muted-foreground">
              {advice.recommendations.map((rec, index) => (
                <li
                  key={index}
                  className="flex gap-3 rounded-lg bg-muted/30 p-3 leading-relaxed"
                >
                  <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {index + 1}
                  </span>
                  <span>{rec}</span>
                </li>
              ))}
            </ol>
          </section>
        </>
      )}

      {/* Encouragement Section */}
      <Separator />
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4.5 w-4.5 text-violet-600 dark:text-violet-400" />
          <h4 className="font-semibold">{t.advice.sections.encouragement}</h4>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {advice.encouragement}
        </p>
      </section>

      {/* Footer with timestamp and regenerate button */}
      <div className="flex items-center justify-between border-t pt-4">
        {generatedAt && (
          <p className="text-xs text-muted-foreground">
            {t.advice.generated} {formatAdviceTimestamp(generatedAt)}
          </p>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="gap-2"
        >
          {isRegenerating ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              {t.advice.regenerating}
            </>
          ) : (
            <>
              <RefreshCw className="h-3.5 w-3.5" />
              {t.advice.regenerate}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
