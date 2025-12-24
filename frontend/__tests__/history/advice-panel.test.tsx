import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AdvicePanel } from "@/components/history/advice-panel";
import * as apiClient from "@/lib/api-client";
import {
  createMockAdviceData,
  createMockProblemArea,
} from "@/__tests__/utils/test-factories";
import type { EligibilityInfo } from "@/types";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getAdvice: vi.fn(),
  generateAdvice: vi.fn(),
}));

const mockGetAdvice = vi.mocked(apiClient.getAdvice);
const mockGenerateAdvice = vi.mocked(apiClient.generateAdvice);

// [>]: Default eligibility info for tests (can_generate=true).
const mockEligibility: EligibilityInfo = {
  can_generate: true,
  is_first_advice: false,
  reason: null,
};

describe("AdvicePanel - State Management", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows skeleton loader in loading state", async () => {
    // [>]: Setup mock to return after a delay to catch loading state.
    mockGetAdvice.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                success: true,
                advice: null,
                generated_at: null,
                exists: false,
                eligibility: mockEligibility,
              }),
            100,
          ),
        ),
    );

    render(<AdvicePanel year={2025} month={12} />);

    // [>]: Should show skeleton with animated pulse.
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows empty state when exists=false", async () => {
    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
      eligibility: mockEligibility,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Aucun conseil disponible")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Générez des conseils personnalisés basés sur vos 3 derniers mois de transactions.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /Générer des conseils/i }),
    ).toBeInTheDocument();
  });

  it("shows advice content when loaded", async () => {
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: All sections should be visible.
    expect(screen.getByText(mockAdvice.analysis)).toBeInTheDocument();
    expect(screen.getByText("Points de vigilance")).toBeInTheDocument();
    expect(screen.getByText("Recommandations")).toBeInTheDocument();
    expect(screen.getByText("Encouragements")).toBeInTheDocument();
    expect(screen.getByText(mockAdvice.encouragement)).toBeInTheDocument();
  });

  it("shows error state with retry button on error", async () => {
    mockGetAdvice.mockRejectedValue(new Error("Network error"));

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /Réessayer/i }),
    ).toBeInTheDocument();
  });

  it("trend colors are correct: red for positive, green for negative", async () => {
    const mockAdvice = createMockAdviceData({
      problem_areas: [
        createMockProblemArea({ category: "Abonnements", amount: 85, trend: "+20%" }),
        createMockProblemArea({ category: "Restaurants", amount: 120, trend: "-15%" }),
      ],
    });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("+20%")).toBeInTheDocument();
    });

    // [>]: Positive trend (+20%) should have red color class (Neutra theme).
    const positiveTrend = screen.getByText("+20%");
    expect(positiveTrend).toHaveClass("text-red-700");

    // [>]: Negative trend (-15%) should have emerald color class.
    const negativeTrend = screen.getByText("-15%");
    expect(negativeTrend).toHaveClass("text-emerald-700");
  });

  it("regenerate button shows spinner while loading", async () => {
    const user = userEvent.setup();
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    // [>]: Generate advice takes time to trigger spinner visibility.
    mockGenerateAdvice.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                success: true,
                advice: mockAdvice,
                generated_at: new Date().toISOString(),
                was_cached: false,
              }),
            100,
          ),
        ),
    );

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Régénérer/i }),
      ).toBeInTheDocument();
    });

    // [>]: Click regenerate button.
    await user.click(screen.getByRole("button", { name: /Régénérer/i }));

    // [>]: Should show loading state with spinner.
    expect(screen.getByText("Régénération...")).toBeInTheDocument();
  });
});

