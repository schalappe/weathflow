"use client";

import { useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronRight,
  Receipt,
  Pencil,
  Briefcase,
  Home,
  ShoppingCart,
  Zap,
  Heart,
  Car,
  Shirt,
  Smartphone,
  Shield,
  CreditCard,
  Utensils,
  Music,
  Plane,
  Laptop,
  Palette,
  Gem,
  Repeat,
  Sofa,
  Gift,
  PiggyBank,
  GraduationCap,
  TrendingUp,
  MoreHorizontal,
  Circle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  formatCurrency,
  formatTransactionDate,
  cn,
  CATEGORY_BADGE_CLASSES,
} from "@/lib/utils";
import { t } from "@/lib/translations";
import {
  groupTransactionsBySubcategory,
  getSubcategoryIcon,
  translateSubcategory,
  type SubcategoryGroup as SubcategoryGroupType,
} from "@/lib/transaction-grouping";
import type { TransactionResponse, MoneyMapType } from "@/types";

// [>]: Map icon names to actual Lucide components.
const ICON_COMPONENTS: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  Briefcase,
  Home,
  ShoppingCart,
  Zap,
  Heart,
  Car,
  Shirt,
  Smartphone,
  Shield,
  CreditCard,
  Utensils,
  Music,
  Plane,
  Laptop,
  Palette,
  Gem,
  Repeat,
  Sofa,
  Gift,
  PiggyBank,
  GraduationCap,
  TrendingUp,
  MoreHorizontal,
  Circle,
};

interface GroupedTransactionListProps {
  transactions: TransactionResponse[];
  onTransactionClick: (transaction: TransactionResponse) => void;
  isLoading: boolean;
}

interface TransactionRowProps {
  transaction: TransactionResponse;
  onClick: () => void;
}

interface SubcategoryGroupComponentProps {
  group: SubcategoryGroupType;
  isExpanded: boolean;
  onToggle: () => void;
  onTransactionClick: (transaction: TransactionResponse) => void;
}

// [>]: Minimal transaction row for expanded subcategory view.
function TransactionRow({ transaction, onClick }: TransactionRowProps) {
  const isPositive = transaction.amount >= 0;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full flex items-center gap-3 py-2.5 px-4 text-left cursor-pointer transition-colors hover:bg-muted/50 focus:outline-none focus:bg-muted/50"
    >
      <span className="w-14 text-xs text-muted-foreground font-mono shrink-0">
        {formatTransactionDate(transaction.date)}
      </span>
      <span className="flex-1 text-sm truncate">{transaction.description}</span>
      {transaction.is_manually_corrected && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-[#e8b931]/10">
                <Pencil className="h-3 w-3 text-[#c9a02a] dark:text-[#f0c43d]" />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t.transactions.manuallyCorrected}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
      <span
        className={cn(
          "font-mono text-sm font-medium tabular-nums shrink-0",
          isPositive ? "text-[#788c5d] dark:text-[#8a9e6a]" : "text-foreground",
        )}
      >
        {isPositive ? "+" : ""}
        {formatCurrency(transaction.amount)}
      </span>
    </button>
  );
}

