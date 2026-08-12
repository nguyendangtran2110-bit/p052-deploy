import type { Account, TokenResponse } from "@/types";

const REFRESH_TOKEN_KEY = "onbxrd_refresh_token";
const ACCOUNT_KEY = "onbxrd_account";

let accessToken: string | null = null;
let account: Account | null = null;
let refreshPromise: Promise<TokenResponse | null> | null = null;

const canUseStorage = () => typeof window !== "undefined";

export function getAccessToken() {
  return accessToken;
}

export function getRefreshToken() {
  if (!canUseStorage()) return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function hasSession() {
  return Boolean(accessToken || getRefreshToken());
}

export function getAccount(): Account | null {
  if (account) return account;
  if (!canUseStorage()) return null;
  const stored = window.localStorage.getItem(ACCOUNT_KEY);
  if (!stored) return null;
  try {
    account = JSON.parse(stored) as Account;
    return account;
  } catch {
    return null;
  }
}

export function setSession(tokens: TokenResponse) {
  accessToken = tokens.access_token;
  account = tokens.account;
  if (canUseStorage()) {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    window.localStorage.setItem(ACCOUNT_KEY, JSON.stringify(tokens.account));
  }
  broadcast({ type: "session", account: tokens.account });
}

export function setAccount(nextAccount: Account) {
  account = nextAccount;
  if (canUseStorage()) window.localStorage.setItem(ACCOUNT_KEY, JSON.stringify(nextAccount));
}

export function clearSession() {
  accessToken = null;
  account = null;
  if (canUseStorage()) {
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    window.localStorage.removeItem(ACCOUNT_KEY);
  }
  broadcast({ type: "logout" });
}

export async function refreshAccessToken(refresh: (refreshToken: string) => Promise<TokenResponse>) {
  if (refreshPromise) return refreshPromise;
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  refreshPromise = refresh(refreshToken)
    .then((tokens) => {
      setSession(tokens);
      return tokens;
    })
    .catch(() => {
      clearSession();
      return null;
    })
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

export async function bootstrapSession(refresh: (refreshToken: string) => Promise<TokenResponse>) {
  if (accessToken && account) return account;
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  const tokens = await refreshAccessToken(refresh);
  return tokens?.account ?? null;
}

function broadcast(message: { type: "session" | "logout"; account?: Account }) {
  if (!canUseStorage()) return;
  try {
    const channel = new BroadcastChannel("onbxrd-auth");
    channel.postMessage(message);
    channel.close();
  } catch {
    // BroadcastChannel is optional; storage remains the reload fallback.
  }
}

export function subscribeToAuthChanges(onChange: () => void) {
  if (!canUseStorage()) return () => undefined;
  let channel: BroadcastChannel | null = null;
  try {
    channel = new BroadcastChannel("onbxrd-auth");
    channel.onmessage = (event) => {
      if (event.data?.type === "logout") clearSessionLocalOnly();
      if (event.data?.type === "session" && event.data.account) setAccount(event.data.account);
      onChange();
    };
  } catch {
    channel = null;
  }
  const storageHandler = () => onChange();
  window.addEventListener("storage", storageHandler);
  return () => {
    channel?.close();
    window.removeEventListener("storage", storageHandler);
  };
}

function clearSessionLocalOnly() {
  accessToken = null;
  account = null;
  if (canUseStorage()) {
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    window.localStorage.removeItem(ACCOUNT_KEY);
  }
}
