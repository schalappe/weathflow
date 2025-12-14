import { describe, it, expect, vi, afterEach } from "vitest";
import { isGenerationAllowed } from "@/components/history/advice-panel-content";

describe("isGenerationAllowed", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("allows current month generation", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 11, 14)); // December 2025

    expect(isGenerationAllowed(2025, 12)).toBe(true);
  });

  it("allows previous month generation", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 11, 14)); // December 2025

    expect(isGenerationAllowed(2025, 11)).toBe(true);
  });

  it("disallows months older than n-1", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 11, 14)); // December 2025

    expect(isGenerationAllowed(2025, 10)).toBe(false);
    expect(isGenerationAllowed(2025, 1)).toBe(false);
    expect(isGenerationAllowed(2024, 12)).toBe(false);
  });

  it("handles January edge case (previous month is December of previous year)", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 0, 15)); // January 2025

    // [>]: Current month (January 2025) should be allowed.
    expect(isGenerationAllowed(2025, 1)).toBe(true);

    // [>]: Previous month (December 2024) should be allowed.
    expect(isGenerationAllowed(2024, 12)).toBe(true);

    // [>]: November 2024 and older should be disallowed.
    expect(isGenerationAllowed(2024, 11)).toBe(false);
    expect(isGenerationAllowed(2024, 10)).toBe(false);
  });

  it("disallows future months", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 5, 14)); // June 2025

    expect(isGenerationAllowed(2025, 7)).toBe(false);
    expect(isGenerationAllowed(2025, 12)).toBe(false);
    expect(isGenerationAllowed(2026, 1)).toBe(false);
  });

  it("handles December edge case correctly", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 11, 31)); // December 31, 2025

    // [>]: Current month (December 2025) allowed.
    expect(isGenerationAllowed(2025, 12)).toBe(true);

    // [>]: Previous month (November 2025) allowed.
    expect(isGenerationAllowed(2025, 11)).toBe(true);

    // [>]: October 2025 and older disallowed.
    expect(isGenerationAllowed(2025, 10)).toBe(false);
  });

  it("handles year boundary transitions", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 1, 14)); // February 2025

    // [>]: Current month (February 2025) allowed.
    expect(isGenerationAllowed(2025, 2)).toBe(true);

    // [>]: Previous month (January 2025) allowed.
    expect(isGenerationAllowed(2025, 1)).toBe(true);

    // [>]: December 2024 is two months ago, disallowed.
    expect(isGenerationAllowed(2024, 12)).toBe(false);
  });
});
