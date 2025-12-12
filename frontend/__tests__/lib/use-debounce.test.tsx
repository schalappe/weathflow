import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDebounce } from "@/lib/hooks/use-debounce";

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("initial", 300));
    expect(result.current).toBe("initial");
  });

  it("returns updated value after delay", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "initial", delay: 300 } },
    );

    // [>]: Change value but don't advance time yet.
    rerender({ value: "updated", delay: 300 });
    expect(result.current).toBe("initial");

    // [>]: Advance time past the delay.
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe("updated");
  });

  it("resets timer when value changes before delay expires", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "first" } },
    );

    // [>]: Change value after 200ms (before 300ms delay).
    rerender({ value: "second" });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("first");

    // [>]: Change value again, timer should reset.
    rerender({ value: "third" });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("first");

    // [>]: After full delay from last change, value should update.
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(result.current).toBe("third");
  });

  it("clears timeout on unmount to prevent memory leaks", () => {
    const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");
    const { rerender, unmount } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "test" } },
    );

    // [>]: Trigger a pending timeout.
    rerender({ value: "updated" });
    unmount();

    // [>]: clearTimeout should be called during cleanup.
    expect(clearTimeoutSpy).toHaveBeenCalled();
    clearTimeoutSpy.mockRestore();
  });

  it("handles zero delay", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 0),
      { initialProps: { value: "initial" } },
    );

    rerender({ value: "updated" });

    // [>]: Even with 0 delay, setTimeout is async so we need to flush.
    act(() => {
      vi.advanceTimersByTime(0);
    });
    expect(result.current).toBe("updated");
  });

  it("works with different value types", () => {
    // [>]: Test with number.
    const { result: numResult, rerender: numRerender } = renderHook(
      ({ value }) => useDebounce(value, 100),
      { initialProps: { value: 0 } },
    );
    expect(numResult.current).toBe(0);
    numRerender({ value: 42 });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(numResult.current).toBe(42);

    // [>]: Test with object.
    const obj1 = { id: 1 };
    const obj2 = { id: 2 };
    const { result: objResult, rerender: objRerender } = renderHook(
      ({ value }) => useDebounce(value, 100),
      { initialProps: { value: obj1 } },
    );
    expect(objResult.current).toBe(obj1);
    objRerender({ value: obj2 });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(objResult.current).toBe(obj2);
  });

  it("updates debounced value when delay changes", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "initial", delay: 300 } },
    );

    // [>]: Change value with original delay.
    rerender({ value: "updated", delay: 300 });
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(result.current).toBe("initial");

    // [>]: Change delay - this triggers effect cleanup and new timer.
    rerender({ value: "updated", delay: 100 });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(result.current).toBe("updated");
  });
});
