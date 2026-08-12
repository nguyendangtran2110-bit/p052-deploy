import { NextResponse } from "next/server";
import { accountFrom, apiError } from "@/app/api/mock/_lib";
import { getTicket } from "@/src/mock/server-ticket-store";

export const dynamic = "force-dynamic";

export async function GET(request: Request, context: { params: Promise<{ ticketId: string }> }) {
  const account = accountFrom(request);
  if (!account) return apiError(401, "authentication_required", "A demo session is required.");
  const { ticketId } = await context.params;
  const ticket = getTicket(account, ticketId);
  return ticket ? NextResponse.json(ticket) : new NextResponse(null, { status: 204 });
}
