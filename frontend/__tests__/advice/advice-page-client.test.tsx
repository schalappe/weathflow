import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AdvicePageClient } from "@/components/advice/advice-page-client";
import * as apiClient from "@/lib/api-client";
import type { MonthSummary } from "@/types";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getMonthsList: vi.fn(),
  getAdvice: vi.fn(),
  generateAdvice: vi.fn(),
}));

const mockGetMonthsList = vi.mocked(apiClient.getMonthsList);
const mockGetAdvice = vi.mocked(apiClient.getAdvice);

// [>]: Factory for creating test month data.
function createMonthSummary(year: number, month: number): MonthSummary {
  return {
    id: year * 100 + month,
    year,
    month,
    total_income: 5000,
    total_core: 2500,
    total_choice: 1500,
    total_compound: 1000,
    core_percentage: 50,
    choice_percentage: 30,
    compound_percentage: 20,
    score: 3,
    score_label: "Great",
    transaction_count: 50,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

describe("AdvicePageClient - Page State Management", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows skeleton loader in loading state", async () => {
    // [>]: Setup mock to return after a delay to catch loading state.
    mockGetMonthsList.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ months: [createMonthSummary(2025, 12)], total: 1 }),
            100,
          ),
        ),
    );

    render(<AdvicePageClient />);

    // [>]: Should show skeleton with animated pulse.
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows empty state when no months available", async () => {
    mockGetMonthsList.mockResolvedValue({ months: [], total: 0 });

    render(<AdvicePageClient />);

    await waitFor(() => {
      expect(screen.getByText("Aucun mois disponible")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Importez vos transactions pour recevoir des conseils personnalisés.",
      ),
    ).toBeInTheDocument();

    // [>]: Should have link to import page.
    const importLink = screen.getByRole("link", {
      name: /Importer des transactions/i,
    });
    expect(importLink).toHaveAttribute("href", "/import");
  });

  it("shows error state with retry button on error", async () => {
    mockGetMonthsList.mockRejectedValue(new Error("Network error"));

    render(<AdvicePageClient />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /Réessayer/i }),
    ).toBeInTheDocument();
  });

  it("shows loaded state with MonthSelector and AdvicePanel", async () => {
    const months = [createMonthSummary(2025, 12), createMonthSummary(2025, 11)];
    mockGetMonthsList.mockResolvedValue({ months, total: 2 });

    // [>]: Mock advice API for AdvicePanelContent.
    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
    });

    render(<AdvicePageClient />);

    await waitFor(() => {
      expect(screen.getByText("Conseils personnalisés")).toBeInTheDocument();
    });

    // [>]: Should show month selector with loaded months.
    expect(
      screen.getByRole("combobox", { name: /Sélectionner le mois/i }),
    ).toBeInTheDocument();

    // [>]: Should show advice panel content area.
    expect(
      screen.getByText(
        "Recommandations IA basées sur vos habitudes de dépenses",
      ),
    ).toBeInTheDocument();
  });
});

describe("AdvicePageClient - User Interactions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("retries loading months when retry button clicked", async () => {
    const user = userEvent.setup();

    // [>]: First call fails, second succeeds.
    mockGetMonthsList
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        months: [createMonthSummary(2025, 12)],
        total: 1,
      });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
    });

    render(<AdvicePageClient />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Réessayer/i }));

    await waitFor(() => {
      expect(mockGetMonthsList).toHaveBeenCalledTimes(2);
    });

    // [>]: Should now show loaded state.
    await waitFor(() => {
      expect(screen.getByText("Conseils personnalisés")).toBeInTheDocument();
    });
  });

  it("auto-selects most recent month on load", async () => {
    const months = [
      createMonthSummary(2025, 12), // Most recent (first in array)
      createMonthSummary(2025, 11),
      createMonthSummary(2025, 10),
    ];
    mockGetMonthsList.mockResolvedValue({ months, total: 3 });

    // [>]: Expect advice to be fetched for the most recent month.
    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
    });

    render(<AdvicePageClient />);

    await waitFor(() => {
      expect(mockGetAdvice).toHaveBeenCalledWith(2025, 12);
    });
  });

  it("updates AdvicePanel when month selection changes", async () => {
    const user = userEvent.setup();
    const months = [createMonthSummary(2025, 12), createMonthSummary(2025, 11)];
    mockGetMonthsList.mockResolvedValue({ months, total: 2 });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
    });

    render(<AdvicePageClient />);

    await waitFor(() => {
      expect(screen.getByText("Conseils personnalisés")).toBeInTheDocument();
    });

    // [>]: First call should be for most recent month.
    expect(mockGetAdvice).toHaveBeenCalledWith(2025, 12);

    // [>]: Open the month selector dropdown.
    const selector = screen.getByRole("combobox", {
      name: /Sélectionner le mois/i,
    });
    await user.click(selector);

    // [>]: Select November 2025.
    const novemberOption = screen.getByRole("option", {
      name: /novembre 2025/i,
    });
    await user.click(novemberOption);

    // [>]: Should fetch advice for November.
    await waitFor(() => {
      expect(mockGetAdvice).toHaveBeenCalledWith(2025, 11);
    });
  });
});
