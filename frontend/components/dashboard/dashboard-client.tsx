"use client";

import { useReducer, useCallback, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Upload, Clock } from "lucide-react";
import { ScoreCard } from "./score-card";
import { MetricCard } from "./metric-card";
import { SpendingPieChart } from "./spending-pie-chart";
import { MonthSelector } from "./month-selector";
import { TransactionTable } from "./transaction-table";
import { getMonthsList, getMonthDetail } from "@/lib/api-client";
import {
  formatMonthDisplay,
  meetsThreshold,
  getErrorMessage,
  CATEGORY_TAILWIND,
  TRANSACTIONS_PER_PAGE,
} from "@/lib/utils";
import type { DashboardState, DashboardAction } from "@/types";

// [>]: Initial state for the dashboard reducer.
const initialState: DashboardState = {
  pageState: "loading",
  monthsList: [],
  selectedMonth: null,
  monthDetail: null,
  currentPage: 1,
  error: null,
};

// [>]: Reducer function handles all state transitions.
function dashboardReducer(
  state: DashboardState,
  action: DashboardAction,
): DashboardState {
  switch (action.type) {
    case "LOAD_START":
      return {
        ...state,
        pageState: "loading",
        error: null,
      };

    case "MONTHS_LOADED":
      // [>]: If no months, transition to empty state.
      if (action.payload.length === 0) {
        return {
          ...state,
          pageState: "empty",
          monthsList: [],
        };
      }
      // [>]: Auto-select most recent month (first in list, assuming backend sorts by recency).
      const mostRecent = action.payload[0];
      return {
        ...state,
        monthsList: action.payload,
        selectedMonth: { year: mostRecent.year, month: mostRecent.month },
      };

    case "MONTH_DETAIL_LOADED":
      return {
        ...state,
        pageState: "loaded",
        monthDetail: action.payload,
      };

    case "SELECT_MONTH":
      // [>]: Reset to page 1 when changing months.
      return {
        ...state,
        selectedMonth: action.payload,
        currentPage: 1,
        pageState: "loading",
      };

    case "SET_PAGE":
      return {
        ...state,
        currentPage: action.payload,
        pageState: "loading",
      };

    case "LOAD_ERROR":
      // [>]: Keep state on error to allow retry without losing context (unlike import page which resets).
      return {
        ...state,
        pageState: "error",
        error: action.payload,
      };

    case "RETRY":
      return {
        ...initialState,
      };

    default:
      return state;
  }
}

