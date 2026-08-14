import { NextResponse } from "next/server";
import { apiError, jsonObject, requireIdempotency, residentFrom } from "@/app/api/mock/_lib";
import { replaceDraft } from "@/src/mock/server-ticket-store";

export async function POST(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  if (!requireIdempotency(request)) return apiError(400, "idempotency_key_required", "An idempotency key is required.");
  const body = await jsonObject(request);
  if (!body || typeof body.draft_id !== "string" || !Number.isInteger(body.expected_version)) return apiError(400, "field_validation_failed", "The replacement request is malformed.");
  const result = replaceDraft(account, body.draft_id, body.expected_version as number);
  if ("error" in result) {
    if (result.error === "ticket_draft_conflict") return apiError(409, result.error, "Another session changed this draft.", { current: result.current });
    return apiError(409, "ticket_draft_generation_gone", "The expected draft is no longer active.");
  }
  return NextResponse.json(result.draft);
}
