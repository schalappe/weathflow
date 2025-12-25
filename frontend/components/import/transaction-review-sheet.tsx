"use client";

import { useState, useCallback, useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TransactionReviewList } from "./transaction-review-list";
import { TransactionEditModal } from "@/components/dashboard/transaction-edit-modal";
import {
  getMonthDetailAllTransactions,
  updateTransaction,
} from "@/lib/api-client";
import { formatMonthDisplay } from "@/lib/utils";
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

  // [>]: Reset state when sheet opens with new data.
  useEffect(() => {
    if (isOpen && monthResults.length > 0) {
      const firstKey = getMonthKey(monthResults[0].year, monthResults[0].month);
      setSelectedTab(firstKey);
      setTransactionsByMonth({});
      setError(null);
      const counts: Record<string, number> = {};
      for (const m of monthResults) {
        counts[getMonthKey(m.year, m.month)] = m.low_confidence_count;
      }
      setLowConfidenceCounts(counts);
    }
  }, [isOpen, monthResults]);

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
  }, [isOpen, selectedTab, transactionsByMonth]);

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

  const currentTransactions = transactionsByMonth[selectedTab] || [];
  const currentLowConfidenceCount = lowConfidenceCounts[selectedTab] || 0;

  return (
    <>
      <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <SheetContent side="right" className="w-full sm:max-w-[800px]">
          <SheetHeader>
            <SheetTitle>{t.review.title}</SheetTitle>
            <SheetDescription>{t.review.subtitle}</SheetDescription>
          </SheetHeader>

          <div className="mt-6 flex-1 overflow-hidden">
            {monthResults.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {t.review.noTransactions}
              </p>
            ) : (
              <Tabs
                value={selectedTab}
                onValueChange={setSelectedTab}
                className="h-full"
              >
                <TabsList className="mb-4 w-full flex-wrap justify-start gap-1">
                  {monthResults.map((m) => {
                    const key = getMonthKey(m.year, m.month);
                    const lowCount = lowConfidenceCounts[key] || 0;

                    return (
                      <TabsTrigger key={key} value={key} className="gap-1.5">
                        {formatMonthDisplay(m.year, m.month)}
                        {lowCount > 0 && (
                          <Badge
                            variant="secondary"
                            className="ml-1 gap-0.5 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                          >
                            <AlertTriangle className="h-3 w-3" />
                            {lowCount}
                          </Badge>
                        )}
                      </TabsTrigger>
                    );
                  })}
                </TabsList>

                {monthResults.map((m) => {
                  const key = getMonthKey(m.year, m.month);
                  return (
                    <TabsContent key={key} value={key} className="mt-0">
                      {error && selectedTab === key ? (
                        <Alert variant="destructive">
                          <AlertDescription>{error}</AlertDescription>
                        </Alert>
                      ) : (
                        <TransactionReviewList
                          transactions={currentTransactions}
                          lowConfidenceCount={currentLowConfidenceCount}
                          isLoading={isLoading && selectedTab === key}
                          onTransactionClick={handleTransactionClick}
                        />
                      )}
                    </TabsContent>
                  );
                })}
              </Tabs>
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
