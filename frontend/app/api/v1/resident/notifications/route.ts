import { markNotificationRead, notificationSnapshot } from "@/src/mock/notification-service";
import { demoAccounts } from "@/src/mock/data";

export const dynamic = "force-dynamic";

function residentFrom(request: Request) {
  const accountId = request.headers.get("x-onbxrd-demo-principal");
  return demoAccounts.find((account) => account.id === accountId && account.role === "resident") ?? null;
}

function apiError(status: number, code: string, message: string) {
  return Response.json({ code, message }, { status });
}

export function GET(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  return Response.json({ notifications: notificationSnapshot(account.id) ?? [] });
}

export async function POST(request: Request) {
  const account = residentFrom(request);
  if (!account) return apiError(401, "authentication_required", "A Resident demo session is required.");
  const body = await request.json().catch(() => null) as Record<string, unknown> | null;
  if (!body || typeof body.notificationId !== "string") return apiError(400, "field_validation_failed", "The notification update is malformed.");
  if (body.simulateUnavailable) return Response.json({ error: "dependency_unavailable" }, { status: 503 });
  const notifications = markNotificationRead(account.id, body.notificationId);
  return notifications ? Response.json({ notifications }) : Response.json({ error: "not_found" }, { status: 404 });
}
