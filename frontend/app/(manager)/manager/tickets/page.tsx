"use client";

import { useEffect, useState } from "react";
import { useApp } from "@/src/components/providers";
import { PageHeader } from "@/src/components/primitives";
import { TicketList } from "@/src/components/ticket-ui";
import { listTickets } from "@/src/lib/ticket-api";
import type { Ticket } from "@/src/mock/data";

export default function ManagerTicketsPage() {
  const { account } = useApp();
  const [scoped, setScoped] = useState<Ticket[]>([]);
  useEffect(() => { if (account) void listTickets(account).then(setScoped); }, [account]);
  return <div className="page manager-page"><PageHeader title="Ticket queue" description="Opening this list is side-effect free. Lifecycle changes begin only after the detail route commits." /><TicketList tickets={scoped} role="manager" /></div>;
}
