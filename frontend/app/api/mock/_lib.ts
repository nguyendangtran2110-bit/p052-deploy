import { NextResponse } from "next/server";
import { demoPrincipal } from "@/src/mock/server-ticket-store";

export function residentFrom(request: Request) {
  const account = demoPrincipal(request.headers.get("x-onbxrd-demo-principal"));
  return account?.role === "resident" ? account : null;
}

export function accountFrom(request: Request) {
  return demoPrincipal(request.headers.get("x-onbxrd-demo-principal"));
}

export function apiError(status: number, code: string, message: string, extra: Record<string, unknown> = {}) {
  return NextResponse.json({ code, message, ...extra }, { status });
}

export async function jsonObject(request: Request) {
  try {
    const body = await request.json();
    return body && typeof body === "object" && !Array.isArray(body) ? body as Record<string, unknown> : null;
  } catch {
    return null;
  }
}

export function requireIdempotency(request: Request) {
  const key = request.headers.get("idempotency-key");
  return key && key.length <= 200 ? key : null;
}
