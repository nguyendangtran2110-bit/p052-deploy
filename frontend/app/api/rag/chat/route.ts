import { NextResponse } from "next/server";
import { accountFrom, apiError, jsonObject } from "@/app/api/mock/_lib";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const account = accountFrom(request);
  if (!account || (account.role !== "resident" && account.role !== "manager")) {
    return apiError(401, "assistant_session_required", "Authenticated Resident or Manager session required");
  }

  const body = await jsonObject(request);
  const message = typeof body?.message === "string" ? body.message.trim() : "";
  const sessionId = typeof body?.session_id === "string" ? body.session_id.trim() : "";

  if (!message) return apiError(422, "message_required", "Message is required");
  if (message.length > 5000) return apiError(422, "message_too_long", "Message is too long");
  if (sessionId.length > 120) return apiError(422, "session_id_too_long", "Session identifier is too long");

  try {
    const backendResponse = await fetch(`${backendBaseUrl()}/api/v1/rag/chat`, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, ...(sessionId ? { session_id: sessionId } : {}) }),
    });
    const payload = await safeJson(backendResponse);

    if (!backendResponse.ok) return apiError(backendResponse.status, "rag_backend_error", "RAG assistant is unavailable");

    return NextResponse.json(managerGroundedResponse(payload, account.role), { headers: { "Cache-Control": "no-store" } });
  } catch {
    return apiError(503, "rag_backend_unavailable", "RAG assistant is unavailable");
  }
}

function backendBaseUrl() {
  return (process.env.BACKEND_API_URL ?? process.env.FASTAPI_URL ?? DEFAULT_BACKEND_URL).replace(/\/+$/, "");
}

async function safeJson(response: Response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function managerGroundedResponse(payload: unknown, role: "resident" | "manager") {
  if (role !== "manager" || !payload || typeof payload !== "object" || Array.isArray(payload)) return payload;
  const record = payload as Record<string, unknown>;
  return {
    ...(typeof record.answer === "string" ? { answer: record.answer } : {}),
    ...(Array.isArray(record.citations) ? { citations: record.citations } : {}),
    ...(typeof record.session_id === "string" ? { session_id: record.session_id } : {}),
  };
}
