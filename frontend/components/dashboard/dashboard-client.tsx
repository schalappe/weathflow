"use client";

import { useReducer, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Upload, RefreshCw } from "lucide-react";
import { ScoreCard } from "./score-card";
import { MetricCard } from "./metric-card";
import { SpendingPieChart } from "./spending-pie-chart";
import { MonthSelector } from "./month-selector";
import { TransactionTable } from "./transaction-table";
import { TransactionEditModal } from "./transaction-edit-modal";
import { ExportButtons } from "./export-buttons";
import {
  getMonthsList,
  getMonthDetail,
  updateTransaction,
} from "@/lib/api-client";
import {
  formatMonthDisplay,
  meetsThreshold,
  getErrorMessage,
  TRANSACTIONS_PER_PAGE,
} from "@/lib/utils";
import type {
  DashboardState,
  DashboardAction,
  TransactionFilters,
  TransactionResponse,
  UpdateTransactionPayload,
} from "@/types";
import { DEFAULT_FILTERS } from "@/types";

const initialState: DashboardState = {
  pageState: "loading",
  monthsList: [],
  selectedMonth: null,
  monthDetail: null,
  currentPage: 1,
  error: null,
  editingTransaction: null,
  filters: DEFAULT_FILTERS,
};

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
      if (action.payload.length === 0) {
        return {
          ...state,
          pageState: "empty",
          monthsList: [],
        };
      }
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
      return {
        ...state,
        selectedMonth: action.payload,
        currentPage: 1,
        filters: DEFAULT_FILTERS,
        pageState: "loading",
      };

    case "SET_PAGE":
      return {
        ...state,
        currentPage: action.payload,
        pageState: "loading",
      };

    case "SET_FILTERS":
      return {
        ...state,
        filters: action.payload,
        currentPage: 1,
        pageState: "loading",
      };

    case "LOAD_ERROR":
      return {
        ...state,
        pageState: "error",
        error: action.payload,
      };

    case "RETRY":
      return {
        ...initialState,
      };

    case "OPEN_EDIT_MODAL":
      return {
        ...state,
        editingTransaction: action.payload,
      };

    case "CLOSE_EDIT_MODAL":
      return {
        ...state,
        editingTransaction: null,
      };

    case "TRANSACTION_UPDATED":
      return {
        ...state,
        editingTransaction: null,
        monthDetail: state.monthDetail
          ? {
              ...state.monthDetail,
              month: action.payload.updated_month_stats,
              transactions: state.monthDetail.transactions.map((tx) =>
                tx.id === action.payload.transaction.id
                  ? action.payload.transaction
                  : tx,
              ),
            }
          : null,
      };

    default:
      return state;
  }
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-7 w-32" />
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-36" />
        </div>
      </div>
      {/* Score card skeleton */}
      <Skeleton className="h-24 w-full rounded-xl" />
      {/* Metric cards skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-36 w-full rounded-xl" />
        ))}
      </div>
      {/* Charts skeleton */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-[380px] w-full rounded-xl lg:col-span-1" />
        <Skeleton className="h-[380px] w-full rounded-xl lg:col-span-2" />
      </div>
    </div>
  );
}

