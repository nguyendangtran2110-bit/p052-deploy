"use client";

import { accountByUsername, demoAccounts, type DemoAccount } from "@/src/mock/data";
import { preserveSubmitAttemptFor } from "@/src/lib/ticket-api";
import { purgeClientBuffers } from "@/src/lib/volatile-store";

const SESSION_KEY = "onbxrd-demo-principal";

export function readSession(): DemoAccount | null {
  if (typeof window === "undefined") return null;
  const id = window.sessionStorage.getItem(SESSION_KEY);
  return demoAccounts.find((account) => account.id === id) ?? null;
}

export function hasSessionFor(accountId: string): boolean {
  return readSession()?.id === accountId;
}

export function login(username: string, passphrase: string): DemoAccount | null {
  const account = accountByUsername(username);
  if (!account || account.passphrase !== passphrase) return null;
  window.sessionStorage.removeItem(SESSION_KEY);
  preserveSubmitAttemptFor(account.id);
  purgeClientBuffers();
  window.sessionStorage.setItem(SESSION_KEY, account.id);
  window.dispatchEvent(new Event("onbxrd-session"));
  return account;
}

export function logout() {
  clearSession();
  window.dispatchEvent(new Event("onbxrd-session"));
}

function clearSession() {
  window.sessionStorage.removeItem(SESSION_KEY);
  window.sessionStorage.removeItem("onbxrd-submit-attempt");
  purgeClientBuffers();
}

export function handleScopeLoss({ purgeProtectedState, navigate }: { purgeProtectedState: () => void; navigate: (href: string) => void }) {
  purgeProtectedState();
  clearSession();
  navigate("/login?reason=scope-changed");
}
