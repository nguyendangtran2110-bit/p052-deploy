import { NextResponse } from "next/server";
import { apiError, jsonObject, requireIdempotency, residentFrom } from "@/app/api/mock/_lib";
import { submitDraft } from "@/src/mock/server-ticket-store";

export async function POST(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  const idempotencyKey = requireIdempotency(request);
  if (!idempotencyKey) return apiError(400, "idempotency_key_required", "An idempotency key is required.");
  const body = await jsonObject(request);
  if (!body || typeof body.draft_id !== "string" || !Number.isInteger(body.expected_version) || typeof body.field_fingerprint !== "string") {
    return apiError(400, "field_validation_failed", "The submission request is malformed.");
  }
  const result = submitDraft(account, body.draft_id, body.expected_version as number, body.field_fingerprint, idempotencyKey);
  if ("error" in result) {
    if (result.error === "field_validation_failed") return apiError(422, result.error, "Check the ticket fields.", { fields: result.fields });
    if (result.error === "ticket_draft_conflict") return apiError(409, result.error, "Another session changed this draft.", { current: result.current });
    if (result.error === "idempotency_key_reused") return apiError(409, result.error, "The submission key was reused with different data.");
    return apiError(409, "ticket_draft_generation_gone", "The expected draft is no longer active.");
  }
  if (result.simulatedUnknown) return apiError(503, "submission_outcome_unknown", "The request was sent, but the result could not be confirmed.");
  return NextResponse.json(result.ticket);
}
