"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useSyncExternalStore } from "react";
import { usePathname } from "next/navigation";
import type { DemoAccount, Theme } from "@/src/mock/data";
import { readSession } from "@/src/lib/session";

type AppContextValue = {
  account: DemoAccount | null;
  theme: Theme;
  setTheme: (theme: Theme) => void;
  reducedMotion: boolean;
  refreshSession: () => void;
};

const AppContext = createContext<AppContextValue | null>(null);
const THEME_EVENT = "onbxrd-theme";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const clientReady = useSyncExternalStore(subscribeNoop, clientReadySnapshot, serverNotReadySnapshot);
  const account = useSyncExternalStore(subscribeSession, readSession, noServerSession);
  const theme = useSyncExternalStore(subscribeTheme, readTheme, serverTheme);
  const reducedMotion = useSyncExternalStore(subscribeReducedMotion, readReducedMotion, noServerReducedMotion);

  const refreshSession = useCallback(() => window.dispatchEvent(new Event("onbxrd-session")), []);
  const setTheme = useCallback((nextTheme: Theme) => {
    document.documentElement.dataset.theme = nextTheme;
    window.localStorage.setItem("onbxrd-theme", nextTheme);
    window.dispatchEvent(new Event(THEME_EVENT));
  }, []);

  const value = useMemo(
    () => ({ account, theme, setTheme, reducedMotion, refreshSession }),
    [account, theme, setTheme, reducedMotion, refreshSession],
  );

  useRouteAnnouncement(pathname, clientReady);
  return <AppContext.Provider value={value}>{clientReady ? children : <main className="route-pending" aria-live="polite">Preparing OnBxrd…</main>}</AppContext.Provider>;
}

export function useApp() {
  const value = useContext(AppContext);
  if (!value) throw new Error("useApp must be used inside AppProviders");
  return value;
}

function subscribeSession(onStoreChange: () => void) {
  window.addEventListener("onbxrd-session", onStoreChange);
  window.addEventListener("pageshow", onStoreChange);
  return () => {
    window.removeEventListener("onbxrd-session", onStoreChange);
    window.removeEventListener("pageshow", onStoreChange);
  };
}

function subscribeTheme(onStoreChange: () => void) {
  window.addEventListener(THEME_EVENT, onStoreChange);
  return () => window.removeEventListener(THEME_EVENT, onStoreChange);
}

function subscribeReducedMotion(onStoreChange: () => void) {
  const query = window.matchMedia("(prefers-reduced-motion: reduce)");
  query.addEventListener("change", onStoreChange);
  return () => query.removeEventListener("change", onStoreChange);
}

function readTheme(): Theme {
  const stored = window.localStorage.getItem("onbxrd-theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function readReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function noServerSession() { return null; }
function serverTheme(): Theme { return "light"; }
function noServerReducedMotion() { return false; }
function subscribeNoop() { return () => {}; }
function clientReadySnapshot() { return true; }
function serverNotReadySnapshot() { return false; }

const routeTitles: Array<[RegExp, string]> = [
  [/^\/login$/, "Sign in"],
  [/^\/register$/, "Activate account"],
  [/^\/recovery$/, "Recover access"],
  [/^\/resident\/onboarding$/, "Resident onboarding"],
  [/^\/resident\/benefits$/, "Resident benefits"],
  [/^\/resident\/assistant$/, "Homie Agent"],
  [/^\/resident\/tickets$/, "Resident tickets"],
  [/^\/resident\/tickets\/new$/, "Create ticket"],
  [/^\/resident\/tickets\/[^/]+$/, "Resident ticket detail"],
  [/^\/resident\/notifications$/, "Resident notifications"],
  [/^\/resident\/profile$/, "Resident profile"],
  [/^\/manager\/dashboard$/, "Manager work home"],
  [/^\/manager\/residents$/, "Resident directory"],
  [/^\/manager\/onboarding$/, "Onboarding oversight"],
  [/^\/manager\/tickets$/, "Manager ticket queue"],
  [/^\/manager\/tickets\/[^/]+$/, "Manager ticket detail"],
  [/^\/manager\/notifications$/, "Manager notifications"],
  [/^\/manager\/profile$/, "Manager profile"],
];

function useRouteAnnouncement(pathname: string, clientReady: boolean) {
  const isInitialRoute = useRef(true);
  const previousPath = useRef(pathname);
  useEffect(() => {
    if (!clientReady) return;
    const title = routeTitles.find(([pattern]) => pattern.test(pathname))?.[1] ?? "OnBxrd";
    const expectedTitle = `${title} · OnBxrd`;
    const applyTitle = () => {
      if (document.title !== expectedTitle) document.title = expectedTitle;
    };
    applyTitle();
    const titleObserver = new MutationObserver(applyTitle);
    titleObserver.observe(document.head, { childList: true, subtree: true, characterData: true });
    const shouldFocus = previousPath.current !== pathname;
    previousPath.current = pathname;
    if (isInitialRoute.current && !shouldFocus) {
      isInitialRoute.current = false;
      return () => titleObserver.disconnect();
    }
    isInitialRoute.current = false;
    const focusHeading = () => {
      const selector = pathname.startsWith("/resident/") || pathname.startsWith("/manager/")
        ? "#main-content h1"
        : ".public-shell main h1";
      const target = Array.from(document.querySelectorAll<HTMLElement>(selector))
        .find((candidate) => isVisible(candidate));
      if (!target) return false;
      if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
      target.focus({ preventScroll: true });
      return document.activeElement === target;
    };
    let focusFrame = 0;
    const focusTimer = window.setTimeout(() => {
      focusFrame = window.requestAnimationFrame(() => focusHeading());
    }, 0);
    const routeObserver = new MutationObserver(() => {
      if (focusHeading()) routeObserver.disconnect();
    });
    routeObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "style"] });
    return () => {
      titleObserver.disconnect();
      routeObserver.disconnect();
      window.clearTimeout(focusTimer);
      window.cancelAnimationFrame(focusFrame);
    };
  }, [clientReady, pathname]);
}

function isVisible(element: HTMLElement) {
  return Boolean(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
}
