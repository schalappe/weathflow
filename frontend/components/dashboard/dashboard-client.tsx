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
import { MonthNavigator } from "./month-navigator";
import { GroupedTransactionList } from "./grouped-transaction-list";
import { TransactionEditModal } from "./transaction-edit-modal";
import { ExportButtons } from "./export-buttons";
import {
  getMonthsList,
  getMonthDetailAllTransactions,
  updateTransaction,
} from "@/lib/api-client";
import {
  formatMonthDisplay,
  meetsThreshold,
  getErrorMessage,
} from "@/lib/utils";
import { t } from "@/lib/translations";
import type {
  DashboardState,
  DashboardAction,
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
    <div className="space-y-6">
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
      {/* Metrics Grid: 2x2 cards + Spending Distribution skeleton */}
      <div className="grid gap-4 lg:grid-cols-3 lg:grid-rows-2">
        <Skeleton className="h-36 w-full rounded-xl" />
        <Skeleton className="h-36 w-full rounded-xl" />
        <Skeleton className="h-full min-h-[300px] w-full rounded-xl lg:row-span-2" />
        <Skeleton className="h-36 w-full rounded-xl" />
        <Skeleton className="h-36 w-full rounded-xl" />
      </div>
      {/* Row 3: Transactions skeleton */}
      <Skeleton className="h-[400px] w-full rounded-xl" />
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
        console.error("[DashboardClient] Failed to load months:", error);
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
        // [>]: Fetch all transactions for grouped view (no pagination).
        const response = await getMonthDetailAllTransactions(
          state.selectedMonth.year,
          state.selectedMonth.month,
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
    // [>]: Removed currentPage and filters from deps since grouped view fetches all transactions.
  }, [state.selectedMonth, state.pageState]);

  const handleMonthChange = useCallback((year: number, month: number) => {
    dispatch({ type: "SELECT_MONTH", payload: { year, month } });
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
                  {t.dashboard.empty.title}
                </h2>
                <p className="text-sm text-muted-foreground max-w-xs">
                  {t.dashboard.empty.description}
                </p>
              </div>
              <Button asChild className="gap-2">
                <Link href="/import">
                  <Upload className="h-4 w-4" />
                  {t.dashboard.empty.button}
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
              {t.dashboard.retry}
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
                <h1 className="text-2xl font-bold tracking-tight">
                  {t.dashboard.title}
                </h1>
                <p className="text-sm text-muted-foreground">
                  {t.dashboard.subtitle}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ExportButtons
                  year={state.selectedMonth.year}
                  month={state.selectedMonth.month}
                  disabled={isLoading}
                />
                <MonthNavigator
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

            {/* Metrics Grid: 2x2 cards + Spending Distribution (spans 2 rows) */}
            <div className="grid gap-4 lg:grid-cols-3 lg:grid-rows-[1fr_1fr]">
              {/* Income - Row 1, Col 1 */}
              <div className="animate-fade-in-up opacity-0 stagger-1 h-full">
                <MetricCard
                  category="Income"
                  amount={state.monthDetail.month.total_income}
                />
              </div>
              {/* Compound - Row 1, Col 2 */}
              <div className="animate-fade-in-up opacity-0 stagger-2 h-full">
                <MetricCard
                  category="Compound"
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
              {/* Spending Distribution - Row 1-2, Col 3 (spans 2 rows) */}
              <div className="animate-fade-in-up opacity-0 stagger-3 lg:row-span-2 h-full">
                <SpendingPieChart
                  core={state.monthDetail.month.total_core}
                  choice={state.monthDetail.month.total_choice}
                  compound={state.monthDetail.month.total_compound}
                />
              </div>
              {/* Core - Row 2, Col 1 */}
              <div className="animate-fade-in-up opacity-0 stagger-4 h-full">
                <MetricCard
                  category="Core"
                  amount={Math.abs(state.monthDetail.month.total_core)}
                  percentage={state.monthDetail.month.core_percentage}
                  isSuccess={meetsThreshold(
                    "CORE",
                    state.monthDetail.month.core_percentage,
                  )}
                />
              </div>
              {/* Choice - Row 2, Col 2 */}
              <div className="animate-fade-in-up opacity-0 stagger-5 h-full">
                <MetricCard
                  category="Choice"
                  amount={Math.abs(state.monthDetail.month.total_choice)}
                  percentage={state.monthDetail.month.choice_percentage}
                  isSuccess={meetsThreshold(
                    "CHOICE",
                    state.monthDetail.month.choice_percentage,
                  )}
                />
              </div>
            </div>

            {/* Row 3: Grouped Transactions (full width) */}
            <div className="animate-fade-in-up opacity-0 stagger-6">
              <GroupedTransactionList
                transactions={state.monthDetail.transactions}
                onTransactionClick={handleTransactionClick}
                isLoading={isLoading}
              />
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
