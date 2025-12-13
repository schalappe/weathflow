import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
import Link from "next/link";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { createLocalStorageMock } from "../utils/test-factories";

const localStorageMock = createLocalStorageMock();

// [>]: Simulated layout structure matching what layout.tsx will render.
function MockLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <header data-testid="navbar">
        <nav>
          <Link href="/">Home</Link>
          <Link href="/import">Import</Link>
        </nav>
        <ThemeToggle />
      </header>
      <main>{children}</main>
    </ThemeProvider>
  );
}

describe("Layout Integration", () => {
  beforeEach(() => {
    localStorageMock.reset();
    document.documentElement.classList.remove("dark");
  });

  afterEach(() => {
    document.documentElement.classList.remove("dark");
  });

  it("ThemeToggle appears in navigation", () => {
    render(
      <MockLayout>
        <div>Page content</div>
      </MockLayout>,
    );

    // [>]: ThemeToggle should be rendered within the header.
    const navbar = screen.getByTestId("navbar");
    const toggleButton = screen.getByRole("button", { name: /switch to/i });

    expect(navbar).toContainElement(toggleButton);
  });

  it("theme toggle works end-to-end (click toggles theme)", async () => {
    const user = userEvent.setup();

    render(
      <MockLayout>
        <div>Page content</div>
      </MockLayout>,
    );

    const toggleButton = screen.getByRole("button", { name: /switch to/i });

    // [>]: Initial state: light mode.
    expect(toggleButton).toHaveAttribute("aria-label", "Switch to dark mode");
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    // [>]: Click to switch to dark mode.
    await user.click(toggleButton);

    await waitFor(() => {
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });
    expect(toggleButton).toHaveAttribute("aria-label", "Switch to light mode");

    // [>]: Click again to switch back to light mode.
    await user.click(toggleButton);

    await waitFor(() => {
      expect(document.documentElement.classList.contains("dark")).toBe(false);
    });
    expect(toggleButton).toHaveAttribute("aria-label", "Switch to dark mode");
  });
});
