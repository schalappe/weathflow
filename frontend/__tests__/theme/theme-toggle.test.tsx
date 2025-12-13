import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { createLocalStorageMock } from "../utils/test-factories";

const localStorageMock = createLocalStorageMock();

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorageMock.reset();
    document.documentElement.classList.remove("dark");
  });

  afterEach(() => {
    document.documentElement.classList.remove("dark");
  });

  it("renders Moon icon in light mode", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    // [>]: In light mode, Moon icon shows (to indicate "switch to dark").
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label", "Switch to dark mode");
    // [>]: lucide-react icons render as SVG.
    expect(button.querySelector("svg")).toBeInTheDocument();
  });

  it("renders Sun icon in dark mode", () => {
    // [>]: Set initial theme to dark via localStorage.
    localStorageMock.setItem("theme", "dark");

    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    // [>]: In dark mode, Sun icon shows (to indicate "switch to light").
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label", "Switch to light mode");
  });
});
