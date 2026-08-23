"use client";

import Link from "next/link";
import type { PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { LucideIcon } from "lucide-react";
import { Badge, cn } from "@/components/ui";
import { useTickets } from "@/features/tickets/queries";
import { label } from "@/lib/format";
import type { Ticket } from "@/types";

const PREVIEW_LIMIT = 20;
const CLOSE_GRACE_MS = 100;

type TicketNavPreviewProps = {
  href: string;
  label: string;
  icon: LucideIcon;
  active: boolean;
  onNavigate: () => void;
};

function statusTone(ticket: Ticket) {
  if (ticket.status === "resolved") return "success";
  if (ticket.status === "in_progress") return "warning";
  if (ticket.status === "rejected" || ticket.status === "cancelled") return "danger";
  return "info";
}

function priorityTone(ticket: Ticket) {
  if (ticket.priority === "urgent" || ticket.priority === "high") return "danger";
  if (ticket.priority === "medium") return "warning";
  return "neutral";
}

export function TicketNavPreview({ href, label: navLabel, icon: Icon, active, onNavigate }: TicketNavPreviewProps) {
  const tickets = useTickets({ limit: PREVIEW_LIMIT });
  const triggerRef = useRef<HTMLAnchorElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const closeTimer = useRef<number | undefined>(undefined);
  const suppressFocusOpen = useRef(false);
  const [isOpen, setIsOpen] = useState(false);
  const [panelPosition, setPanelPosition] = useState({ left: 258, top: 16 });
  const panelId = useId();

  const canPreview = () => window.matchMedia("(min-width: 761px)").matches;

  const clearTimers = () => {
    window.clearTimeout(closeTimer.current);
  };

  useEffect(() => () => clearTimers(), []);

  const openPreview = () => {
    if (!canPreview()) return;
    clearTimers();
    const trigger = triggerRef.current?.getBoundingClientRect();
    if (trigger) {
      setPanelPosition({
        left: trigger.right + 12,
        top: Math.max(16, Math.min(window.innerHeight - 436, trigger.top)),
      });
    }
    setIsOpen(true);
  };

  const focusStaysInRegion = (next: EventTarget | null) => next instanceof Node && (triggerRef.current?.parentElement?.contains(next) || panelRef.current?.contains(next));

  const closePreview = () => {
    if (focusStaysInRegion(document.activeElement)) return;
    window.clearTimeout(closeTimer.current);
    closeTimer.current = window.setTimeout(() => {
      setIsOpen(false);
    }, CLOSE_GRACE_MS);
  };

  const handleNavigate = () => {
    clearTimers();
    setIsOpen(false);
    onNavigate();
  };

  const onPointerEnter = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.pointerType === "touch") return;
    openPreview();
  };

  return <div
    className={cn("ticket-nav-preview", isOpen && "ticket-nav-preview-open")}
    onPointerEnter={onPointerEnter}
    onPointerLeave={closePreview}
    onFocus={(event) => {
      if (suppressFocusOpen.current && document.activeElement === triggerRef.current) {
        suppressFocusOpen.current = false;
        return;
      }
      openPreview();
    }}
    onBlur={(event) => {
      if (!focusStaysInRegion(event.relatedTarget)) closePreview();
    }}
    onKeyDown={(event) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      clearTimers();
      setIsOpen(false);
      suppressFocusOpen.current = true;
      triggerRef.current?.focus();
    }}
  >
    <Link ref={triggerRef} href={href} onClick={handleNavigate} className={cn("side-link", active && "side-link-active")} aria-controls={panelId} aria-expanded={isOpen}>
      <Icon size={18} /><span>{navLabel}</span>
    </Link>
    {isOpen && typeof document !== "undefined" && createPortal(<section id={panelId} ref={panelRef} className="ticket-nav-preview-panel" style={panelPosition} aria-label={`${navLabel} preview`} onPointerEnter={openPreview} onPointerLeave={closePreview} onFocus={openPreview} onBlur={(event) => { if (!focusStaysInRegion(event.relatedTarget)) closePreview(); }} onKeyDown={(event) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      clearTimers();
      setIsOpen(false);
      suppressFocusOpen.current = true;
      triggerRef.current?.focus();
    }}>
      <div className="ticket-nav-preview-heading"><span>{navLabel}</span><small>Quick access</small></div>
      {tickets.isLoading && <div className="ticket-nav-preview-loading" role="status" aria-live="polite"><span className="skeleton" /><span className="skeleton" /><span className="skeleton" /></div>}
      {tickets.isError && <p className="ticket-nav-preview-message" role="status">Ticket preview is unavailable.</p>}
      {!tickets.isLoading && !tickets.isError && !(tickets.data?.items.length) && <p className="ticket-nav-preview-message">No visible tickets.</p>}
      {!tickets.isLoading && !tickets.isError && Boolean(tickets.data?.items.length) && <div className="ticket-nav-preview-list">
        {tickets.data?.items.map((ticket) => <Link key={ticket.id} href={`${href}/${ticket.id}`} className="ticket-nav-preview-row" onClick={handleNavigate}>
          <strong title={ticket.title}>{ticket.title}</strong>
          <span><Badge tone={statusTone(ticket)}>{label(ticket.status)}</Badge><Badge tone={priorityTone(ticket)}>{label(ticket.priority)}</Badge></span>
        </Link>)}
      </div>}
    </section>, document.body)}
  </div>;
}
