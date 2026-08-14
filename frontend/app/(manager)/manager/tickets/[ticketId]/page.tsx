"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ExternalIcon } from "@/src/components/icons";
import { useApp } from "@/src/components/providers";
import { Button, ButtonLink, Card, EmptyState, FormField, ModalDialog, PageHeader, StatusBadge } from "@/src/components/primitives";
import { getTicket } from "@/src/lib/ticket-api";
import type { Ticket, TicketStatus } from "@/src/mock/data";
import { handleScopeLoss } from "@/src/lib/session";

type DialogKind = "resolved" | "denied" | "notify" | "zalo" | null;
type OpenResult = "opening" | "transitioned" | "already-current" | "conflict" | "unavailable";
type OpenSimulation = Extract<OpenResult, "conflict" | "unavailable">;

export default function ManagerTicketDetailPage() {
  const { account } = useApp();
  const params = useParams<{ ticketId: string }>();
  const [ticket, setTicket] = useState<Ticket | null | undefined>(undefined);
  const [status, setStatus] = useState<TicketStatus | null>(null);
  const [openResult, setOpenResult] = useState<OpenResult>("opening");
  const [dialog, setDialog] = useState<DialogKind>(null);
  const [denial, setDenial] = useState("");
  const [notifyStage, setNotifyStage] = useState<"edit" | "preview">("edit");
  const [notifySubject, setNotifySubject] = useState(ticket ? `Update for ${ticket.id}` : "");
  const [notifyContent, setNotifyContent] = useState("There is an update on your building support ticket.");
  const [message, setMessage] = useState("Opening ticket and refreshing the current server state.");
  const openTimer = useRef<number | null>(null);

  useEffect(() => {
    if (!account) return;
    let active = true;
    void getTicket(account, params.ticketId).then((result) => { if (active) setTicket(result); });
    return () => { active = false; };
  }, [account, params.ticketId]);

  const runOpen = useCallback((observedStatus: TicketStatus, simulation?: OpenSimulation) => {
    if (openTimer.current !== null) window.clearTimeout(openTimer.current);
    setOpenResult("opening");
    setStatus(observedStatus);
    setMessage("Opening ticket and refreshing the current server state.");
    setDialog(null);

    openTimer.current = window.setTimeout(() => {
      openTimer.current = null;
      if (simulation === "unavailable") {
        setOpenResult("unavailable");
        setMessage("Ticket open is unavailable. No transition was claimed and the observed state remains unchanged.");
        return;
      }
      if (simulation === "conflict") {
        const refreshedStatus = observedStatus === "Pending" ? "Resolving" : observedStatus;
        setStatus(refreshedStatus);
        setOpenResult("conflict");
        setMessage(`Another manager opened this ticket first. Safe current state refreshed to ${refreshedStatus}; a conflict notification is available in Notifications.`);
        return;
      }
      if (observedStatus === "Pending") {
        setStatus("Resolving");
        setOpenResult("transitioned");
        setMessage("Ticket opened and moved from Pending to Resolving.");
        return;
      }
      setOpenResult("already-current");
      setMessage(`Ticket is already ${observedStatus}. Current state refreshed without another transition.`);
    }, 500);
  }, []);

  useEffect(() => {
    if (!ticket) return;
    const initialize = window.setTimeout(() => {
      runOpen(ticket.status);
      setNotifySubject(`Update for ${ticket.id}`);
    }, 0);
    return () => {
      window.clearTimeout(initialize);
      if (openTimer.current !== null) window.clearTimeout(openTimer.current);
    };
  }, [runOpen, ticket]);

  if (ticket === undefined) return <div className="page"><PageHeader title="Loading ticket" description="Confirming current exact Manager scope." /></div>;
  if (!ticket) return <div className="page"><EmptyState title="Ticket unavailable" description="The resource does not exist or is outside the current exact scope. No resident details are disclosed." action={<ButtonLink href="/manager/tickets">Return to ticket queue</ButtonLink>} /></div>;

  const currentStatus = status ?? ticket.status;
  const actionsAvailable = openResult === "transitioned" || openResult === "already-current" || openResult === "conflict";

  const transition = (next: TicketStatus) => {
    if (next === "Denied" && !denial.trim()) return;
    setStatus(next);
    setMessage(`Ticket moved to ${next}. The durable timeline was updated.`);
    setDialog(null);
  };
  const closeDialog = () => { setDialog(null); setNotifyStage("edit"); };
  const purgeProtectedState = () => {
    setDialog(null);
    setDenial("");
    setNotifyStage("edit");
    setNotifySubject("");
    setNotifyContent("");
    setMessage("");
  };
  const loseScope = () => handleScopeLoss({ purgeProtectedState, navigate: (href) => window.location.replace(href) });
  const dialogTitle = dialog === "resolved" ? "Confirm resolution" : dialog === "denied" ? "Deny this ticket" : dialog === "notify" ? (notifyStage === "preview" ? "Review resident notification" : "Notify this resident") : "Zalo handoff unavailable";

  return <div className="page manager-page">
    <PageHeader title={ticket.subject} description={`${ticket.id} · ${ticket.building} · ${ticket.floor}-${ticket.room}`} action={<StatusBadge status={currentStatus} />} />
    {message ? <div className={openResult === "transitioned" || openResult === "already-current" ? "notice notice-success" : "notice"} role={openResult === "unavailable" ? "alert" : "status"}><span>{message}</span>{openResult === "unavailable" ? <Button kind="quiet" onClick={() => runOpen(currentStatus)}>Retry open</Button> : null}</div> : null}
    <div className="manager-detail"><section className="detail-stack"><Card className="reveal reveal-2"><h2>Immutable submitted snapshot</h2><p>{ticket.content}</p><dl className="detail-grid"><div><dt>Resident</dt><dd>{ticket.ownerId.replace("demo-resident-", "Synthetic ")}</dd></div><div><dt>Location</dt><dd>{ticket.building}, floor {ticket.floor}, room {ticket.room}</dd></div><div><dt>Urgency</dt><dd>{ticket.urgency}</dd></div><div><dt>Observed version</dt><dd>v4</dd></div></dl></Card><Card className="timeline-card reveal reveal-3"><h2>Event timeline</h2><ol className="timeline"><li><span /><div><strong>Resident submitted ticket</strong><small>{new Date(ticket.submittedAt).toLocaleString("en-GB")}</small></div></li><li><span /><div><strong>Manager detail opened</strong><small>Idempotent open command · {openResult === "opening" ? "opening" : `current state ${currentStatus}`}</small></div></li></ol><div className="form-actions"><Button kind="quiet" disabled={openResult === "opening"} onClick={() => runOpen(currentStatus, "conflict")}>Simulate open conflict</Button><Button kind="quiet" disabled={openResult === "opening"} onClick={() => runOpen(currentStatus, "unavailable")}>Simulate open unavailable</Button><Button kind="quiet" onClick={loseScope}>Simulate scope loss</Button></div></Card></section><aside className="action-rail reveal reveal-3"><Card><h2>Contact</h2><p>Contact actions are separate from lifecycle decisions.</p><div className="stack-actions"><Button kind="secondary" disabled={!actionsAvailable} onClick={() => setDialog("zalo")}>Zalo <ExternalIcon /></Button><Button kind="quiet" disabled={!actionsAvailable} onClick={() => setDialog("notify")}>Notify resident</Button></div></Card><Card><h2>Lifecycle</h2><p>Use only actions returned for the current server state.</p><div className="stack-actions"><Button disabled={!actionsAvailable || currentStatus === "Resolved" || currentStatus === "Denied"} onClick={() => setDialog("resolved")}>Mark resolved</Button><Button kind="danger" disabled={!actionsAvailable || currentStatus === "Resolved" || currentStatus === "Denied"} onClick={() => setDialog("denied")}>Deny ticket</Button></div></Card></aside></div>
    <ModalDialog open={Boolean(dialog)} title={dialogTitle} focusKey={`${dialog}-${notifyStage}`} description={dialog === "resolved" ? "This records a terminal Resolved state after server validation." : dialog === "denied" ? "A non-empty explanation is required and preserved through recoverable conflicts." : dialog === "notify" ? "The audience is exactly one server-authorized ticket Resident and cannot be edited." : "The synthetic mock returns the safe Notify fallback and makes no profile or delivery claim."} onClose={closeDialog}>
      {dialog === "denied" ? <FormField id="denial-explanation" label="Required explanation" error={!denial.trim() ? "Enter an explanation before confirming." : undefined}><textarea value={denial} onChange={(event) => setDenial(event.target.value)} rows={4} /></FormField> : null}
      {dialog === "notify" && notifyStage === "edit" ? <><FormField id="notify-subject" label="Subject"><input value={notifySubject} onChange={(event) => setNotifySubject(event.target.value)} /></FormField><FormField id="notify-message" label="Message"><textarea rows={4} value={notifyContent} onChange={(event) => setNotifyContent(event.target.value)} /></FormField><div className="notice"><strong>Audience</strong><span>Exactly one authorized ticket Resident. Preview is required before send.</span></div></> : null}
      {dialog === "notify" && notifyStage === "preview" ? <Card className="preview-card"><h3>Server-derived preview</h3><p><strong>{notifySubject}</strong></p><p>{notifyContent}</p><dl><div><dt>Recipients</dt><dd>1 synthetic authorized Resident</dd></div><div><dt>Expiry</dt><dd>10 minutes</dd></div></dl></Card> : null}
      {dialog === "zalo" ? <div className="notice"><strong>Safe fallback</strong><span>No external URL was returned. You can cancel or continue into the ticket-specific Notify flow.</span></div> : null}
      <div className="form-actions"><Button kind="quiet" data-safe-focus onClick={closeDialog}>Cancel</Button>{dialog === "resolved" ? <><Button kind="quiet" onClick={() => { setMessage(`Another manager changed this ticket. Current state remains ${currentStatus}; review before trying again.`); closeDialog(); }}>Simulate conflict</Button><Button onClick={() => transition("Resolved")}>Confirm resolved</Button></> : null}{dialog === "denied" ? <><Button kind="quiet" onClick={() => { setMessage(`Another manager changed this ticket. Current state remains ${currentStatus}; your explanation is still in this tab.`); closeDialog(); }}>Simulate conflict</Button><Button kind="danger" disabled={!denial.trim()} onClick={() => transition("Denied")}>Confirm denial</Button></> : null}{dialog === "notify" && notifyStage === "edit" ? <Button disabled={!notifySubject.trim() || !notifyContent.trim()} onClick={() => setNotifyStage("preview")}>Create preview</Button> : null}{dialog === "notify" && notifyStage === "preview" ? <><Button kind="quiet" onClick={() => setNotifyStage("edit")}>Edit message</Button><Button onClick={() => { setMessage("Notification campaign accepted for one authorized recipient. Delivery and read status are not claimed."); closeDialog(); }}>Send notification</Button></> : null}{dialog === "zalo" ? <Button onClick={() => { setDialog("notify"); setNotifyStage("edit"); }}>Use Notify instead</Button> : null}</div>
    </ModalDialog>
  </div>;
}
