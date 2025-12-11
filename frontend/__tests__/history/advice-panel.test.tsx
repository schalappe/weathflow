import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AdvicePanel } from "@/components/history/advice-panel";
import * as apiClient from "@/lib/api-client";
import { createMockAdviceData } from "@/__tests__/utils/test-factories";

// [>]: Mock the API client module.
vi.mock("@/lib/api-client", () => ({
  getAdvice: vi.fn(),
  generateAdvice: vi.fn(),
}));

const mockGetAdvice = vi.mocked(apiClient.getAdvice);
const mockGenerateAdvice = vi.mocked(apiClient.generateAdvice);

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
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Aucun conseil disponible")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Generez des conseils personnalises bases sur vos 3 derniers mois de transactions.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Generer des conseils" }),
    ).toBeInTheDocument();
  });

  it("shows advice content when loaded", async () => {
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: All sections should be visible.
    expect(screen.getByText(mockAdvice.analysis)).toBeInTheDocument();
    expect(screen.getByText("Points d'attention")).toBeInTheDocument();
    expect(screen.getByText("Recommandations")).toBeInTheDocument();
    expect(screen.getByText("Encouragement")).toBeInTheDocument();
    expect(screen.getByText(mockAdvice.encouragement)).toBeInTheDocument();
  });

  it("shows error state with retry button on error", async () => {
    mockGetAdvice.mockRejectedValue(new Error("Network error"));

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: "Reessayer" }),
    ).toBeInTheDocument();
  });

  it("trend colors are correct: red for positive, green for negative", async () => {
    const mockAdvice = createMockAdviceData({
      problem_areas: [
        { category: "Abonnements", amount: 85, trend: "+20%" },
        { category: "Restaurants", amount: 120, trend: "-15%" },
      ],
    });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("+20%")).toBeInTheDocument();
    });

    // [>]: Positive trend (+20%) should have red color class.
    const positiveTrend = screen.getByText("+20%");
    expect(positiveTrend).toHaveClass("text-red-600");

    // [>]: Negative trend (-15%) should have green color class.
    const negativeTrend = screen.getByText("-15%");
    expect(negativeTrend).toHaveClass("text-green-600");
  });

  it("regenerate button shows spinner while loading", async () => {
    const user = userEvent.setup();
    const mockAdvice = createMockAdviceData();

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
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
        screen.getByRole("button", { name: /Regenerer/ }),
      ).toBeInTheDocument();
    });

    // [>]: Click regenerate button.
    await user.click(screen.getByRole("button", { name: /Regenerer/ }));

    // [>]: Should show loading state with spinner.
    expect(screen.getByText("Regeneration...")).toBeInTheDocument();
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
        screen.getByRole("button", { name: "Generer des conseils" }),
      ).toBeInTheDocument();
    });

    await user.click(
      screen.getByRole("button", { name: "Generer des conseils" }),
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
        screen.getByRole("button", { name: /Regenerer/ }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Regenerer/ }));

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
      });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Reessayer" }));

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
    });

    mockGenerateAdvice.mockRejectedValue(new Error("AI service unavailable"));

    render(<AdvicePanel year={2025} month={12} />);

    // [>]: Wait for advice to load.
    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: Click regenerate button.
    await user.click(screen.getByRole("button", { name: /Regenerer/ }));

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
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("Analyse des tendances")).toBeInTheDocument();
    });

    // [>]: Problem areas section should not be visible when empty.
    expect(screen.queryByText("Points d'attention")).not.toBeInTheDocument();
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
      problem_areas: [{ category: "Neutral", amount: 100, trend: "0%" }],
    });

    mockGetAdvice.mockResolvedValue({
      success: true,
      advice: mockAdvice,
      generated_at: new Date().toISOString(),
      exists: true,
    });

    render(<AdvicePanel year={2025} month={12} />);

    await waitFor(() => {
      expect(screen.getByText("0%")).toBeInTheDocument();
    });

    // [>]: Neutral trend should have gray color class.
    const neutralTrend = screen.getByText("0%");
    expect(neutralTrend).toHaveClass("text-slate-500");
  });
});
