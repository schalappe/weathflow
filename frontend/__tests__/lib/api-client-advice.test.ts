import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  deleteActivePriority,
  generateAdvice,
  getActivePriority,
  getAdvice,
  putActivePriority,
} from "@/lib/api-client";
import { createMockAdviceData } from "@/__tests__/utils/test-factories";

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
        advice: createMockAdviceData(),
        generated_at: "2025-12-11T10:00:00Z",
        is_valid: true,
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
      expect(result.advice?.outputs[0].type).toBe("recommendation");
    });

    it("returns exists=false when no advice exists", async () => {
      const mockResponse = {
        success: true,
        advice: null,
        generated_at: null,
        is_valid: false,
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
        advice: createMockAdviceData(),
        generated_at: "2025-12-11T10:00:00Z",
        is_valid: true,
        was_cached: false,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await generateAdvice(2025, 12, { regenerate: false });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/generate"),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            year: 2025,
            month: 12,
            regenerate: false,
            remember_priority: true,
          }),
        }),
      );
    });

    it("sends correct payload with regenerate=true", async () => {
      const mockResponse = {
        success: true,
        advice: createMockAdviceData(),
        generated_at: "2025-12-11T11:00:00Z",
        is_valid: true,
        was_cached: false,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await generateAdvice(2025, 12, { regenerate: true });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/generate"),
        expect.objectContaining({
          body: JSON.stringify({
            year: 2025,
            month: 12,
            regenerate: true,
            remember_priority: true,
          }),
        }),
      );
    });

    it("returns typed GenerateAdviceResponse on success", async () => {
      const mockResponse = {
        success: true,
        advice: createMockAdviceData(),
        generated_at: "2025-12-11T10:00:00Z",
        is_valid: true,
        was_cached: true,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await generateAdvice(2025, 12);

      expect(result.success).toBe(true);
      expect(result.was_cached).toBe(true);
      expect(result.advice.outputs).toHaveLength(1);
    });

    it("sends session-only active priority", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            advice: createMockAdviceData(),
            generated_at: "2026-08-02T12:00:00Z",
            is_valid: true,
            was_cached: false,
          }),
      });

      await generateAdvice(2025, 12, {
        regenerate: true,
        activePriority: {
          goal: "Fonds d'urgence",
          target: "6 000 €",
          deadline: null,
        },
        rememberPriority: false,
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/generate"),
        expect.objectContaining({
          body: JSON.stringify({
            year: 2025,
            month: 12,
            regenerate: true,
            active_priority: {
              goal: "Fonds d'urgence",
              target: "6 000 €",
              deadline: null,
            },
            remember_priority: false,
          }),
        }),
      );
    });

    it("persists unknown clarification as an abstention", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            advice: createMockAdviceData(),
            generated_at: "2026-08-02T12:00:00Z",
            is_valid: true,
            was_cached: false,
          }),
      });

      await generateAdvice(2025, 12, {
        regenerate: true,
        clarificationAction: "unknown",
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/advice/generate"),
        expect.objectContaining({
          body: JSON.stringify({
            year: 2025,
            month: 12,
            regenerate: true,
            remember_priority: true,
            clarification_action: "unknown",
          }),
        }),
      );
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

  describe("active priority context", () => {
    it("reads, corrects, and deletes through the context API", async () => {
      const response = {
        priority: {
          goal: "Fonds d'urgence",
          target: "6 000 €",
          deadline: null,
          state: "active",
          last_confirmed_at: "2026-08-02T12:00:00Z",
          valid_until: "2027-01-29T12:00:00Z",
        },
      };
      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(response),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(response),
        })
        .mockResolvedValueOnce({ ok: true });

      await expect(getActivePriority()).resolves.toEqual(response);
      await expect(
        putActivePriority({
          goal: "Fonds d'urgence",
          target: "6 000 €",
          deadline: null,
        }),
      ).resolves.toEqual(response);
      await expect(deleteActivePriority()).resolves.toBeUndefined();

      expect(global.fetch).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining("/api/advice/context/active-priority"),
        expect.objectContaining({ method: "PUT" }),
      );
      expect(global.fetch).toHaveBeenNthCalledWith(
        3,
        expect.stringContaining("/api/advice/context/active-priority"),
        { method: "DELETE" },
      );
    });
  });
});
