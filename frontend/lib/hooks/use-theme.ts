import { useContext } from "react";
import { ThemeContext } from "@/components/ui/theme-provider";

// [>]: Access theme context with fail-fast error if used outside provider.
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
