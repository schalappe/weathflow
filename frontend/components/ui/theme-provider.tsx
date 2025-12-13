"use client";

import { createContext, useCallback, useState } from "react";

export type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

// [>]: Exported for use-theme hook to access.
export const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "theme";

// [>]: Read initial theme from localStorage. Runs once during state initialization.
function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  try {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (stored === "light" || stored === "dark") {
      return stored;
    }
  } catch {
    // [>]: localStorage unavailable (private browsing), use default.
  }
  return "light";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // [>]: Lazy initialization reads localStorage once, avoids cascading renders.
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "light" ? "dark" : "light";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // [>]: localStorage unavailable, theme still works in-memory.
      }
      document.documentElement.classList.toggle("dark", next === "dark");
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
