import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getAdvice, generateAdvice } from "@/lib/api-client";

describe("API Client - Advice Functions", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe("getAdvice", () => {
    it("returns typed GetAdviceResponse on success", async () => {
      const mockResponse = {
        success: true,
        advice: {
          analysis: "Test analysis",
          problem_areas: [],
          recommendations: ["Test recommendation"],
          encouragement: "Keep it up!",
        },
        generated_at: "2025-12-11T10:00:00Z",
        exists: true,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await getAdvice(2025, 12);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/2025/12"),
      );
      expect(result).toEqual(mockResponse);
      expect(result.exists).toBe(true);
      expect(result.advice?.analysis).toBe("Test analysis");
    });

    it("returns exists=false when no advice exists", async () => {
      const mockResponse = {
        success: true,
        advice: null,
        generated_at: null,
        exists: false,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await getAdvice(2025, 11);

      expect(result.exists).toBe(false);
      expect(result.advice).toBeNull();
    });

    it("throws error on network failure", async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error("Network failure"));

      await expect(getAdvice(2025, 12)).rejects.toThrow(
        "Unable to connect to server",
      );
    });

    it("throws error on API error response", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: "Month not found" }),
      });

      await expect(getAdvice(2025, 12)).rejects.toThrow("Month not found");
    });

    it("throws user-friendly error on malformed JSON response", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.reject(new SyntaxError("Unexpected token")),
      });

      await expect(getAdvice(2025, 12)).rejects.toThrow(
        "Server returned an invalid response",
      );
    });
  });

  describe("generateAdvice", () => {
    it("sends correct payload with regenerate=false", async () => {
      const mockResponse = {
        success: true,
        advice: {
          analysis: "Generated analysis",
          problem_areas: [],
          recommendations: [],
          encouragement: "Good job!",
        },
        generated_at: "2025-12-11T10:00:00Z",
        was_cached: false,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await generateAdvice(2025, 12, false);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/generate"),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ year: 2025, month: 12, regenerate: false }),
        }),
      );
    });

    it("sends correct payload with regenerate=true", async () => {
      const mockResponse = {
        success: true,
        advice: {
          analysis: "Regenerated analysis",
          problem_areas: [],
          recommendations: [],
          encouragement: "Excellent!",
        },
        generated_at: "2025-12-11T11:00:00Z",
        was_cached: false,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await generateAdvice(2025, 12, true);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/generate"),
        expect.objectContaining({
          body: JSON.stringify({ year: 2025, month: 12, regenerate: true }),
        }),
      );
    });

    it("returns typed GenerateAdviceResponse on success", async () => {
      const mockResponse = {
        success: true,
        advice: {
          analysis: "New analysis",
          problem_areas: [{ category: "Test", amount: 100, trend: "+10%" }],
          recommendations: ["Do this"],
          encouragement: "Nice!",
        },
        generated_at: "2025-12-11T10:00:00Z",
        was_cached: true,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await generateAdvice(2025, 12);

      expect(result.success).toBe(true);
      expect(result.was_cached).toBe(true);
      expect(result.advice.problem_areas).toHaveLength(1);
    });

    it("throws error on network failure", async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));

      await expect(generateAdvice(2025, 12)).rejects.toThrow(
        "Unable to connect to server",
      );
    });

    it("throws error on API error response", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: "AI service unavailable" }),
      });

      await expect(generateAdvice(2025, 12)).rejects.toThrow(
        "AI service unavailable",
      );
    });
  });
});
