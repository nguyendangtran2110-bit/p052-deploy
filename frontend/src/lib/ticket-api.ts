"use client";

import type { DemoAccount, Ticket } from "@/src/mock/data";
import type { DraftError, DraftRecord, DraftStartResult, DraftValue, SubmitAttempt } from "@/src/lib/ticket-contract";

const ATTEMPT_KEY = "onbxrd-submit-attempt";

export class TicketApiError extends Error {
  constructor(public status: number, public detail: DraftError) {
    super(detail.message);
  }
}

export function getDraft(account: DemoAccount) {
  return request<DraftRecord | null>(account, "/api/mock/resident/ticket-draft");
}

export function startDraft(account: DemoAccount) {
  return request<DraftStartResult>(account, "/api/mock/resident/ticket-draft/start", { method: "POST", headers: mutationHeaders() });
}

export function updateDraft(account: DemoAccount, baseline: DraftRecord, changes: Partial<DraftValue>) {
  return request<DraftRecord>(account, "/api/mock/resident/ticket-draft", {
    method: "PATCH",
    headers: mutationHeaders(),
    body: JSON.stringify({ draft_id: baseline.draftId, expected_version: baseline.version, changes }),
  });
}

export function replaceDraft(account: DemoAccount, baseline: DraftRecord) {
  return request<DraftRecord>(account, "/api/mock/resident/ticket-draft/replace", {
    method: "POST",
    headers: mutationHeaders(),
    body: JSON.stringify({ draft_id: baseline.draftId, expected_version: baseline.version }),
  });
}

export function submitDraft(account: DemoAccount, attempt: SubmitAttempt) {
  return request<Ticket>(account, "/api/mock/resident/ticket-draft/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": attempt.idempotencyKey },
    body: JSON.stringify({ draft_id: attempt.draftId, expected_version: attempt.expectedVersion, field_fingerprint: attempt.fieldFingerprint }),
  });
}

export function listTickets(account: DemoAccount) {
  return request<Ticket[]>(account, "/api/mock/tickets");
}

export function getTicket(account: DemoAccount, ticketId: string) {
  return request<Ticket | null>(account, `/api/mock/tickets/${encodeURIComponent(ticketId)}`);
}

export async function createSubmitAttempt(account: DemoAccount, draft: DraftRecord): Promise<SubmitAttempt> {
  const source = ["ticket-submit:v1", draft.draftId, String(draft.version), draft.fieldFingerprint].join("\u001f");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(source));
  const idempotencyKey = toBase64Url(new Uint8Array(digest));
  return { accountId: account.id, draftId: draft.draftId, expectedVersion: draft.version, fieldFingerprint: draft.fieldFingerprint, idempotencyKey, startedAt: new Date().toISOString() };
}

export function writeSubmitAttempt(attempt: SubmitAttempt) {
  window.sessionStorage.setItem(ATTEMPT_KEY, JSON.stringify(attempt));
}

export function readSubmitAttempt(account: DemoAccount): SubmitAttempt | null {
  const raw = window.sessionStorage.getItem(ATTEMPT_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<SubmitAttempt>;
    if (parsed.accountId !== account.id || !parsed.draftId || !Number.isInteger(parsed.expectedVersion) || !parsed.fieldFingerprint || !parsed.idempotencyKey || !parsed.startedAt) {
      clearSubmitAttempt();
      return null;
    }
    return parsed as SubmitAttempt;
  } catch {
    clearSubmitAttempt();
    return null;
  }
}

export function clearSubmitAttempt() {
  window.sessionStorage.removeItem(ATTEMPT_KEY);
}

export function preserveSubmitAttemptFor(accountId: string) {
  const raw = window.sessionStorage.getItem(ATTEMPT_KEY);
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw) as Partial<SubmitAttempt>;
    if (parsed.accountId !== accountId) clearSubmitAttempt();
  } catch {
    clearSubmitAttempt();
  }
}

async function request<T>(account: DemoAccount, path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    cache: "no-store",
    headers: { "X-OnBxrd-Demo-Principal": account.id, ...init.headers },
  });
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new TicketApiError(response.status, body as DraftError);
  return body as T;
}

function mutationHeaders() {
  return { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() };
}

function toBase64Url(bytes: Uint8Array) {
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}
