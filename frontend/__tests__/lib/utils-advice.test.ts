import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { formatAdviceTimestamp } from "@/lib/utils";

describe("formatAdviceTimestamp", () => {
  const MOCK_NOW = new Date("2025-12-11T15:00:00Z");

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(MOCK_NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns 'a l'instant' for timestamps less than 1 minute ago", () => {
    const thirtySecondsAgo = new Date("2025-12-11T14:59:40Z").toISOString();
    expect(formatAdviceTimestamp(thirtySecondsAgo)).toBe("a l'instant");
  });

  it("returns relative minutes for timestamps 1-59 minutes ago", () => {
    const fiveMinutesAgo = new Date("2025-12-11T14:55:00Z").toISOString();
    expect(formatAdviceTimestamp(fiveMinutesAgo)).toBe("il y a 5 minutes");
  });

  it("returns singular minute for exactly 1 minute ago", () => {
    const oneMinuteAgo = new Date("2025-12-11T14:59:00Z").toISOString();
    expect(formatAdviceTimestamp(oneMinuteAgo)).toBe("il y a 1 minute");
  });

  it("returns relative hours for timestamps 1-23 hours ago", () => {
    const threeHoursAgo = new Date("2025-12-11T12:00:00Z").toISOString();
    expect(formatAdviceTimestamp(threeHoursAgo)).toBe("il y a 3 heures");
  });

  it("returns singular hour for exactly 1 hour ago", () => {
    const oneHourAgo = new Date("2025-12-11T14:00:00Z").toISOString();
    expect(formatAdviceTimestamp(oneHourAgo)).toBe("il y a 1 heure");
  });

  it("returns absolute date for timestamps 24+ hours ago", () => {
    const twoDaysAgo = new Date("2025-12-09T15:00:00Z").toISOString();
    const result = formatAdviceTimestamp(twoDaysAgo);
    // [>]: French locale formats as "9 decembre 2025".
    expect(result).toMatch(/9.*d.cembre.*2025/i);
  });

  it("returns 'date inconnue' for invalid date strings", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    expect(formatAdviceTimestamp("not-a-date")).toBe("date inconnue");
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it("returns absolute date for future timestamps (clock skew)", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const futureDate = new Date("2025-12-11T16:00:00Z").toISOString();
    const result = formatAdviceTimestamp(futureDate);
    // [>]: Should show actual date, not "a l'instant".
    expect(result).not.toBe("a l'instant");
    expect(result).toMatch(/11.*d.cembre.*2025/i);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it("handles empty string as invalid date", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    expect(formatAdviceTimestamp("")).toBe("date inconnue");
    consoleSpy.mockRestore();
  });
});
