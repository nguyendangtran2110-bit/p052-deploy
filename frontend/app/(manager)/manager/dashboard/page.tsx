"use client";

import { BellIcon, StepsIcon, TicketIcon, UsersIcon } from "@/src/components/icons";
import { useApp } from "@/src/components/providers";
import { Card, PageHeader, SignalLink, StatusBadge } from "@/src/components/primitives";
import { ticketsForAccount } from "@/src/mock/data";

const workAreas = [
  { href: "/manager/tickets", title: "Ticket queue", text: "Find scoped requests without triggering a lifecycle change.", icon: TicketIcon, tone: "lagoon" },
  { href: "/manager/residents", title: "Resident directory", text: "Browse privacy-safe resident summaries inside exact grants.", icon: UsersIcon, tone: "harbor" },
  { href: "/manager/onboarding", title: "Onboarding oversight", text: "Identify incomplete and blocked steps without reminder controls.", icon: StepsIcon, tone: "ember" },
  { href: "/manager/notifications", title: "Notifications", text: "Read your inbox or preview a scoped resident campaign.", icon: BellIcon, tone: "moss" },
];

export default function ManagerDashboardPage() {
  const { account } = useApp();
  const scoped = account ? ticketsForAccount(account).slice(0, 3) : [];
  return <div className="page manager-page"><PageHeader title="Work home" description={`Current scope: ${account?.building} · ${account?.floors.includes("ALL_FLOORS") ? "all floors" : `floor ${account?.floors.join(", ")}`}.`} /><div className="work-grid reveal reveal-2">{workAreas.map(({ href, title, text, icon: Icon, tone }, index) => <Card className={`work-area tone-${tone}`} key={href}><span className="work-icon"><Icon /></span><div><h2>{title}</h2><p>{text}</p><SignalLink href={href}>Open {title.toLowerCase()}</SignalLink></div><span className="area-index" aria-hidden="true">0{index + 1}</span></Card>)}</div><Card className="recent-zone reveal reveal-3"><div className="section-heading"><div><h2>Recent scoped tickets</h2><p>Limited recent items, not an aggregate or KPI.</p></div><SignalLink href="/manager/tickets">View queue</SignalLink></div><div className="compact-list">{scoped.map((ticket) => <a href={`/manager/tickets/${ticket.id}`} key={ticket.id}><span><strong>{ticket.subject}</strong><small>{ticket.id} · Floor {ticket.floor}</small></span><StatusBadge status={ticket.status} /></a>)}</div></Card></div>;
}
