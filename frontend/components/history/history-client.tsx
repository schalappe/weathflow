"use client";

import { useReducer, useCallback, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Upload } from "lucide-react";
import { PeriodSelector } from "./period-selector";
import { ScoreChart } from "./score-chart";
import { SpendingBreakdownChart } from "./breakdown-chart";
import { getMonthsHistory } from "@/lib/api-client";
import { getErrorMessage } from "@/lib/utils";
import type { MonthHistory } from "@/types";

// [>]: Page states for the history page state machine.
type HistoryPageState = "loading" | "loaded" | "empty" | "error";

// [>]: State shape for the history page reducer.
interface HistoryState {
  pageState: HistoryPageState;
  period: number;
  months: MonthHistory[];
  error: string | null;
}

// [>]: Discriminated union for type-safe reducer actions.
type HistoryAction =
  | { type: "LOAD_START" }
  | { type: "LOAD_SUCCESS"; payload: MonthHistory[] }
  | { type: "LOAD_ERROR"; payload: string }
  | { type: "SET_PERIOD"; payload: number };

// [>]: Initial state with default period of 12 months.
const initialState: HistoryState = {
  pageState: "loading",
  period: 12,
  months: [],
  error: null,
};

// [>]: Reducer handles all state transitions.
function historyReducer(
  state: HistoryState,
  action: HistoryAction,
): HistoryState {
  switch (action.type) {
    case "LOAD_START":
      return {
        ...state,
        pageState: "loading",
        error: null,
      };

    case "LOAD_SUCCESS":
      // [>]: If months array is empty, treat as empty state.
      if (action.payload.length === 0) {
        return {
          ...state,
          pageState: "empty",
          months: [],
        };
      }
      return {
        ...state,
        pageState: "loaded",
        months: action.payload,
      };

    case "LOAD_ERROR":
      return {
        ...state,
        pageState: "error",
        error: action.payload,
      };

    case "SET_PERIOD":
      // [>]: Trigger refetch by setting pageState to loading.
      return {
        ...state,
        period: action.payload,
        pageState: "loading",
      };

    default:
      return state;
  }
}

export function HistoryClient() {
  const [state, dispatch] = useReducer(historyReducer, initialState);

  // [>]: Fetch history data with cleanup to prevent memory leaks.
  useEffect(() => {
    let isMounted = true;

    async function loadHistory() {
      try {
        const response = await getMonthsHistory(state.period);
        if (isMounted) {
          dispatch({ type: "LOAD_SUCCESS", payload: response.months });
        }
      } catch (error) {
        console.error("[HistoryClient] Failed to load history data:", error);
        if (isMounted) {
          dispatch({
            type: "LOAD_ERROR",
            payload: getErrorMessage(error, "Failed to load history data"),
          });
        }
      }
    }

    if (state.pageState === "loading") {
      loadHistory();
    }

    return () => {
      isMounted = false;
    };
  }, [state.pageState, state.period]);

  // [>]: Handle period change from selector.
  const handlePeriodChange = useCallback((months: number) => {
    dispatch({ type: "SET_PERIOD", payload: months });
  }, []);

  // [>]: Handle retry after error.
  const handleRetry = useCallback(() => {
    dispatch({ type: "LOAD_START" });
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Loading State - Initial load only */}
      {state.pageState === "loading" && state.months.length === 0 && (
        <div className="flex items-center justify-center py-24">
          <div className="flex flex-col items-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {state.pageState === "empty" && (
        <Card className="mx-auto max-w-md">
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="rounded-full bg-slate-100 p-4">
              <Upload className="h-8 w-8 text-slate-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">
                Aucune donnee historique
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Importez vos premieres transactions pour voir l&apos;evolution
                de votre budget.
              </p>
            </div>
            <Button asChild>
              <Link href="/import">Importer des transactions</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {state.pageState === "error" && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{state.error}</span>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              Reessayer
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* [>]: Show content when loaded or during period switch (optimistic UI). */}
      {(state.pageState === "loaded" ||
        (state.pageState === "loading" && state.months.length > 0)) && (
        <>
          {/* Header Row */}
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold tracking-tight">Historique</h1>
            <PeriodSelector
              value={state.period}
              onChange={handlePeriodChange}
              disabled={state.pageState === "loading"}
            />
          </div>

          {/* Charts Grid */}
          <div className="grid gap-6 lg:grid-cols-2">
            <ScoreChart months={state.months} />
            <SpendingBreakdownChart months={state.months} />
          </div>
        </>
      )}
    </div>
  );
}
