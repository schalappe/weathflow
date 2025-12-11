"use client";

import { useReducer, useCallback, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { getAdvice, generateAdvice } from "@/lib/api-client";
import {
  cn,
  formatAdviceTimestamp,
  formatCurrency,
  getErrorMessage,
} from "@/lib/utils";
import type { AdviceData, ProblemArea } from "@/types";

// [>]: Panel state machine with 4 core states + regenerating flag.
type AdvicePanelState = "loading" | "loaded" | "empty" | "error";

interface AdviceState {
  panelState: AdvicePanelState;
  advice: AdviceData | null;
  generatedAt: string | null;
  isRegenerating: boolean;
  error: string | null;
}

// [>]: Discriminated union for type-safe reducer actions.
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
      // [>]: Keep existing advice visible, show error inline.
      return { ...state, isRegenerating: false, error: action.payload };

    default:
      return state;
  }
}

// [>]: Determine if trend is positive (spending increased = bad).
function isTrendPositive(trend: string): boolean {
  return trend.startsWith("+");
}

// [>]: Determine if trend is negative (spending decreased = good).
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

  // [>]: Reset to loading state when year/month props change.
  useEffect(() => {
    dispatch({ type: "FETCH_START" });
  }, [year, month]);

  // [>]: Fetch advice when in loading state (initial mount, prop change, or retry).
  useEffect(() => {
    let isMounted = true;

    async function loadAdvice() {
      try {
        const response = await getAdvice(year, month);
        if (!isMounted) return;

        // [>]: Discriminated union guarantees advice/generated_at when exists=true.
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
              "Impossible de charger les conseils",
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

  // [>]: Handle generate/regenerate button click.
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
        payload: getErrorMessage(error, "Impossible de generer les conseils"),
      });
    }
  }, [year, month, state.panelState]);

  // [>]: Handle retry after error.
  const handleRetry = useCallback(() => {
    dispatch({ type: "FETCH_START" });
  }, []);

  return (
    <Card className={cn("mt-6", className)}>
      <CardHeader>
        <CardTitle>Conseils Personnalises</CardTitle>
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

// [>]: Skeleton loader mimicking the layout of loaded state.
function AdviceSkeletonLoader() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Analysis skeleton */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-slate-200" />
          <div className="h-5 w-40 rounded bg-slate-200" />
        </div>
        <div className="h-4 w-full rounded bg-slate-200" />
        <div className="h-4 w-3/4 rounded bg-slate-200" />
      </div>

      {/* Problem areas skeleton */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-slate-200" />
          <div className="h-5 w-36 rounded bg-slate-200" />
        </div>
        <div className="h-10 w-full rounded bg-slate-200" />
        <div className="h-10 w-full rounded bg-slate-200" />
      </div>

      {/* Recommendations skeleton */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-slate-200" />
          <div className="h-5 w-32 rounded bg-slate-200" />
        </div>
        <div className="h-4 w-full rounded bg-slate-200" />
        <div className="h-4 w-5/6 rounded bg-slate-200" />
        <div className="h-4 w-2/3 rounded bg-slate-200" />
      </div>
    </div>
  );
}

// [>]: Empty state with call-to-action.
interface EmptyStateProps {
  onGenerate: () => void;
  isLoading: boolean;
}

function EmptyState({ onGenerate, isLoading }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-8 text-center">
      <div className="rounded-full bg-slate-100 p-4">
        <Sparkles className="h-8 w-8 text-slate-400" />
      </div>
      <div>
        <h3 className="font-semibold">Aucun conseil disponible</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Generez des conseils personnalises bases sur vos 3 derniers mois de
          transactions.
        </p>
      </div>
      <Button onClick={onGenerate} disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generation...
          </>
        ) : (
          "Generer des conseils"
        )}
      </Button>
    </div>
  );
}

// [>]: Error state with retry button.
interface ErrorStateProps {
  error: string | null;
  onRetry: () => void;
}

function ErrorState({ error, onRetry }: ErrorStateProps) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>{error}</span>
        <Button variant="outline" size="sm" onClick={onRetry}>
          Reessayer
        </Button>
      </AlertDescription>
    </Alert>
  );
}

// [>]: Problem area item with trend color coding.
interface ProblemAreaItemProps {
  area: ProblemArea;
  index: number;
}

function ProblemAreaItem({ area, index }: ProblemAreaItemProps) {
  return (
    <li className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
      <span className="text-sm">
        {index + 1}. {area.category}
      </span>
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium">
          {formatCurrency(area.amount)}
        </span>
        <span
          className={cn(
            "text-sm font-medium",
            // [>]: Red for positive trend (spending up = bad).
            // [>]: Green for negative trend (spending down = good).
            // [>]: Gray for neutral.
            isTrendPositive(area.trend)
              ? "text-red-600"
              : isTrendNegative(area.trend)
                ? "text-green-600"
                : "text-slate-500",
          )}
        >
          {area.trend}
        </span>
      </div>
    </li>
  );
}

// [>]: Main advice content display.
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
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{regenerateError}</AlertDescription>
        </Alert>
      )}

      {/* Analysis Section */}
      <section>
        <div className="mb-2 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
          <h4 className="font-semibold">Analyse des tendances</h4>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          {advice.analysis}
        </p>
      </section>

      {/* Problem Areas Section */}
      {advice.problem_areas.length > 0 && (
        <section>
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-muted-foreground" />
            <h4 className="font-semibold">Points d&apos;attention</h4>
          </div>
          <ul className="space-y-2">
            {advice.problem_areas.map((area, index) => (
              <ProblemAreaItem key={index} area={area} index={index} />
            ))}
          </ul>
        </section>
      )}

      {/* Recommendations Section */}
      {advice.recommendations.length > 0 && (
        <section>
          <div className="mb-3 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-muted-foreground" />
            <h4 className="font-semibold">Recommandations</h4>
          </div>
          <ol className="list-decimal list-inside space-y-2 text-sm text-slate-600">
            {advice.recommendations.map((rec, index) => (
              <li key={index} className="leading-relaxed">
                {rec}
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* Encouragement Section */}
      <section>
        <div className="mb-2 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-muted-foreground" />
          <h4 className="font-semibold">Encouragement</h4>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          {advice.encouragement}
        </p>
      </section>

      {/* Footer with timestamp and regenerate button */}
      <div className="flex items-center justify-between border-t pt-4">
        {generatedAt && (
          <p className="text-xs text-muted-foreground">
            Genere {formatAdviceTimestamp(generatedAt)}
          </p>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={onRegenerate}
          disabled={isRegenerating}
        >
          {isRegenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Regeneration...
            </>
          ) : (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerer
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
