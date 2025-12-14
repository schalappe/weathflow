import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getCashFlow } from "@/lib/api-client";
import type { CashFlowResponse } from "@/types";

describe("getCashFlow", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches cashflow with default months parameter", async () => {
    const mockResponse: CashFlowResponse = {
      data: {
        income_total: 5000,
        core_total: 2000,
        choice_total: 1000,
        compound_total: 2000,
        deficit: 0,
        core_breakdown: [],
        choice_breakdown: [],
        compound_breakdown: [],
      },
      period_months: 12,
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getCashFlow();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/months/cashflow?months=12"),
    );
    expect(result).toEqual(mockResponse);
  });

  it("fetches cashflow with custom months parameter", async () => {
    const mockResponse: CashFlowResponse = {
      data: {
        income_total: 10000,
        core_total: 4000,
        choice_total: 2000,
        compound_total: 4000,
        deficit: 0,
        core_breakdown: [],
        choice_breakdown: [],
        compound_breakdown: [],
      },
      period_months: 6,
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getCashFlow(6);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/months/cashflow?months=6"),
    );
    expect(result).toEqual(mockResponse);
  });

  it("throws error on network failure", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("Network error"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getCashFlow()).rejects.toThrow(
      "Unable to connect to server. Please check your network connection.",
    );
  });

  it("throws error on non-ok response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "Internal server error" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getCashFlow()).rejects.toThrow("Internal server error");
  });
});
