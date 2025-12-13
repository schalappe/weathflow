"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/hooks/use-theme";

// [>]: Subscribe to a no-op store that returns true on client, false on server.
// This is React 18's recommended pattern for detecting hydration completion.
const emptySubscribe = () => () => {};
const getClientSnapshot = () => true;
const getServerSnapshot = () => false;

function useHydrated() {
  return useSyncExternalStore(
    emptySubscribe,
    getClientSnapshot,
    getServerSnapshot,
  );
}

// [>]: Toggle button using existing Button component patterns.
export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const hydrated = useHydrated();

  // [>]: Render placeholder during SSR and hydration to match server output.
  if (!hydrated) {
    return (
      <Button variant="ghost" size="icon-sm" aria-label="Toggle theme">
        <span className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
    >
      {theme === "light" ? (
        <Moon className="h-4 w-4" />
      ) : (
        <Sun className="h-4 w-4" />
      )}
    </Button>
  );
}
