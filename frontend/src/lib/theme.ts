import { useCallback, useEffect, useState } from "react";

export type ThemeName = "light" | "dark";

export const THEME_STORAGE_KEY = "failure-lab-theme";

function readStoredTheme(): ThemeName {
  if (typeof document !== "undefined") {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr === "dark" || attr === "light") {
      return attr;
    }
  }
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === "dark" || stored === "light") {
      return stored;
    }
  } catch {
    // localStorage unavailable — fall through to the default.
  }
  return "light";
}

export function useTheme(): { theme: ThemeName; toggleTheme: () => void } {
  const [theme, setTheme] = useState<ThemeName>(readStoredTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // localStorage unavailable — the attribute alone still themes this session.
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((current) => (current === "light" ? "dark" : "light"));
  }, []);

  return { theme, toggleTheme };
}
