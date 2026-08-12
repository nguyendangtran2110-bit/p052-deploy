import { NextResponse } from "next/server";
import { accountFrom, apiError } from "@/app/api/mock/_lib";
import { listTickets } from "@/src/mock/server-ticket-store";

export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const account = accountFrom(request);
  if (!account) return apiError(401, "authentication_required", "A demo session is required.");
  return NextResponse.json(listTickets(account));
}
