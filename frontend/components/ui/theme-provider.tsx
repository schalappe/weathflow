"use client";

import { createContext, useCallback, useSyncExternalStore } from "react";

export type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

// [>]: Exported for use-theme hook to access.
export const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "theme";

// [>]: Subscribers notified when theme changes.
let listeners: Array<() => void> = [];

function subscribe(listener: () => void): () => void {
  listeners = [...listeners, listener];
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

function getSnapshot(): Theme {
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

// [>]: Server always returns "light" to match initial client render.
function getServerSnapshot(): Theme {
  return "light";
}

function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // [>]: localStorage unavailable, theme still works in-memory.
  }
  document.documentElement.classList.toggle("dark", theme === "dark");
  // [>]: Notify all subscribers of the change.
  listeners.forEach((listener) => listener());
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // [>]: useSyncExternalStore handles hydration correctly without causing cascading renders.
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggleTheme = useCallback(() => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
