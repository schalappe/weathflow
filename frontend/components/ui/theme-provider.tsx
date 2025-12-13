"use client";

import { createContext, useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

// [>]: Exported for use-theme hook to access.
export const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "theme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // [>]: Default to light, inline script will set correct value before hydration.
  const [theme, setTheme] = useState<Theme>("light");

  // [>]: Sync state with localStorage on mount. Try-catch handles private browsing.
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
      if (stored === "light" || stored === "dark") {
        setTheme(stored);
        document.documentElement.classList.toggle("dark", stored === "dark");
      }
    } catch {
      // [>]: localStorage unavailable (private browsing), use default.
    }
  }, []);

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