export function DashboardClient() {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

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
          state.filters,
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
  }, [state.selectedMonth, state.currentPage, state.pageState, state.filters]);

  const handleMonthChange = useCallback((year: number, month: number) => {
    dispatch({ type: "SELECT_MONTH", payload: { year, month } });
  }, []);

  const handlePageChange = useCallback((page: number) => {
    dispatch({ type: "SET_PAGE", payload: page });
  }, []);

  const handleFiltersChange = useCallback((filters: TransactionFilters) => {
    dispatch({ type: "SET_FILTERS", payload: filters });
  }, []);

  const handleRetry = useCallback(() => {
    dispatch({ type: "RETRY" });
  }, []);

  const handleTransactionClick = useCallback(
    (transaction: TransactionResponse) => {
      dispatch({ type: "OPEN_EDIT_MODAL", payload: transaction });
    },
    [],
  );

  const handleCloseModal = useCallback(() => {
    dispatch({ type: "CLOSE_EDIT_MODAL" });
    setSaveError(null);
  }, []);

  const handleSaveTransaction = useCallback(
    async (payload: UpdateTransactionPayload) => {
      if (!state.editingTransaction) return;

      setIsSaving(true);
      setSaveError(null);

      try {
        const response = await updateTransaction(
          state.editingTransaction.id,
          payload,
        );
        dispatch({ type: "TRANSACTION_UPDATED", payload: response });
      } catch (error) {
        setSaveError(getErrorMessage(error, "Failed to update transaction"));
      } finally {
        setIsSaving(false);
      }
    },
    [state.editingTransaction],
  );

  const isLoading = state.pageState === "loading";

  return (
    <div className="space-y-6">
      {/* Loading State - Initial load only */}
      {state.pageState === "loading" && state.monthsList.length === 0 && (
        <DashboardSkeleton />
      )}

      {/* Empty State */}
      {state.pageState === "empty" && (
        <div className="flex min-h-[60vh] items-center justify-center">
          <Card className="mx-auto max-w-md border-0 shadow-lg">
            <CardContent className="flex flex-col items-center gap-6 py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/20">
                <Upload className="h-8 w-8 text-violet-600 dark:text-violet-400" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-semibold tracking-tight">
                  No data yet
                </h2>
                <p className="text-sm text-muted-foreground max-w-xs">
                  Import your first Bankin&apos; CSV export to see your Money
                  Map dashboard and start tracking your 50/30/20 budget.
                </p>
              </div>
              <Button asChild className="gap-2">
                <Link href="/import">
                  <Upload className="h-4 w-4" />
                  Import Transactions
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
              Try Again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Dashboard Content */}
      {(state.pageState === "loaded" ||
        (state.pageState === "loading" && state.monthDetail)) &&
        state.monthDetail &&
        state.selectedMonth && (
          <div className="space-y-6 animate-fade-in-up">
            {/* Header Row */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
                <p className="text-sm text-muted-foreground">
                  Your Money Map overview for the selected period
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ExportButtons
                  year={state.selectedMonth.year}
                  month={state.selectedMonth.month}
                  disabled={isLoading}
                />
                <MonthSelector
                  months={state.monthsList}
                  selectedYear={state.selectedMonth.year}
                  selectedMonth={state.selectedMonth.month}
                  onMonthChange={handleMonthChange}
                  isDisabled={isLoading}
                />
              </div>
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

            {/* Metric Cards Grid */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="animate-fade-in-up opacity-0 stagger-1">
                <MetricCard
                  title="Income"
                  amount={state.monthDetail.month.total_income}
                />
              </div>
              <div className="animate-fade-in-up opacity-0 stagger-2">
                <MetricCard
                  title="Core"
                  amount={Math.abs(state.monthDetail.month.total_core)}
                  percentage={state.monthDetail.month.core_percentage}
                  isSuccess={meetsThreshold(
                    "CORE",
                    state.monthDetail.month.core_percentage,
                  )}
                />
              </div>
              <div className="animate-fade-in-up opacity-0 stagger-3">
                <MetricCard
                  title="Choice"
                  amount={Math.abs(state.monthDetail.month.total_choice)}
                  percentage={state.monthDetail.month.choice_percentage}
                  isSuccess={meetsThreshold(
                    "CHOICE",
                    state.monthDetail.month.choice_percentage,
                  )}
                />
              </div>
              <div className="animate-fade-in-up opacity-0 stagger-4">
                <MetricCard
                  title="Compound"
                  amount={Math.abs(state.monthDetail.month.total_compound)}
                  percentage={state.monthDetail.month.compound_percentage}
                  isSuccess={meetsThreshold(
                    "COMPOUND",
                    state.monthDetail.month.compound_percentage,
                  )}
                  compoundDirection={
                    state.monthDetail.month.total_compound >= 0
                      ? "positive"
                      : "negative"
                  }
                />
              </div>
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
                  onTransactionClick={handleTransactionClick}
                  isLoading={isLoading}
                  filters={state.filters}
                  onFiltersChange={handleFiltersChange}
                  selectedMonth={state.selectedMonth}
                />
              </div>
            </div>
          </div>
        )}

      {/* Transaction Edit Modal */}
      <TransactionEditModal
        key={state.editingTransaction?.id ?? "closed"}
        transaction={state.editingTransaction}
        isOpen={state.editingTransaction !== null}
        onClose={handleCloseModal}
        onSave={handleSaveTransaction}
        isSaving={isSaving}
        error={saveError}
      />
    </div>
  );
}
