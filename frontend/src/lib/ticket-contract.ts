import type { Ticket } from "@/src/mock/data";

export type DraftValue = { subject: string; content: string; urgency: "Low" | "Normal" | "High" };

export type DraftRecord = {
  value: DraftValue;
  draftId: string;
  version: number;
  fieldFingerprint: string;
  updatedAt: string;
};

export type DraftStartResult = { outcome: "created" | "existing"; draft: DraftRecord };
export type DraftErrorCode = "ticket_draft_conflict" | "ticket_draft_generation_gone" | "draft_service_unavailable" | "field_validation_failed";
export type DraftError = { code: DraftErrorCode; message: string; current?: DraftRecord; ticket?: Ticket; fields?: Record<string, string> };

export type SubmitAttempt = {
  accountId: string;
  draftId: string;
  expectedVersion: number;
  fieldFingerprint: string;
  idempotencyKey: string;
  startedAt: string;
};
