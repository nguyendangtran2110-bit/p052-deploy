import { NextResponse } from "next/server";
import { apiError, jsonObject, requireIdempotency, residentFrom } from "@/app/api/mock/_lib";
import { getDraft, updateDraft } from "@/src/mock/server-ticket-store";
import type { DraftValue } from "@/src/lib/ticket-contract";

export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  const draft = getDraft(account);
  return draft ? NextResponse.json(draft) : new NextResponse(null, { status: 204 });
}

export async function PATCH(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  if (!requireIdempotency(request)) return apiError(400, "idempotency_key_required", "An idempotency key is required.");
  const body = await jsonObject(request);
  if (!body || typeof body.draft_id !== "string" || !Number.isInteger(body.expected_version) || !isDraftChanges(body.changes)) {
    return apiError(400, "field_validation_failed", "The draft update is malformed.");
  }
  const result = updateDraft(account, body.draft_id, body.expected_version as number, body.changes);
  if ("draft" in result) return NextResponse.json(result.draft);
  return draftMutationError(result);
}

function isDraftChanges(value: unknown): value is Partial<DraftValue> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const changes = value as Record<string, unknown>;
  if (Object.keys(changes).some((key) => !["subject", "content", "urgency"].includes(key))) return false;
  if ("subject" in changes && (typeof changes.subject !== "string" || changes.subject.length > 120)) return false;
  if ("content" in changes && (typeof changes.content !== "string" || changes.content.length > 4000)) return false;
  if ("urgency" in changes && !["Low", "Normal", "High"].includes(String(changes.urgency))) return false;
  return Object.keys(changes).length > 0;
}

function draftMutationError(result: { error: string; current?: unknown }) {
  if (result.error === "ticket_draft_conflict") return apiError(409, result.error, "Another session changed this draft.", { current: result.current });
  if (result.error === "draft_service_unavailable") return apiError(503, result.error, "The synthetic draft service is unavailable.");
  return apiError(409, "ticket_draft_generation_gone", "The expected draft is no longer active.");
}
