"use client";

import { useReducer, useCallback, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Upload, RefreshCw, TrendingUp } from "lucide-react";
import { AdvicePanel } from "./advice-panel";
import { PeriodSelector } from "./period-selector";
import { ScoreChart } from "./score-chart";
import { SpendingBreakdownChart } from "./breakdown-chart";
import { getMonthsHistory } from "@/lib/api-client";
import { getErrorMessage } from "@/lib/utils";
import { t } from "@/lib/translations";
import type { MonthHistory } from "@/types";

type HistoryPageState = "loading" | "loaded" | "empty" | "error";

interface HistoryState {
  pageState: HistoryPageState;
  period: number;
  months: MonthHistory[];
  error: string | null;
}

type HistoryAction =
  | { type: "LOAD_START" }
  | { type: "LOAD_SUCCESS"; payload: MonthHistory[] }
  | { type: "LOAD_ERROR"; payload: string }
  | { type: "SET_PERIOD"; payload: number };

const initialState: HistoryState = {
  pageState: "loading",
  period: 12,
  months: [],
  error: null,
};

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
      return {
        ...state,
        period: action.payload,
        pageState: "loading",
      };

    default:
      return state;
  }
}

function HistorySkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-9 w-28" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-[320px] w-full rounded-xl" />
        <Skeleton className="h-[320px] w-full rounded-xl" />
      </div>
      <Skeleton className="h-[400px] w-full rounded-xl" />
    </div>
  );
}

export function HistoryClient() {
  const [state, dispatch] = useReducer(historyReducer, initialState);

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

  const handlePeriodChange = useCallback((months: number) => {
    dispatch({ type: "SET_PERIOD", payload: months });
  }, []);

  const handleRetry = useCallback(() => {
    dispatch({ type: "LOAD_START" });
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Loading State - Initial load only */}
      {state.pageState === "loading" && state.months.length === 0 && (
        <HistorySkeleton />
      )}

      {/* Empty State */}
      {state.pageState === "empty" && (
        <div className="flex min-h-[60vh] items-center justify-center">
          <Card className="mx-auto max-w-md border-0 shadow-lg">
            <CardContent className="flex flex-col items-center gap-6 py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/20">
                <TrendingUp className="h-8 w-8 text-violet-600 dark:text-violet-400" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-semibold tracking-tight">
                  {t.history.empty.title}
                </h2>
                <p className="text-sm text-muted-foreground max-w-xs">
                  {t.history.empty.description}
                </p>
              </div>
              <Button asChild className="gap-2">
                <Link href="/import">
                  <Upload className="h-4 w-4" />
                  {t.history.empty.button}
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Error State */}
      {state.pageState === "error" && (
        <Alert
          variant="destructive"
          className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{state.error}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetry}
              className="gap-2"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              {t.history.retry}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loaded Content */}
      {(state.pageState === "loaded" ||
        (state.pageState === "loading" && state.months.length > 0)) && (
        <div className="space-y-6 animate-fade-in-up">
          {/* Header Row */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                {t.history.title}
              </h1>
              <p className="text-sm text-muted-foreground">
                {t.history.subtitle}
              </p>
            </div>
            <PeriodSelector
              value={state.period}
              onChange={handlePeriodChange}
              disabled={state.pageState === "loading"}
            />
          </div>

          {/* Charts Grid */}
          <div className="grid gap-6 lg:grid-cols-2">
            <ScoreChart months={state.months} period={state.period} />
            <SpendingBreakdownChart months={state.months} />
          </div>

          {/* Advice Panel */}
          {state.months.length > 0 && (
            <AdvicePanel
              year={state.months[state.months.length - 1].year}
              month={state.months[state.months.length - 1].month}
            />
          )}
        </div>
      )}
    </div>
  );
}
