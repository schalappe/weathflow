"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Sparkles,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { TransactionReviewList } from "./transaction-review-list";
import { TransactionEditModal } from "@/components/dashboard/transaction-edit-modal";
import {
  getMonthDetailAllTransactions,
  updateTransaction,
} from "@/lib/api-client";
import { formatMonthDisplay, cn } from "@/lib/utils";
import { t } from "@/lib/translations";
import type {
  MonthResult,
  TransactionResponse,
  UpdateTransactionPayload,
} from "@/types";

interface TransactionReviewSheetProps {
  isOpen: boolean;
  onClose: () => void;
  monthResults: MonthResult[];
}

// [>]: Helper to create consistent month keys for tabs.
function getMonthKey(year: number, month: number): string {
  return `${year}-${month}`;
}

export function TransactionReviewSheet({
  isOpen,
  onClose,
  monthResults,
}: TransactionReviewSheetProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // [>]: Controlled tabs with first month as default.
  const firstMonthKey =
    monthResults.length > 0
      ? getMonthKey(monthResults[0].year, monthResults[0].month)
      : "";
  const [selectedTab, setSelectedTab] = useState(firstMonthKey);

  // [>]: Transaction state per month (cached).
  const [transactionsByMonth, setTransactionsByMonth] = useState<
    Record<string, TransactionResponse[]>
  >({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // [>]: Edit modal state.
  const [editingTransaction, setEditingTransaction] =
    useState<TransactionResponse | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // [>]: Mutable low confidence counts (decremented on edit).
  const [lowConfidenceCounts, setLowConfidenceCounts] = useState<
    Record<string, number>
  >(() => {
    const counts: Record<string, number> = {};
    for (const m of monthResults) {
      counts[getMonthKey(m.year, m.month)] = m.low_confidence_count;
    }
    return counts;
  });

  // [>]: Track edited transactions count per month.
  const [editedCounts, setEditedCounts] = useState<Record<string, number>>({});

  // [>]: Scroll state for navigation arrows.
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // [>]: Check scroll position for arrow visibility.
  const updateScrollState = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    setCanScrollLeft(container.scrollLeft > 0);
    setCanScrollRight(
      container.scrollLeft < container.scrollWidth - container.clientWidth - 1,
    );
  }, []);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    updateScrollState();
    container.addEventListener("scroll", updateScrollState);
    window.addEventListener("resize", updateScrollState);

    return () => {
      container.removeEventListener("scroll", updateScrollState);
      window.removeEventListener("resize", updateScrollState);
    };
  }, [updateScrollState, isOpen]);

  // [>]: Reset state when sheet opens with new data.
  useEffect(() => {
    if (isOpen && monthResults.length > 0) {
      const firstKey = getMonthKey(monthResults[0].year, monthResults[0].month);
      setSelectedTab(firstKey);
      setTransactionsByMonth({});
      setError(null);
      setEditedCounts({});
      const counts: Record<string, number> = {};
      for (const m of monthResults) {
        counts[getMonthKey(m.year, m.month)] = m.low_confidence_count;
      }
      setLowConfidenceCounts(counts);

      // [>]: Reset scroll position after render.
      requestAnimationFrame(() => {
        updateScrollState();
      });
    }
  }, [isOpen, monthResults, updateScrollState]);

  // [>]: Fetch transactions when tab changes.
  useEffect(() => {
    if (!isOpen || !selectedTab) return;

    // [>]: Skip if already cached.
    if (transactionsByMonth[selectedTab]) return;

    const [yearStr, monthStr] = selectedTab.split("-");
    const year = parseInt(yearStr, 10);
    const month = parseInt(monthStr, 10);

    // [>]: Track if this effect was cancelled to prevent race conditions.
    let isCancelled = false;

    const fetchTransactions = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // [>]: Fetch all transactions for the month (handles pagination internally).
        const response = await getMonthDetailAllTransactions(year, month);
        if (!isCancelled) {
          setTransactionsByMonth((prev) => ({
            ...prev,
            [selectedTab]: response.transactions,
          }));
        }
      } catch (err) {
        if (!isCancelled) {
          const message =
            err instanceof Error ? err.message : "Erreur de chargement";
          setError(message);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchTransactions();

    return () => {
      isCancelled = true;
    };
    // [>]: transactionsByMonth excluded - early return guard is sufficient, including it causes unnecessary re-runs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, selectedTab]);

  const handleTransactionClick = useCallback(
    (transaction: TransactionResponse) => {
      setEditingTransaction(transaction);
      setSaveError(null);
    },
    [],
  );

  const handleCloseEditModal = useCallback(() => {
    setEditingTransaction(null);
    setSaveError(null);
  }, []);

  const handleSaveTransaction = useCallback(
    async (payload: UpdateTransactionPayload) => {
      if (!editingTransaction) return;

      setIsSaving(true);
      setSaveError(null);

      try {
        const response = await updateTransaction(
          editingTransaction.id,
          payload,
        );

        // [>]: Update local transactions list.
        setTransactionsByMonth((prev) => {
          const monthKey = selectedTab;
          const transactions = prev[monthKey] || [];
          return {
            ...prev,
            [monthKey]: transactions.map((tx) =>
              tx.id === response.transaction.id ? response.transaction : tx,
            ),
          };
        });

        // [>]: Decrement low confidence count (assume edited transaction was low-confidence).
        setLowConfidenceCounts((prev) => ({
          ...prev,
          [selectedTab]: Math.max(0, (prev[selectedTab] || 0) - 1),
        }));

        // [>]: Increment edited count for progress tracking.
        setEditedCounts((prev) => ({
          ...prev,
          [selectedTab]: (prev[selectedTab] || 0) + 1,
        }));

        setEditingTransaction(null);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Erreur de sauvegarde";
        setSaveError(message);
      } finally {
        setIsSaving(false);
      }
    },
    [editingTransaction, selectedTab],
  );

  const handleScrollLeft = useCallback(() => {
    scrollContainerRef.current?.scrollBy({ left: -200, behavior: "smooth" });
  }, []);

  const handleScrollRight = useCallback(() => {
    scrollContainerRef.current?.scrollBy({ left: 200, behavior: "smooth" });
  }, []);

  const currentTransactions = transactionsByMonth[selectedTab] || [];
  const currentLowConfidenceCount = lowConfidenceCounts[selectedTab] || 0;
  const currentEditedCount = editedCounts[selectedTab] || 0;

  // [>]: Calculate totals across all months.
  const totalTransactions = monthResults.reduce(
    (sum, m) => sum + m.transactions_categorized,
    0,
  );
  const totalLowConfidence = Object.values(lowConfidenceCounts).reduce(
    (sum, c) => sum + c,
    0,
  );
  const totalEdited = Object.values(editedCounts).reduce(
    (sum, c) => sum + c,
    0,
  );

  // [>]: Find selected month data.
  const selectedMonthData = monthResults.find(
    (m) => getMonthKey(m.year, m.month) === selectedTab,
  );

  return (
    <>
      <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <SheetContent
          side="right"
          className="review-sheet-content flex w-full flex-col gap-0 p-0 sm:max-w-[800px]"
        >
          {/* [>]: Header section with gradient background. */}
          <div className="review-sheet-header relative overflow-hidden border-b bg-gradient-to-br from-background via-background to-muted/30 px-6 pb-4 pt-6">
            {/* [>]: Decorative background element. */}
            <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary/5 blur-3xl" />

            <SheetHeader className="relative space-y-1">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                  <ClipboardList className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <SheetTitle className="text-xl">{t.review.title}</SheetTitle>
                  <SheetDescription className="text-sm">
                    {t.review.subtitle}
                  </SheetDescription>
                </div>
              </div>
            </SheetHeader>

            {/* [>]: Summary stats row. */}
            {monthResults.length > 0 && (
              <div className="relative mt-5 grid grid-cols-3 gap-3">
                <div className="review-stat-card rounded-xl border bg-card/50 p-3 backdrop-blur-sm">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Transactions</span>
                  </div>
                  <p className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
                    {totalTransactions}
                  </p>
                </div>

                <div className="review-stat-card rounded-xl border bg-card/50 p-3 backdrop-blur-sm">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    <span>À vérifier</span>
                  </div>
                  <p
                    className={cn(
                      "mt-1 text-2xl font-semibold tabular-nums",
                      totalLowConfidence > 0
                        ? "text-amber-600 dark:text-amber-400"
                        : "text-muted-foreground",
                    )}
                  >
                    {totalLowConfidence}
                  </p>
                </div>

                <div className="review-stat-card rounded-xl border bg-card/50 p-3 backdrop-blur-sm">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <CheckCircle2 className="h-3.5 w-3.5 text-compound" />
                    <span>Corrigées</span>
                  </div>
                  <p className="mt-1 text-2xl font-semibold tabular-nums text-compound-text">
                    {totalEdited}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* [>]: Month selector with horizontal scroll. */}
          {monthResults.length > 0 && (
            <div className="relative border-b bg-muted/20 px-6 py-3">
              {/* [>]: Left scroll arrow. */}
              {canScrollLeft && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute left-1 top-1/2 z-10 h-8 w-8 -translate-y-1/2 rounded-full bg-background/80 shadow-md backdrop-blur-sm hover:bg-background"
                  onClick={handleScrollLeft}
                  aria-label="Faire défiler vers la gauche"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              )}

              {/* [>]: Scrollable month pills. */}
              <div
                ref={scrollContainerRef}
                className="hide-scrollbar flex gap-2 overflow-x-auto scroll-smooth px-1 py-1"
              >
                {monthResults.map((m, index) => {
                  const key = getMonthKey(m.year, m.month);
                  const lowCount = lowConfidenceCounts[key] || 0;
                  const isSelected = selectedTab === key;

                  return (
                    <button
                      key={key}
                      onClick={() => setSelectedTab(key)}
                      className={cn(
                        "review-month-pill group relative flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all duration-200",
                        isSelected
                          ? "bg-foreground text-background shadow-lg"
                          : "bg-background text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground",
                        "animate-fade-in-up",
                      )}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <span>{formatMonthDisplay(m.year, m.month)}</span>
                      {lowCount > 0 && (
                        <span
                          className={cn(
                            "flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-xs font-semibold tabular-nums",
                            isSelected
                              ? "bg-amber-400 text-amber-950"
                              : "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400",
                          )}
                        >
                          {lowCount}
                        </span>
                      )}
                      {lowCount === 0 && m.transactions_categorized > 0 && (
                        <CheckCircle2
                          className={cn(
                            "h-4 w-4",
                            isSelected
                              ? "text-compound"
                              : "text-compound/60 group-hover:text-compound",
                          )}
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* [>]: Right scroll arrow. */}
              {canScrollRight && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 z-10 h-8 w-8 -translate-y-1/2 rounded-full bg-background/80 shadow-md backdrop-blur-sm hover:bg-background"
                  onClick={handleScrollRight}
                  aria-label="Faire défiler vers la droite"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}

          {/* [>]: Main content area. */}
          <div className="flex-1 overflow-hidden">
            {monthResults.length === 0 ? (
              <div className="flex h-full items-center justify-center p-6">
                <p className="text-sm text-muted-foreground">
                  {t.review.noTransactions}
                </p>
              </div>
            ) : error ? (
              <div className="p-6">
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </div>
            ) : (
              <div className="h-full px-6 py-4">
                {/* [>]: Current month header. */}
                {selectedMonthData && (
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold">
                        {formatMonthDisplay(
                          selectedMonthData.year,
                          selectedMonthData.month,
                        )}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {currentTransactions.length} {t.review.transactions}
                        {currentLowConfidenceCount > 0 && (
                          <span className="ml-1 text-amber-600 dark:text-amber-400">
                            · {currentLowConfidenceCount}{" "}
                            {t.review.lowConfidence}
                          </span>
                        )}
                        {currentEditedCount > 0 && (
                          <span className="ml-1 text-compound-text">
                            · {currentEditedCount} corrigée
                            {currentEditedCount > 1 ? "s" : ""}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                )}

                <TransactionReviewList
                  transactions={currentTransactions}
                  lowConfidenceCount={currentLowConfidenceCount}
                  isLoading={isLoading}
                  onTransactionClick={handleTransactionClick}
                />
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* [>]: Edit modal rendered outside Sheet to avoid z-index issues. */}
      <TransactionEditModal
        key={editingTransaction?.id ?? "closed"}
        transaction={editingTransaction}
        isOpen={editingTransaction !== null}
        onClose={handleCloseEditModal}
        onSave={handleSaveTransaction}
        isSaving={isSaving}
        error={saveError}
      />
    </>
  );
}
