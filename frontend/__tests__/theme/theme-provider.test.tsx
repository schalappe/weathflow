import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { useTheme } from "@/lib/hooks/use-theme";
import { createLocalStorageMock } from "../utils/test-factories";

const localStorageMock = createLocalStorageMock();

describe("ThemeProvider", () => {
  beforeEach(() => {
    localStorageMock.reset();
    document.documentElement.classList.remove("dark");
  });

  afterEach(() => {
    document.documentElement.classList.remove("dark");
  });

  it("renders children correctly", () => {
    render(
      <ThemeProvider>
        <div data-testid="child">Child content</div>
      </ThemeProvider>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("returns theme value and toggleTheme function via useTheme", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ThemeProvider>{children}</ThemeProvider>
    );

    const { result } = renderHook(() => useTheme(), { wrapper });

    // [>]: Check initial state.
    expect(result.current.theme).toBe("light");
    expect(typeof result.current.toggleTheme).toBe("function");

    // [>]: Toggle to dark.
    act(() => {
      result.current.toggleTheme();
    });
    expect(result.current.theme).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    // [>]: Toggle back to light.
    act(() => {
      result.current.toggleTheme();
    });
    expect(result.current.theme).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("throws error when useTheme is used outside ThemeProvider", () => {
    // [>]: Suppress console.error for expected error.
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      renderHook(() => useTheme());
    }).toThrow("useTheme must be used within ThemeProvider");

    consoleSpy.mockRestore();
  });

  it("persists theme changes to localStorage", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ThemeProvider>{children}</ThemeProvider>
    );

    const { result } = renderHook(() => useTheme(), { wrapper });

    // [>]: Toggle to dark and verify persistence.
    act(() => {
      result.current.toggleTheme();
    });
    expect(localStorageMock.setItem).toHaveBeenCalledWith("theme", "dark");

    // [>]: Toggle back to light and verify persistence.
    act(() => {
      result.current.toggleTheme();
    });
    expect(localStorageMock.setItem).toHaveBeenCalledWith("theme", "light");
  });
});
