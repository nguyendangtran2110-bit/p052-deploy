"use client";

import { useEffect, useState } from "react";
import { useApp } from "@/src/components/providers";
import { ButtonLink, PageHeader } from "@/src/components/primitives";
import { TicketList } from "@/src/components/ticket-ui";
import { listTickets } from "@/src/lib/ticket-api";
import type { Ticket } from "@/src/mock/data";

export default function ResidentTicketsPage() {
  const { account } = useApp();
  const [scoped, setScoped] = useState<Ticket[]>([]);
  useEffect(() => { if (account) void listTickets(account).then(setScoped); }, [account]);
  return <div className="page manager-page"><PageHeader title="Your tickets" description="Every submitted request, its current state, and its immutable history." action={<ButtonLink href="/resident/tickets/new?intent=new">Create ticket</ButtonLink>} /><TicketList tickets={scoped} role="resident" /></div>;
}
