"use client";

import { useState, useCallback } from "react";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { formatCurrency, formatTransactionDate } from "@/lib/utils";
import { t } from "@/lib/translations";
import { MONEY_MAP_TYPES, SUBCATEGORY_OPTIONS } from "@/lib/category-options";
import type {
  TransactionResponse,
  MoneyMapType,
  UpdateTransactionPayload,
} from "@/types";

interface TransactionEditModalProps {
  transaction: TransactionResponse | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: UpdateTransactionPayload) => Promise<void>;
  isSaving: boolean;
  error: string | null;
}

export function TransactionEditModal({
  transaction,
  isOpen,
  onClose,
  onSave,
  isSaving,
  error,
}: TransactionEditModalProps) {
  // [>]: State initialized from transaction prop; parent uses key prop to reset on transaction change.
  const [selectedType, setSelectedType] = useState<MoneyMapType | null>(
    transaction?.money_map_type ?? null,
  );
  const [selectedSubcategory, setSelectedSubcategory] = useState<string | null>(
    transaction?.money_map_subcategory ?? null,
  );

  const handleTypeChange = useCallback((value: string) => {
    const newType = value as MoneyMapType;
    setSelectedType(newType);

    // [>]: Clear subcategory when type changes, auto-select first option if available.
    const subcategories = SUBCATEGORY_OPTIONS[newType];
    if (subcategories.length > 0) {
      setSelectedSubcategory(subcategories[0]);
    } else {
      setSelectedSubcategory(null);
    }
  }, []);

  const handleSubcategoryChange = useCallback((value: string) => {
    setSelectedSubcategory(value);
  }, []);

  const handleSave = useCallback(async () => {
    if (!selectedType) return;

    await onSave({
      money_map_type: selectedType,
      money_map_subcategory: selectedSubcategory,
    });
  }, [selectedType, selectedSubcategory, onSave]);

  // [>]: Check if any changes were made compared to original transaction.
  const hasChanges =
    transaction &&
    selectedType !== null &&
    (selectedType !== transaction.money_map_type ||
      selectedSubcategory !== transaction.money_map_subcategory);

  const subcategoryOptions = selectedType
    ? SUBCATEGORY_OPTIONS[selectedType]
    : [];
  const showSubcategory =
    selectedType !== "EXCLUDED" && subcategoryOptions.length > 0;

  if (!transaction) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t.editModal.title}</DialogTitle>
          <DialogDescription>
            {t.editModal.description}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Transaction details (read-only) */}
          <div className="space-y-2 rounded-lg bg-muted/50 p-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.editModal.labels.description}</span>
              <span className="max-w-[200px] truncate font-medium">
                {transaction.description}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.editModal.labels.amount}</span>
              <span
                className={
                  transaction.amount >= 0 ? "text-[#788c5d]" : "text-[#d97757]"
                }
              >
                {transaction.amount >= 0 ? "+" : ""}
                {formatCurrency(transaction.amount)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.editModal.labels.date}</span>
              <span>{formatTransactionDate(transaction.date)}</span>
            </div>
          </div>

          {/* Category Type Select */}
          <div className="space-y-2">
            <Label htmlFor="category-type">{t.editModal.categoryType}</Label>
            <Select
              value={selectedType || undefined}
              onValueChange={handleTypeChange}
              disabled={isSaving}
            >
              <SelectTrigger id="category-type" className="w-full">
                <SelectValue placeholder={t.editModal.selectCategoryType} />
              </SelectTrigger>
              <SelectContent>
                {MONEY_MAP_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {t.categories[type as keyof typeof t.categories]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Subcategory Select */}
          {showSubcategory && (
            <div className="space-y-2">
              <Label htmlFor="subcategory">{t.editModal.subcategory}</Label>
              <Select
                value={selectedSubcategory || undefined}
                onValueChange={handleSubcategoryChange}
                disabled={isSaving}
              >
                <SelectTrigger id="subcategory" className="w-full">
                  <SelectValue placeholder={t.editModal.selectSubcategory} />
                </SelectTrigger>
                <SelectContent>
                  {subcategoryOptions.map((sub) => (
                    <SelectItem key={sub} value={sub}>
                      {t.subcategories[sub as keyof typeof t.subcategories] || sub}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Error message */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            {t.editModal.cancel}
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges || isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t.editModal.save}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
