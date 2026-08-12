import "server-only";

import { createHash, randomUUID } from "node:crypto";
import { demoAccounts, ticketForAccount, tickets, ticketsForAccount, type DemoAccount, type Ticket } from "@/src/mock/data";
import type { DraftRecord, DraftValue } from "@/src/lib/ticket-contract";

type SubmissionRecord = { draftId: string; version: number; fingerprint: string; ticket: Ticket; ambiguityPending: boolean };
type MockTicketState = {
  drafts: Map<string, DraftRecord>;
  createdTickets: Map<string, Ticket>;
  submissions: Map<string, SubmissionRecord>;
  nextTicketNumber: number;
};

const globalStore = globalThis as typeof globalThis & { __onbxrdMockTicketState?: MockTicketState };
const state = globalStore.__onbxrdMockTicketState ??= {
  drafts: new Map(),
  createdTickets: new Map(),
  submissions: new Map(),
  nextTicketNumber: 4001,
};

const emptyDraft: DraftValue = { subject: "", content: "", urgency: "Normal" };

export function demoPrincipal(accountId: string | null): DemoAccount | null {
  return demoAccounts.find((account) => account.id === accountId) ?? null;
}

export function getDraft(account: DemoAccount) {
  return cloneDraft(state.drafts.get(account.id) ?? null);
}

export function startDraft(account: DemoAccount) {
  const existing = state.drafts.get(account.id);
  if (existing) return { outcome: "existing" as const, draft: cloneDraft(existing)! };
  const draft = createDraft(emptyDraft);
  state.drafts.set(account.id, draft);
  return { outcome: "created" as const, draft: cloneDraft(draft)! };
}

export function updateDraft(account: DemoAccount, draftId: string, expectedVersion: number, changes: Partial<DraftValue>) {
  const current = state.drafts.get(account.id);
  const generationError = checkGeneration(current, draftId, expectedVersion);
  if (generationError) return generationError;
  const nextValue = { ...current!.value, ...changes };
  if (nextValue.subject.toLowerCase().includes("[simulate unavailable]")) return { error: "draft_service_unavailable" as const };
  const next = createDraft(nextValue, current!.draftId, current!.version + 1);
  state.drafts.set(account.id, next);
  return { draft: cloneDraft(next)! };
}

export function replaceDraft(account: DemoAccount, draftId: string, expectedVersion: number) {
  const current = state.drafts.get(account.id);
  const generationError = checkGeneration(current, draftId, expectedVersion);
  if (generationError) return generationError;
  const next = createDraft(emptyDraft);
  state.drafts.set(account.id, next);
  return { draft: cloneDraft(next)! };
}

export function submitDraft(account: DemoAccount, draftId: string, expectedVersion: number, fingerprint: string, idempotencyKey: string) {
  const submissionKey = `${account.id}:${idempotencyKey}`;
  const prior = state.submissions.get(submissionKey);
  if (prior) {
    if (prior.draftId !== draftId || prior.version !== expectedVersion || prior.fingerprint !== fingerprint) return { error: "idempotency_key_reused" as const };
    prior.ambiguityPending = false;
    return { ticket: cloneTicket(prior.ticket), simulatedUnknown: false };
  }

  const current = state.drafts.get(account.id);
  const generationError = checkGeneration(current, draftId, expectedVersion);
  if (generationError) return generationError;
  if (current!.fieldFingerprint !== fingerprint) return { error: "ticket_draft_conflict" as const, current: cloneDraft(current!)! };
  const fields: Record<string, string> = {};
  if (!current!.value.subject.trim()) fields.subject = "Enter a short subject.";
  if (!current!.value.content.trim()) fields.content = "Describe what happened and what help you need.";
  if (Object.keys(fields).length) return { error: "field_validation_failed" as const, fields };

  const ticket: Ticket = {
    ...current!.value,
    id: `TKT-DEMO-${state.nextTicketNumber++}`,
    ownerId: account.id,
    status: "Pending",
    building: account.building,
    floor: account.floors[0],
    room: roomFor(account),
    submittedAt: new Date().toISOString(),
  };
  state.createdTickets.set(ticket.id, ticket);
  state.drafts.delete(account.id);
  const simulatedUnknown = current!.value.subject.toLowerCase().includes("[simulate outcome unknown]");
  state.submissions.set(submissionKey, { draftId, version: expectedVersion, fingerprint, ticket, ambiguityPending: simulatedUnknown });
  return { ticket: cloneTicket(ticket), simulatedUnknown };
}

export function listTickets(account: DemoAccount) {
  const created = Array.from(state.createdTickets.values());
  const allowedCreated = account.role === "resident"
    ? created.filter((ticket) => ticket.ownerId === account.id)
    : created.filter((ticket) => ticket.building === account.building && (account.floors.includes("ALL_FLOORS") || account.floors.includes(ticket.floor)));
  return [...allowedCreated, ...ticketsForAccount(account)].map(cloneTicket);
}

export function getTicket(account: DemoAccount, ticketId: string) {
  const created = state.createdTickets.get(ticketId);
  if (created) return listTickets(account).find((ticket) => ticket.id === ticketId) ?? null;
  return ticketForAccount(account, ticketId) ?? null;
}

export function fingerprint(value: DraftValue) {
  const canonicalUrgency = value.urgency.toUpperCase();
  return createHash("sha256").update([value.subject.normalize("NFC"), value.content.normalize("NFC"), canonicalUrgency].join("\u001f"), "utf8").digest("base64url");
}

export function resetMockTicketStateForTests() {
  state.drafts.clear();
  state.createdTickets.clear();
  state.submissions.clear();
  state.nextTicketNumber = 4001;
}

function createDraft(value: DraftValue, draftId = `draft_${randomUUID()}`, version = 1): DraftRecord {
  const copied = { ...value };
  return { value: copied, draftId, version, fieldFingerprint: fingerprint(copied), updatedAt: new Date().toISOString() };
}

function checkGeneration(current: DraftRecord | undefined, draftId: string, expectedVersion: number) {
  if (!current || current.draftId !== draftId) return { error: "ticket_draft_generation_gone" as const };
  if (current.version !== expectedVersion) return { error: "ticket_draft_conflict" as const, current: cloneDraft(current)! };
  return null;
}

function roomFor(account: DemoAccount) {
  const fixture = tickets.find((ticket) => ticket.ownerId === account.id);
  return fixture?.room ?? "DEMO";
}

function cloneDraft(draft: DraftRecord | null) {
  return draft ? { ...draft, value: { ...draft.value } } : null;
}

function cloneTicket(ticket: Ticket) {
  return { ...ticket };
}
