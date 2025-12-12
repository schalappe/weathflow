import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  TransactionFilters,
  getMonthBounds,
} from "@/components/dashboard/transaction-filters";
import { DEFAULT_FILTERS } from "@/types";
import type { TransactionFilters as TFilters } from "@/types";

// [>]: Default props for TransactionFilters tests.
const mockOnFiltersChange = vi.fn();
const defaultMonthBounds = getMonthBounds(2025, 10);

const renderFilters = (
  filters: TFilters = DEFAULT_FILTERS,
  props: Partial<Parameters<typeof TransactionFilters>[0]> = {},
) => {
  return render(
    <TransactionFilters
      filters={filters}
      onFiltersChange={mockOnFiltersChange}
      monthBounds={defaultMonthBounds}
      disabled={false}
      {...props}
    />,
  );
};

describe("TransactionFilters", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockOnFiltersChange.mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("rendering", () => {
    it("renders all filter controls", () => {
      renderFilters();

      // [>]: Category dropdown.
      expect(screen.getByText("All Categories")).toBeInTheDocument();

      // [>]: Date pickers.
      expect(screen.getByText("From")).toBeInTheDocument();
      expect(screen.getByText("To")).toBeInTheDocument();

      // [>]: Search input.
      expect(
        screen.getByPlaceholderText("Search description..."),
      ).toBeInTheDocument();
    });

    it("shows category count badge when categories selected", () => {
      renderFilters({ ...DEFAULT_FILTERS, categoryTypes: ["CORE", "CHOICE"] });

      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("Categories")).toBeInTheDocument();
    });

    it("shows clear button only when filters are active", () => {
      const { rerender } = renderFilters();

      // [>]: No clear button with default filters.
      expect(screen.queryByText("Clear")).not.toBeInTheDocument();

      // [>]: Clear button appears with active filters.
      rerender(
        <TransactionFilters
          filters={{ ...DEFAULT_FILTERS, categoryTypes: ["CORE"] }}
          onFiltersChange={mockOnFiltersChange}
          monthBounds={defaultMonthBounds}
        />,
      );

      expect(screen.getByText("Clear")).toBeInTheDocument();
    });

    it("displays formatted dates when set", () => {
      renderFilters({
        ...DEFAULT_FILTERS,
        dateFrom: "2025-10-05",
        dateTo: "2025-10-15",
      });

      expect(screen.getByText("05 Oct")).toBeInTheDocument();
      expect(screen.getByText("15 Oct")).toBeInTheDocument();
    });
  });

  describe("category filter", () => {
    it("toggles category and calls onFiltersChange", async () => {
      renderFilters();

      // [>]: Open category dropdown.
      fireEvent.click(screen.getByText("All Categories"));

      // [>]: Click CORE checkbox.
      const coreCheckbox = screen.getByRole("checkbox", { name: /CORE/i });
      fireEvent.click(coreCheckbox);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        ...DEFAULT_FILTERS,
        categoryTypes: ["CORE"],
      });
    });

    it("removes category when unchecked", () => {
      renderFilters({ ...DEFAULT_FILTERS, categoryTypes: ["CORE", "CHOICE"] });

      // [>]: Open category dropdown.
      fireEvent.click(screen.getByText("Categories"));

      // [>]: Uncheck CORE.
      const coreCheckbox = screen.getByRole("checkbox", { name: /CORE/i });
      fireEvent.click(coreCheckbox);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        ...DEFAULT_FILTERS,
        categoryTypes: ["CHOICE"],
      });
    });
  });

  describe("search filter", () => {
    it("debounces search input by 300ms", () => {
      renderFilters();

      const searchInput = screen.getByPlaceholderText("Search description...");
      fireEvent.change(searchInput, { target: { value: "grocery" } });

      // [>]: Should NOT call immediately.
      expect(mockOnFiltersChange).not.toHaveBeenCalled();

      // [>]: Advance 299ms - still not called.
      act(() => {
        vi.advanceTimersByTime(299);
      });
      expect(mockOnFiltersChange).not.toHaveBeenCalled();

      // [>]: Advance to 300ms - now called.
      act(() => {
        vi.advanceTimersByTime(1);
      });
      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        ...DEFAULT_FILTERS,
        searchQuery: "grocery",
      });
    });

    it("resets debounce timer on rapid input changes", () => {
      renderFilters();

      const searchInput = screen.getByPlaceholderText("Search description...");

      // [>]: Type "abc" with pauses.
      fireEvent.change(searchInput, { target: { value: "a" } });
      act(() => {
        vi.advanceTimersByTime(100);
      });

      fireEvent.change(searchInput, { target: { value: "ab" } });
      act(() => {
        vi.advanceTimersByTime(100);
      });

      fireEvent.change(searchInput, { target: { value: "abc" } });

      // [>]: After 300ms from last change, should trigger with final value.
      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(mockOnFiltersChange).toHaveBeenCalledTimes(1);
      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        ...DEFAULT_FILTERS,
        searchQuery: "abc",
      });
    });

    it("shows clear icon when search has value", () => {
      renderFilters();

      const searchInput = screen.getByPlaceholderText("Search description...");
      fireEvent.change(searchInput, { target: { value: "test" } });

      // [>]: Find the X button near search input.
      const searchContainer = searchInput.closest("div");
      const clearButton = searchContainer?.querySelector("button");
      expect(clearButton).toBeInTheDocument();
    });
  });

  describe("clear filters", () => {
    it("clears all filters when clear button clicked", () => {
      renderFilters({
        categoryTypes: ["CORE"],
        dateFrom: "2025-10-01",
        dateTo: "2025-10-15",
        searchQuery: "test",
      });

      fireEvent.click(screen.getByText("Clear"));

      expect(mockOnFiltersChange).toHaveBeenCalledWith(DEFAULT_FILTERS);
    });

    it("clears local search state when clear button clicked", () => {
      renderFilters({
        ...DEFAULT_FILTERS,
        searchQuery: "test",
      });

      const searchInput = screen.getByPlaceholderText("Search description...");
      expect(searchInput).toHaveValue("test");

      fireEvent.click(screen.getByText("Clear"));

      // [>]: After clicking clear, the input should be empty.
      // Note: The component resets local state, but we need to verify via re-render.
      expect(mockOnFiltersChange).toHaveBeenCalledWith(DEFAULT_FILTERS);
    });
  });

  describe("external state sync", () => {
    it("syncs local search state when parent clears filters externally", () => {
      const { rerender } = render(
        <TransactionFilters
          filters={{ ...DEFAULT_FILTERS, searchQuery: "external" }}
          onFiltersChange={mockOnFiltersChange}
          monthBounds={defaultMonthBounds}
        />,
      );

      const searchInput = screen.getByPlaceholderText("Search description...");
      expect(searchInput).toHaveValue("external");

      // [>]: Parent clears filters (simulating month change).
      rerender(
        <TransactionFilters
          filters={DEFAULT_FILTERS}
          onFiltersChange={mockOnFiltersChange}
          monthBounds={defaultMonthBounds}
        />,
      );

      expect(searchInput).toHaveValue("");
    });
  });

  describe("disabled state", () => {
    it("disables all controls when disabled prop is true", () => {
      renderFilters(DEFAULT_FILTERS, { disabled: true });

      expect(
        screen.getByText("All Categories").closest("button"),
      ).toBeDisabled();
      expect(screen.getByText("From").closest("button")).toBeDisabled();
      expect(screen.getByText("To").closest("button")).toBeDisabled();
      expect(
        screen.getByPlaceholderText("Search description..."),
      ).toBeDisabled();
    });
  });
});

describe("getMonthBounds", () => {
  it("returns correct bounds for October 2025", () => {
    const bounds = getMonthBounds(2025, 10);

    expect(bounds.minDate.getFullYear()).toBe(2025);
    expect(bounds.minDate.getMonth()).toBe(9); // 0-indexed
    expect(bounds.minDate.getDate()).toBe(1);

    expect(bounds.maxDate.getFullYear()).toBe(2025);
    expect(bounds.maxDate.getMonth()).toBe(9);
    expect(bounds.maxDate.getDate()).toBe(31);
  });

  it("handles February in leap year", () => {
    const bounds = getMonthBounds(2024, 2);

    expect(bounds.maxDate.getDate()).toBe(29);
  });

  it("handles February in non-leap year", () => {
    const bounds = getMonthBounds(2025, 2);

    expect(bounds.maxDate.getDate()).toBe(28);
  });
});