export function DashboardClient() {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);

  // [>]: Fetch months list on mount with cleanup to prevent state updates after unmount.
  useEffect(() => {
    let isMounted = true;

    async function loadMonths() {
      try {
        const response = await getMonthsList();
        if (isMounted) {
          dispatch({ type: "MONTHS_LOADED", payload: response.months });
        }
      } catch (error) {
        if (isMounted) {
          dispatch({
            type: "LOAD_ERROR",
            payload: getErrorMessage(error, "Failed to load months"),
          });
        }
      }
    }

    if (state.pageState === "loading" && state.monthsList.length === 0) {
      loadMonths();
    }

    return () => {
      isMounted = false;
    };
  }, [state.pageState, state.monthsList.length]);

  // [>]: Fetch month detail when selectedMonth or currentPage changes with cleanup.
  useEffect(() => {
    let isMounted = true;

    async function loadMonthDetail() {
      if (!state.selectedMonth) return;

      try {
        const response = await getMonthDetail(
          state.selectedMonth.year,
          state.selectedMonth.month,
          state.currentPage,
          TRANSACTIONS_PER_PAGE,
        );
        if (isMounted) {
          dispatch({ type: "MONTH_DETAIL_LOADED", payload: response });
        }
      } catch (error) {
        if (isMounted) {
          dispatch({
            type: "LOAD_ERROR",
            payload: getErrorMessage(error, "Failed to load month data"),
          });
        }
      }
    }

    if (state.selectedMonth && state.pageState === "loading") {
      loadMonthDetail();
    }

    return () => {
      isMounted = false;
    };
  }, [state.selectedMonth, state.currentPage, state.pageState]);

  // [>]: Handle month change from selector.
  const handleMonthChange = useCallback((year: number, month: number) => {
    dispatch({ type: "SELECT_MONTH", payload: { year, month } });
  }, []);

  // [>]: Handle pagination change.
  const handlePageChange = useCallback((page: number) => {
    dispatch({ type: "SET_PAGE", payload: page });
  }, []);

  // [>]: Handle retry after error.
  const handleRetry = useCallback(() => {
    dispatch({ type: "RETRY" });
  }, []);

  const isLoading = state.pageState === "loading";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Navigation Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Money Map Manager
          </h1>
          <nav className="flex items-center gap-4">
            <Link
              href="/import"
              className="flex items-center gap-2 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
            >
              <Upload className="h-4 w-4" />
              Import
            </Link>
            <span className="flex cursor-not-allowed items-center gap-2 text-sm font-medium text-slate-400">
              <Clock className="h-4 w-4" />
              History
            </span>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        {/* Loading State */}
        {state.pageState === "loading" && state.monthsList.length === 0 && (
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
                  No months imported yet
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Import your first Bankin&apos; CSV export to see your Money
                  Map dashboard.
                </p>
              </div>
              <Button asChild>
                <Link href="/import">Import Transactions</Link>
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
                Try Again
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* [>]: Show dashboard when data exists. During loading (pagination/month change), keep
            showing old data for optimistic UI instead of flashing a loading spinner. */}
        {(state.pageState === "loaded" ||
          (state.pageState === "loading" && state.monthDetail)) &&
          state.monthDetail &&
          state.selectedMonth && (
            <>
              {/* Month Selector Row */}
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-slate-700">
                  Dashboard
                </h2>
                <MonthSelector
                  months={state.monthsList}
                  selectedYear={state.selectedMonth.year}
                  selectedMonth={state.selectedMonth.month}
                  onMonthChange={handleMonthChange}
                  isDisabled={isLoading}
                />
              </div>

              {/* Score Card */}
              <ScoreCard
                score={state.monthDetail.month.score}
                scoreLabel={state.monthDetail.month.score_label}
                monthDisplay={formatMonthDisplay(
                  state.monthDetail.month.year,
                  state.monthDetail.month.month,
                )}
              />

              {/* [>]: Metric Cards Grid. Backend returns expense categories as negative values,
                  so Math.abs() is applied for display. Income is already positive. */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                  title="Income"
                  amount={state.monthDetail.month.total_income}
                  colorClass={CATEGORY_TAILWIND.INCOME}
                />
                <MetricCard
                  title="Core"
                  amount={Math.abs(state.monthDetail.month.total_core)}
                  percentage={state.monthDetail.month.core_percentage}
                  isSuccess={meetsThreshold(
                    "CORE",
                    state.monthDetail.month.core_percentage,
                  )}
                  colorClass={CATEGORY_TAILWIND.CORE}
                />
                <MetricCard
                  title="Choice"
                  amount={Math.abs(state.monthDetail.month.total_choice)}
                  percentage={state.monthDetail.month.choice_percentage}
                  isSuccess={meetsThreshold(
                    "CHOICE",
                    state.monthDetail.month.choice_percentage,
                  )}
                  colorClass={CATEGORY_TAILWIND.CHOICE}
                />
                <MetricCard
                  title="Compound"
                  amount={Math.abs(state.monthDetail.month.total_compound)}
                  percentage={state.monthDetail.month.compound_percentage}
                  isSuccess={meetsThreshold(
                    "COMPOUND",
                    state.monthDetail.month.compound_percentage,
                  )}
                  colorClass={CATEGORY_TAILWIND.COMPOUND}
                  compoundDirection={
                    state.monthDetail.month.total_compound >= 0
                      ? "positive"
                      : "negative"
                  }
                />
              </div>

              {/* Pie Chart and Transaction Table */}
              <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-1">
                  <SpendingPieChart
                    core={state.monthDetail.month.total_core}
                    choice={state.monthDetail.month.total_choice}
                    compound={state.monthDetail.month.total_compound}
                  />
                </div>
                <div className="lg:col-span-2">
                  <TransactionTable
                    transactions={state.monthDetail.transactions}
                    pagination={state.monthDetail.pagination}
                    onPageChange={handlePageChange}
                    isLoading={isLoading}
                  />
                </div>
              </div>
            </>
          )}
      </main>
    </div>
  );
}