// [>]: Expandable subcategory row with transaction list.
function SubcategoryGroupComponent({
  group,
  isExpanded,
  onToggle,
  onTransactionClick,
}: SubcategoryGroupComponentProps) {
  const iconName = getSubcategoryIcon(group.subcategory);
  const IconComponent = ICON_COMPONENTS[iconName] ?? Circle;
  const translatedName = translateSubcategory(group.subcategory);
  const transactionCount = group.transactions.length;
  const countLabel =
    transactionCount === 1
      ? t.transactions.transactionCount
      : t.transactions.transactionsCount;

  const badgeClass = group.moneyMapType
    ? CATEGORY_BADGE_CLASSES[group.moneyMapType]
    : CATEGORY_BADGE_CLASSES.EXCLUDED;

  const categoryLabel = group.moneyMapType
    ? t.categories[group.moneyMapType as keyof typeof t.categories]
    : t.categories.EXCLUDED;

  return (
    <div className="border-b border-border/50 last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isExpanded}
        className="w-full flex items-center gap-3 py-3 px-4 text-left cursor-pointer transition-colors hover:bg-muted/50 focus:outline-none focus:bg-muted/50"
      >
        {/* Chevron */}
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        )}

        {/* Category icon */}
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
          <IconComponent className="h-4 w-4 text-muted-foreground" />
        </div>

        {/* Subcategory name */}
        <span className="font-medium text-sm">{translatedName}</span>

        {/* Percentage badge */}
        <Badge variant="secondary" className="text-xs shrink-0">
          {group.percentage.toFixed(1)}%
        </Badge>

        {/* Transaction count */}
        <span className="text-xs text-muted-foreground shrink-0">
          {transactionCount} {countLabel}
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Money Map type badge */}
        <Badge className={cn("text-xs shrink-0", badgeClass)}>
          {categoryLabel}
        </Badge>

        {/* Total amount */}
        <span className="font-mono text-sm font-semibold tabular-nums shrink-0">
          {formatCurrency(group.total)}
        </span>
      </button>

      {/* Expanded transaction list */}
      {isExpanded && (
        <div className="bg-muted/20 border-t border-border/30">
          {group.transactions.map((tx) => (
            <TransactionRow
              key={tx.id}
              transaction={tx}
              onClick={() => onTransactionClick(tx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// [>]: Shared empty state component for tabs with no transactions.
function EmptyState() {
  return (
    <div className="flex h-32 flex-col items-center justify-center gap-2 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
        <Receipt className="h-5 w-5 text-muted-foreground" />
      </div>
      <p className="text-sm text-muted-foreground">{t.transactions.empty}</p>
    </div>
  );
}

export function GroupedTransactionList({
  transactions,
  onTransactionClick,
  isLoading,
}: GroupedTransactionListProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  // [>]: Group transactions by flow direction and subcategory.
  const grouped = useMemo(
    () => groupTransactionsBySubcategory(transactions),
    [transactions],
  );

  const toggleSubcategory = (tab: string, subcategory: string) => {
    const key = `${tab}-${subcategory}`;
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const inputsCount = grouped.inputs.reduce(
    (sum, g) => sum + g.transactions.length,
    0,
  );
  const outputsCount = grouped.outputs.reduce(
    (sum, g) => sum + g.transactions.length,
    0,
  );

  return (
    <Card className={cn("border-0 shadow-sm", isLoading && "opacity-50")}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
            <Receipt className="h-4.5 w-4.5 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold">
              {t.transactions.title}
            </CardTitle>
            <span className="text-xs text-muted-foreground">
              {transactions.length} {t.transactions.total}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <Tabs defaultValue="outputs" className="w-full">
          <TabsList className="w-full justify-start mb-4">
            <TabsTrigger value="inputs" className="gap-1.5">
              {t.transactions.tabs.inputs}
              <Badge variant="secondary" className="ml-1 text-xs">
                {inputsCount}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="outputs" className="gap-1.5">
              {t.transactions.tabs.outputs}
              <Badge variant="secondary" className="ml-1 text-xs">
                {outputsCount}
              </Badge>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="inputs" className="mt-0">
            {grouped.inputs.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="rounded-lg border border-border/50">
                {grouped.inputs.map((group) => (
                  <SubcategoryGroupComponent
                    key={group.subcategory}
                    group={group}
                    isExpanded={expandedKeys.has(`inputs-${group.subcategory}`)}
                    onToggle={() =>
                      toggleSubcategory("inputs", group.subcategory)
                    }
                    onTransactionClick={onTransactionClick}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="outputs" className="mt-0">
            {grouped.outputs.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="rounded-lg border border-border/50">
                {grouped.outputs.map((group) => (
                  <SubcategoryGroupComponent
                    key={group.subcategory}
                    group={group}
                    isExpanded={expandedKeys.has(
                      `outputs-${group.subcategory}`,
                    )}
                    onToggle={() =>
                      toggleSubcategory("outputs", group.subcategory)
                    }
                    onTransactionClick={onTransactionClick}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
