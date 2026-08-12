"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { SearchIcon } from "@/src/components/icons";
import { Card, EmptyState, StatusBadge } from "@/src/components/primitives";
import type { Role, Ticket, TicketStatus } from "@/src/mock/data";

const filters: Array<"All" | TicketStatus> = ["All", "Pending", "Resolving", "Resolved", "Denied"];

export function TicketList({ tickets, role }: { tickets: Ticket[]; role: Role }) {
  const [filter, setFilter] = useState<(typeof filters)[number]>("All");
  const [search, setSearch] = useState("");
  const filtered = useMemo(() => tickets.filter((ticket) => {
    const matchesStatus = filter === "All" || ticket.status === filter;
    const query = search.trim().toLowerCase();
    return matchesStatus && (!query || `${ticket.id} ${ticket.subject} ${ticket.room}`.toLowerCase().includes(query));
  }), [filter, search, tickets]);

  return (
    <>
      <Card className="filter-band reveal reveal-2">
        <label className="search-field"><SearchIcon /><span className="sr-only">Search tickets</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by subject, ticket, or room" /></label>
        <div className="chip-group" aria-label="Filter by status">
          {filters.map((item) => <button key={item} className={filter === item ? "chip selected" : "chip"} onClick={() => setFilter(item)} aria-pressed={filter === item}>{item}</button>)}
        </div>
      </Card>
      {filtered.length === 0 ? <EmptyState title="No matching tickets" description="Change the filters or search query. Your access scope has not changed." /> : (
        <div className="data-list reveal reveal-3">
          <div className="data-list-head" aria-hidden="true"><span>Ticket</span><span>Location</span><span>Urgency</span><span>Status</span><span /></div>
          {filtered.map((ticket, index) => (
            <Link className={`data-row stagger-${Math.min(index, 5)}`} href={`/${role}/tickets/${ticket.id}`} key={ticket.id}>
              <span className="row-title"><strong>{ticket.subject}</strong><small>{ticket.id} · {new Date(ticket.submittedAt).toLocaleDateString("en-GB", { day: "2-digit", month: "short" })}</small></span>
              <span data-label="Location">{ticket.building} · {ticket.floor}-{ticket.room}</span>
              <span data-label="Urgency" className={`urgency urgency-${ticket.urgency.toLowerCase()}`}>{ticket.urgency}</span>
              <span data-label="Status"><StatusBadge status={ticket.status} /></span>
              <span className="row-arrow" aria-hidden="true">→</span>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
