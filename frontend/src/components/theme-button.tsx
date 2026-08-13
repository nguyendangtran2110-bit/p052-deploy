"use client";

import { MoonIcon, SunIcon } from "@/src/components/icons";
import { useApp } from "@/src/components/providers";

export function ThemeButton() {
  const { theme, setTheme } = useApp();
  return <button className="theme-toggle public-theme" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}>{theme === "light" ? <MoonIcon /> : <SunIcon />}<span>{theme === "light" ? "Dark" : "Light"}</span></button>;
}
