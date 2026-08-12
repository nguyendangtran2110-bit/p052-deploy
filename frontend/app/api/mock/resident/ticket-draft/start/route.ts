import { NextResponse } from "next/server";
import { apiError, requireIdempotency, residentFrom } from "@/app/api/mock/_lib";
import { startDraft } from "@/src/mock/server-ticket-store";

export async function POST(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  if (!requireIdempotency(request)) return apiError(400, "idempotency_key_required", "An idempotency key is required.");
  return NextResponse.json(startDraft(account));
}
