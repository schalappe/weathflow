"use client";

import { useReducer, useCallback, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Upload, RefreshCw, Lightbulb } from "lucide-react";
import { MonthNavigator } from "@/components/dashboard/month-navigator";
import { AdvicePanelContent } from "@/components/history/advice-panel-content";
import { getMonthsList } from "@/lib/api-client";
import { getErrorMessage } from "@/lib/utils";
import { t } from "@/lib/translations";
import type { MonthSummary } from "@/types";

type AdvicePageState = "loading" | "loaded" | "empty" | "error";

interface PageState {
  pageState: AdvicePageState;
  monthsList: MonthSummary[];
  selectedYear: number | null;
  selectedMonth: number | null;
  error: string | null;
}

type PageAction =
  | { type: "LOAD_START" }
  | { type: "MONTHS_LOADED"; payload: MonthSummary[] }
  | { type: "LOAD_ERROR"; payload: string }
  | { type: "SELECT_MONTH"; payload: { year: number; month: number } };

const initialState: PageState = {
  pageState: "loading",
  monthsList: [],
  selectedYear: null,
  selectedMonth: null,
  error: null,
};

function pageReducer(state: PageState, action: PageAction): PageState {
  switch (action.type) {
    case "LOAD_START":
      return { ...state, pageState: "loading", error: null };

    case "MONTHS_LOADED":
      if (action.payload.length === 0) {
        return { ...state, pageState: "empty", monthsList: [] };
      }
      // [>]: Auto-select most recent month (first in array, sorted desc).
      const mostRecent = action.payload[0];
      return {
        ...state,
        pageState: "loaded",
        monthsList: action.payload,
        selectedYear: mostRecent.year,
        selectedMonth: mostRecent.month,
      };

    case "LOAD_ERROR":
      return { ...state, pageState: "error", error: action.payload };

    case "SELECT_MONTH":
      return {
        ...state,
        selectedYear: action.payload.year,
        selectedMonth: action.payload.month,
      };

    default:
      return state;
  }
}

function AdvicePageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-[180px]" />
      </div>
      <Card className="border-0 shadow-lg">
        <CardContent className="pt-6">
          <div className="space-y-6">
            <div className="space-y-3">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
            <Skeleton className="h-px w-full" />
            <div className="space-y-3">
              <Skeleton className="h-5 w-36" />
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-12 w-full rounded-lg" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function AdvicePageClient() {
  const [state, dispatch] = useReducer(pageReducer, initialState);

  useEffect(() => {
    let isMounted = true;

    async function loadMonths() {
      try {
        const response = await getMonthsList();
        if (isMounted) {
          dispatch({ type: "MONTHS_LOADED", payload: response.months });
        }
      } catch (error) {
        console.error("[AdvicePageClient] Failed to load months:", error);
        if (isMounted) {
          dispatch({
            type: "LOAD_ERROR",
            payload: getErrorMessage(error, t.advicePage.loadMonthsError),
          });
        }
      }
    }

    if (state.pageState === "loading") {
      loadMonths();
    }

    return () => {
      isMounted = false;
    };
  }, [state.pageState]);

  const handleMonthChange = useCallback((year: number, month: number) => {
    dispatch({ type: "SELECT_MONTH", payload: { year, month } });
  }, []);

  const handleRetry = useCallback(() => {
    dispatch({ type: "LOAD_START" });
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Loading State */}
      {state.pageState === "loading" && <AdvicePageSkeleton />}

      {/* Empty State */}
      {state.pageState === "empty" && (
        <div className="flex min-h-[60vh] items-center justify-center">
          <Card className="mx-auto max-w-md border-0 shadow-lg">
            <CardContent className="flex flex-col items-center gap-6 py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500/10 to-orange-500/20">
                <Lightbulb className="h-8 w-8 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-semibold tracking-tight">
                  {t.advicePage.empty.title}
                </h2>
                <p className="text-sm text-muted-foreground max-w-xs">
                  {t.advicePage.empty.description}
                </p>
              </div>
              <Button asChild className="gap-2">
                <Link href="/import">
                  <Upload className="h-4 w-4" />
                  {t.advicePage.empty.button}
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
              {t.advicePage.retry}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loaded Content */}
      {state.pageState === "loaded" &&
        state.selectedYear !== null &&
        state.selectedMonth !== null && (
          <div className="space-y-6 animate-fade-in-up">
            {/* Header Row */}
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h1 className="text-2xl font-bold tracking-tight">
                  {t.advicePage.title}
                </h1>
                <p className="text-muted-foreground">{t.advicePage.subtitle}</p>
              </div>
              <MonthNavigator
                months={state.monthsList}
                selectedYear={state.selectedYear}
                selectedMonth={state.selectedMonth}
                onMonthChange={handleMonthChange}
                isDisabled={false}
              />
            </div>

            {/* Advice Content in Card */}
            <Card className="border-0 shadow-lg">
              <CardContent className="pt-6">
                <AdvicePanelContent
                  key={`${state.selectedYear}-${state.selectedMonth}`}
                  year={state.selectedYear}
                  month={state.selectedMonth}
                />
              </CardContent>
            </Card>
          </div>
        )}
    </div>
  );
}
