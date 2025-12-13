"use client";

import { useState, useEffect, useRef } from "react";
import { CalendarIcon, ChevronDown, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn, CATEGORY_BADGE_CLASSES, getActiveFilterCount } from "@/lib/utils";
import { t } from "@/lib/translations";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { MONEY_MAP_TYPES } from "@/lib/category-options";
import type { TransactionFilters as TFilters, MoneyMapType } from "@/types";

interface TransactionFiltersProps {
  filters: TFilters;
  onFiltersChange: (filters: TFilters) => void;
  monthBounds: { minDate: Date; maxDate: Date };
  disabled?: boolean;
}

// [>]: Calculate month boundaries from year/month.
export function getMonthBounds(year: number, month: number) {
  const minDate = new Date(year, month - 1, 1);
  const maxDate = new Date(year, month, 0);
  return { minDate, maxDate };
}

export function TransactionFilters({
  filters,
  onFiltersChange,
  monthBounds,
  disabled = false,
}: TransactionFiltersProps) {
  // [>]: Local state for search input to enable debouncing.
  // Initialize with filters.searchQuery and track if it's been externally cleared.
  const [searchInput, setSearchInput] = useState(filters.searchQuery);
  const debouncedSearch = useDebounce(searchInput, 300);
  const lastExternalValueRef = useRef(filters.searchQuery);

  // [>]: Sync local input when parent resets filters (external clear).
  // Use key pattern: if parent's searchQuery changed from outside, sync local state.
  if (filters.searchQuery !== lastExternalValueRef.current) {
    lastExternalValueRef.current = filters.searchQuery;
    if (filters.searchQuery !== searchInput) {
      setSearchInput(filters.searchQuery);
    }
  }

  // [>]: Sync debounced search value to parent.
  useEffect(() => {
    if (debouncedSearch !== filters.searchQuery) {
      onFiltersChange({ ...filters, searchQuery: debouncedSearch });
    }
    // [!]: Only trigger when debouncedSearch changes to avoid infinite loops.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const activeCount = getActiveFilterCount(filters);

  const handleCategoryToggle = (category: MoneyMapType) => {
    const newCategories = filters.categoryTypes.includes(category)
      ? filters.categoryTypes.filter((c) => c !== category)
      : [...filters.categoryTypes, category];
    onFiltersChange({ ...filters, categoryTypes: newCategories });
  };

  const handleDateFromChange = (date: Date | undefined) => {
    onFiltersChange({
      ...filters,
      dateFrom: date ? date.toISOString().split("T")[0] : null,
    });
  };

  const handleDateToChange = (date: Date | undefined) => {
    onFiltersChange({
      ...filters,
      dateTo: date ? date.toISOString().split("T")[0] : null,
    });
  };

  const handleClearFilters = () => {
    setSearchInput("");
    onFiltersChange({
      categoryTypes: [],
      dateFrom: null,
      dateTo: null,
      searchQuery: "",
    });
  };

  const formatDateDisplay = (dateStr: string | null) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    // [!]: Validate date to avoid displaying "Invalid Date" to users.
    if (isNaN(date.getTime())) {
      console.warn(`[formatDateDisplay] Invalid date string: "${dateStr}"`);
      return null;
    }
    return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
  };

  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center lg:justify-center lg:gap-2">
      {/* Category Multi-Select */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            className="w-full justify-between lg:w-auto"
          >
            <span className="flex items-center gap-2">
              {filters.categoryTypes.length > 0 ? (
                <>
                  <span className="hidden sm:inline">{t.filters.categories}</span>
                  <Badge
                    variant="secondary"
                    className="rounded-full px-2 py-0.5 text-xs"
                  >
                    {filters.categoryTypes.length}
                  </Badge>
                </>
              ) : (
                t.filters.allCategories
              )}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-56 p-3" align="start">
          <div className="space-y-3">
            <p className="text-sm font-medium text-foreground">
              {t.filters.filterByCategory}
            </p>
            <div className="space-y-2">
              {MONEY_MAP_TYPES.map((category) => (
                <label
                  key={category}
                  className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-muted"
                >
                  <Checkbox
                    checked={filters.categoryTypes.includes(category)}
                    onCheckedChange={() => handleCategoryToggle(category)}
                    disabled={disabled}
                  />
                  <span className="flex items-center gap-2 text-sm">
                    <span
                      className={cn(
                        "h-2.5 w-2.5 rounded-full",
                        CATEGORY_BADGE_CLASSES[category]
                          .replace("text-white", "")
                          .trim(),
                      )}
                    />
                    {t.categories[category as keyof typeof t.categories]}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Date From Picker */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            className={cn(
              "w-full justify-start lg:w-auto",
              !filters.dateFrom && "text-muted-foreground",
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {filters.dateFrom ? formatDateDisplay(filters.dateFrom) : t.filters.from}
            {filters.dateFrom && (
              <X
                className="ml-2 h-3 w-3 opacity-50 hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDateFromChange(undefined);
                }}
              />
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={filters.dateFrom ? new Date(filters.dateFrom) : undefined}
            onSelect={handleDateFromChange}
            disabled={(date) =>
              date < monthBounds.minDate ||
              date > monthBounds.maxDate ||
              (filters.dateTo ? date > new Date(filters.dateTo) : false)
            }
            defaultMonth={monthBounds.minDate}
          />
        </PopoverContent>
      </Popover>

      {/* Date To Picker */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            className={cn(
              "w-full justify-start lg:w-auto",
              !filters.dateTo && "text-muted-foreground",
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {filters.dateTo ? formatDateDisplay(filters.dateTo) : t.filters.to}
            {filters.dateTo && (
              <X
                className="ml-2 h-3 w-3 opacity-50 hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDateToChange(undefined);
                }}
              />
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={filters.dateTo ? new Date(filters.dateTo) : undefined}
            onSelect={handleDateToChange}
            disabled={(date) =>
              date < monthBounds.minDate ||
              date > monthBounds.maxDate ||
              (filters.dateFrom ? date < new Date(filters.dateFrom) : false)
            }
            defaultMonth={monthBounds.minDate}
          />
        </PopoverContent>
      </Popover>

      {/* Search Input */}
      <div className="relative w-full lg:w-48 xl:w-56">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder={t.filters.search}
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          disabled={disabled}
          className="h-9 pl-9 pr-8"
        />
        {searchInput && (
          <button
            type="button"
            onClick={() => setSearchInput("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Clear Filters Button */}
      {activeCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClearFilters}
          disabled={disabled}
          className="w-full shrink-0 text-muted-foreground hover:text-foreground lg:w-auto"
        >
          <X className="mr-1 h-4 w-4" />
          {t.filters.clear}
          <Badge
            variant="secondary"
            className="ml-1.5 rounded-full px-1.5 py-0 text-xs"
          >
            {activeCount}
          </Badge>
        </Button>
      )}
    </div>
  );
}
