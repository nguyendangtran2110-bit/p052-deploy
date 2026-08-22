"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

type Theme = "light" | "dark";
const STORAGE_KEY = "onbxrd-theme";

function preferredTheme(): Theme {
  if (typeof window === "undefined") return "light";
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // Storage can be unavailable in private browsing or restricted embeds.
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeControl({ compact = false }: { compact?: boolean }) {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const initial = preferredTheme();
    setTheme(initial);
    document.documentElement.dataset.theme = initial;
  }, []);

  function toggleTheme() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // The in-memory theme still applies when persistence is unavailable.
    }
  }

  const currentLabel = theme === "light" ? "Sáng" : "Tối";
  const nextLabel = theme === "light" ? "tối" : "sáng";
  return <button className={`theme-control${compact ? " theme-control-compact" : ""}`} type="button" onClick={toggleTheme} aria-label={`Chuyển sang giao diện ${nextLabel}`} title={`Giao diện hiện tại: ${currentLabel}. Chuyển sang ${nextLabel}`}><span className="theme-control-icon" aria-hidden="true">{theme === "light" ? <Moon size={16} /> : <Sun size={16} />}</span><span>{compact ? currentLabel : `Giao diện ${currentLabel.toLowerCase()}`}</span></button>;
}