describe("AdvicePanel - User Interactions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("generates advice when empty state button clicked", async () => {
    const user = userEvent.setup();
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
      eligibility: mockEligibility,
    });

    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Générer des conseils/i }),
      ).toBeInTheDocument();
    });

    await user.click(
      screen.getByRole("button", { name: /Générer des conseils/i }),
    );

    // [>]: Should call generateAdvice with regenerate=false.
    await waitFor(() => {
      expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, false);
    });

    // [>]: Should show advice content after generation.
    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });
  });

  it("regenerates advice when loaded state button clicked", async () => {
    const user = userEvent.setup();
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    mockGenerateAdvice.mockResolvedValue({
      success: true,
      advice: { ...mockAdvice, analysis: "Updated analysis" },
      generated_at: new Date().toISOString(),
      was_cached: false,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Régénérer/i }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Régénérer/i }));

    // [>]: Should call generateAdvice with regenerate=true (existing advice).
    await waitFor(() => {
      expect(mockGenerateAdvice).toHaveBeenCalledWith(2025, 12, true);
    });
  });

  it("retries fetch when error retry button clicked", async () => {
    const user = userEvent.setup();

    // [>]: First call fails, second succeeds.
    mockGetAdvice
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        success: true,
        advice: null,
        generated_at: null,
        exists: false,
        eligibility: mockEligibility,
      });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Réessayer/i }));

    await waitFor(() => {
      expect(mockGetAdvice).toHaveBeenCalledTimes(2);
    });
  });

  it("refetches advice when year/month props change", async () => {
    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: null,
      generated_at: null,
      exists: false,
      eligibility: mockEligibility,
    });

    const { rerender } = render(<AdvicePanel year={2025} month={11} />);

    await waitFor(() => {
      expect(mockGetAdvice).toHaveBeenCalledWith(2025, 11);
    });

    // [>]: Change props to trigger refetch.
    rerender(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(mockGetAdvice).toHaveBeenCalledWith(2025, 12);
    });
  });

  it("shows error banner while keeping existing advice when regeneration fails", async () => {
    const user = userEvent.setup();
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    mockGenerateAdvice.mockRejectedValue(new Error("AI service unavailable"));

    render(<AdvicePanel year={2025} month={12} />);

    // [>]: Wait for advice to load.
    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: Click regenerate button.
    await user.click(screen.getByRole("button", { name: /Régénérer/i }));

    // [>]: Error banner should appear.
    await waitFor(() => {
      expect(screen.getByText("AI service unavailable")).toBeInTheDocument();
    });

    // [>]: Existing advice should still be visible (not replaced by error state).
    expect(screen.getByText(mockAdvice.analysis)).toBeInTheDocument();
    expect(screen.getByText(mockAdvice.encouragement)).toBeInTheDocument();
  });

  it("hides problem areas section when array is empty", async () => {
    const mockAdvice = createMockAdviceData({
      problem_areas: [],
    });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: Problem areas section should not be visible when empty.
    expect(screen.queryByText("Points de vigilance")).not.toBeInTheDocument();
  });

  it("hides recommendations section when array is empty", async () => {
    const mockAdvice = createMockAdviceData({
      recommendations: [],
    });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: Recommendations section should not be visible when empty.
    expect(screen.queryByText("Recommandations")).not.toBeInTheDocument();
  });

  it("shows gray color for neutral trend (0%)", async () => {
    const mockAdvice = createMockAdviceData({
      problem_areas: [
        createMockProblemArea({ category: "Neutral", amount: 100, trend: "0%" }),
      ],
    });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("0%")).toBeInTheDocument();
    });

    // [>]: Neutral trend should have gray color class.
    const neutralTrend = screen.getByText("0%");
    expect(neutralTrend).toHaveClass("text-gray-600");
  });

  it("disables regenerate button during regeneration to prevent double-submit", async () => {
    const user = userEvent.setup();
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
      eligibility: mockEligibility,
    });

    // [>]: Slow response to observe disabled state.
    mockGenerateAdvice.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                success: true,
                advice: mockAdvice,
                generated_at: new Date().toISOString(),
                was_cached: false,
              }),
            200,
          ),
        ),
    );

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Régénérer/i }),
      ).toBeInTheDocument();
    });

    const button = screen.getByRole("button", { name: /Régénérer/i });
    await user.click(button);

    // [>]: Button should be disabled during regeneration.
    expect(
      screen.getByRole("button", { name: /Régénération/i }),
    ).toBeDisabled();
  });
});

describe("AdvicePanel - Error State Actionable Guidance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows import link for data-related errors (month not found)", async () => {
    mockGetAdvice.mockRejectedValue(new Error("Month not found"));

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Month not found")).toBeInTheDocument();
    });

    // [>]: Data-related error should show import link instead of retry.
    const importLink = screen.getByRole("link", { name: /Importer/i });
    expect(importLink).toHaveAttribute("href", "/import");
    expect(
      screen.queryByRole("button", { name: /Réessayer/i }),
    ).not.toBeInTheDocument();
  });

  it("shows import link for insufficient data errors", async () => {
    mockGetAdvice.mockRejectedValue(
      new Error("Insufficient data for analysis"),
    );

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(
        screen.getByText("Insufficient data for analysis"),
      ).toBeInTheDocument();
    });

    // [>]: Insufficient data should prompt import.
    const importLink = screen.getByRole("link", { name: /Importer/i });
    expect(importLink).toHaveAttribute("href", "/import");
  });

  it("shows retry button for network errors", async () => {
    mockGetAdvice.mockRejectedValue(new Error("Network error"));

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    // [>]: Network errors should show retry, not import link.
    expect(
      screen.getByRole("button", { name: /Réessayer/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /Importer/i }),
    ).not.toBeInTheDocument();
  });

  it("shows retry button for generic server errors", async () => {
    mockGetAdvice.mockRejectedValue(new Error("Internal server error"));

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Internal server error")).toBeInTheDocument();
    });

    // [>]: Server errors can be retried.
    expect(
      screen.getByRole("button", { name: /Réessayer/i }),
    ).toBeInTheDocument();
  });
});
