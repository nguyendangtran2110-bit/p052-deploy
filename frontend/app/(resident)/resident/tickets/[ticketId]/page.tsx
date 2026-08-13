"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useApp } from "@/src/components/providers";
import { ButtonLink, Card, EmptyState, PageHeader, StatusBadge } from "@/src/components/primitives";
import { getTicket } from "@/src/lib/ticket-api";
import type { Ticket } from "@/src/mock/data";

export default function ResidentTicketDetailPage() {
  const { account } = useApp();
  const params = useParams<{ ticketId: string }>();
  const [ticket, setTicket] = useState<Ticket | null | undefined>(undefined);
  useEffect(() => { if (account) void getTicket(account, params.ticketId).then(setTicket); }, [account, params.ticketId]);
  if (ticket === undefined) return <div className="page"><PageHeader title="Loading ticket" description="Confirming the account-owned durable result." /></div>;
  if (!ticket) return <div className="page"><EmptyState title="Ticket not found" description="This ticket does not exist or is not owned by the signed-in Resident. No protected details are shown." action={<ButtonLink href="/resident/tickets">Return to your tickets</ButtonLink>} /></div>;
  return <div className="page"><PageHeader title={ticket.subject} description={`${ticket.id} · Submitted ${new Date(ticket.submittedAt).toLocaleString("en-GB")}`} action={<StatusBadge status={ticket.status} />} /><div className="detail-layout"><Card className="reveal reveal-2"><h2>Submitted snapshot</h2><p>{ticket.content}</p><dl className="detail-grid"><div><dt>Resident</dt><dd>{account?.name}</dd></div><div><dt>Building</dt><dd>{ticket.building}</dd></div><div><dt>Floor and room</dt><dd>{ticket.floor} · {ticket.room}</dd></div><div><dt>Urgency</dt><dd>{ticket.urgency}</dd></div></dl>{ticket.denialReason ? <div className="denial-panel"><h3>Why this ticket was denied</h3><p>{ticket.denialReason}</p></div> : null}</Card><Card className="timeline-card reveal reveal-3"><h2>Status history</h2><ol className="timeline"><li><span /><div><strong>Submitted</strong><small>{new Date(ticket.submittedAt).toLocaleString("en-GB")}</small></div></li>{ticket.status !== "Pending" ? <li><span /><div><strong>{ticket.status === "Resolving" ? "Manager opened the ticket" : `Ticket ${ticket.status.toLowerCase()}`}</strong><small>Durable server event</small></div></li> : null}</ol></Card></div></div>;
}
