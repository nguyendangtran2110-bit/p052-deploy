"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { BellIcon } from "@/src/components/icons";
import { Button, Card, FormField, PageHeader } from "@/src/components/primitives";
import { useStageFocus } from "@/src/components/use-stage-focus";
import { useApp } from "@/src/components/providers";
import { notificationsForAccount, residentProfiles } from "@/src/mock/data";
import { handleScopeLoss } from "@/src/lib/session";

type Audience = "building" | "floor" | "unit" | "selected";
type Stage = "edit" | "preview" | "stale" | "unknown" | "accepted";

function defaultAudience(allFloors: boolean): Audience {
  return allFloors ? "building" : "floor";
}

export default function ManagerNotificationsPage() {
  const { account } = useApp();
  const [mode, setMode] = useState<"inbox" | "compose">("inbox");
  const [stage, setStage] = useState<Stage>("edit");
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");
  const [audience, setAudience] = useState<Audience>(() => defaultAudience(Boolean(account?.floors.includes("ALL_FLOORS"))));
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [error, setError] = useState("");
  const audienceRef = useRef<HTMLSelectElement>(null);
  const stageRef = useStageFocus(`${mode}-${stage}`);

  useEffect(() => {
    const resetTimer = window.setTimeout(() => {
      setAudience(defaultAudience(Boolean(account?.floors.includes("ALL_FLOORS"))));
      setStage("edit");
      setSelectedIds([]);
      setError("");
    }, 0);
    return () => window.clearTimeout(resetTimer);
  }, [account?.id, account?.floors]);

  const safeAudience = audience === "building" && !account?.floors.includes("ALL_FLOORS") ? "floor" : audience;

  const scopedResidents = useMemo(() => residentProfiles.filter((resident) => account && resident.building === account.building && (account.floors.includes("ALL_FLOORS") || account.floors.includes(resident.floor))), [account]);
  const recipients = useMemo(() => {
    if (!account) return [];
    if (safeAudience === "selected") return scopedResidents.filter((resident) => selectedIds.includes(resident.id));
    if (safeAudience === "unit") return scopedResidents.slice(0, 1);
    if (safeAudience === "floor" && account.floors.includes("ALL_FLOORS")) return scopedResidents.filter((resident) => resident.floor === scopedResidents[0]?.floor);
    return scopedResidents;
  }, [account, safeAudience, scopedResidents, selectedIds]);

  const audienceSummary = safeAudience === "building" ? `${account?.building} · all authorized floors` : safeAudience === "floor" ? `${account?.building} · floor ${account?.floors.includes("ALL_FLOORS") ? scopedResidents[0]?.floor ?? "none" : account?.floors[0]}` : safeAudience === "unit" ? `${account?.building} · one in-scope unit` : `${recipients.length} selected in-scope Resident${recipients.length === 1 ? "" : "s"}`;

  const preview = (event: FormEvent) => {
    event.preventDefault();
    if (!subject.trim() || !content.trim()) return;
    if (!recipients.length) {
      setError("The authorized audience is empty. Select at least one in-scope Resident or choose another audience.");
      window.setTimeout(() => audienceRef.current?.focus(), 0);
      return;
    }
    setError("");
    setStage("preview");
  };

  const reset = () => { setStage("edit"); setSubject(""); setContent(""); setSelectedIds([]); setError(""); };
  const purgeProtectedState = () => { setMode("inbox"); reset(); };
  const loseScope = () => handleScopeLoss({ purgeProtectedState, navigate: (href) => window.location.replace(href) });

  return <div ref={stageRef} className="page manager-page">
    <PageHeader title="Notifications" description="Read your inbox or compose a scoped campaign with server-derived preview before send." action={<div className="page-header-controls"><div className="segmented"><button aria-pressed={mode === "inbox"} onClick={() => setMode("inbox")}>Inbox</button><button aria-pressed={mode === "compose"} onClick={() => setMode("compose")}>Compose</button></div><Button kind="quiet" onClick={loseScope}>Simulate scope loss</Button></div>} />
    {mode === "inbox" ? <div className="notification-list reveal reveal-2">{account ? notificationsForAccount(account).map((item) => <article className={item.unread ? "notification unread" : "notification"} key={item.id}><span className="notification-icon"><BellIcon /></span><div><div className="notification-heading"><h2>{item.title}</h2>{item.unread ? <span className="unread-label">Unread</span> : null}</div><p>{item.body}</p><small>{item.time}</small></div></article>) : null}</div> : <div className="composer-layout">
      {stage === "accepted" ? <div className="durable-result" role="status"><span className="result-mark">✓</span><h2 data-stage-focus tabIndex={-1}>Campaign accepted</h2><p>The campaign is durably queued for processing. This does not claim delivery or read status.</p><Button onClick={reset}>Create another</Button></div> : <form className="reveal reveal-2" onSubmit={preview}><Card><h2>{stage === "edit" ? "Compose message" : "Reviewed message"}</h2>{error ? <div className="error-summary" role="alert"><strong>Audience needs attention</strong><span>{error}</span></div> : null}<FormField id="campaign-subject" label="Subject"><input required value={subject} readOnly={stage !== "edit"} onChange={(event) => setSubject(event.target.value)} /></FormField><FormField id="campaign-content" label="Content"><textarea required rows={6} value={content} readOnly={stage !== "edit"} onChange={(event) => setContent(event.target.value)} /></FormField><FormField id="campaign-audience" label="Audience" hint="Available choices come from the signed-in Manager's exact scope."><select ref={audienceRef} value={safeAudience} disabled={stage !== "edit"} onChange={(event) => { setAudience(event.target.value as Audience); setError(""); }}>
        {account?.floors.includes("ALL_FLOORS") ? <option value="building">Authorized building</option> : null}
        <option value="floor">Current assigned floor</option><option value="unit">One in-scope unit</option><option value="selected">Selected in-scope Residents</option>
      </select></FormField>
      {safeAudience === "selected" ? <fieldset className="resident-selector" disabled={stage !== "edit"}><legend>Select Residents</legend>{scopedResidents.map((resident) => <label key={resident.id}><input type="checkbox" checked={selectedIds.includes(resident.id)} onChange={(event) => setSelectedIds((current) => event.target.checked ? [...current, resident.id] : current.filter((id) => id !== resident.id))} /><span><strong>{resident.name}</strong><small>{resident.building} · {resident.floor}-{resident.room}</small></span></label>)}</fieldset> : null}
      {stage === "edit" ? <Button>Create preview</Button> : <div className="form-actions"><Button kind="quiet" type="button" onClick={() => setStage("edit")}>Edit preview</Button>{stage === "preview" ? <><Button kind="quiet" type="button" onClick={() => setStage("stale")}>Simulate stale preview</Button><Button type="button" onClick={() => setStage("accepted")}>Send campaign</Button></> : null}{stage === "stale" ? <Button type="button" onClick={() => setStage("preview")}>Refresh preview</Button> : null}{stage === "unknown" ? <Button type="button" onClick={() => setStage("accepted")}>Retry same request</Button> : null}</div>}</Card></form>}
      <aside className="reveal reveal-3"><Card className="preview-card" role={stage === "preview" ? "status" : undefined}><span className="proposal-label">Server-derived preview</span><h2 data-stage-focus={stage === "preview" ? "" : undefined} tabIndex={stage === "preview" ? -1 : undefined}>{stage === "preview" ? "Preview ready" : stage === "stale" ? "Preview expired" : stage === "unknown" ? "Outcome unknown" : "Audience check"}</h2>{stage === "preview" ? <><p>{subject}</p><dl><div><dt>Audience</dt><dd>{audienceSummary}</dd></div><div><dt>Recipients</dt><dd>{recipients.length} synthetic in-scope Resident{recipients.length === 1 ? "" : "s"}</dd></div><div><dt>Preview expiry</dt><dd>10 minutes</dd></div></dl><p className="muted">Recipients are re-resolved at send. Authorization remains server-owned.</p><Button kind="quiet" onClick={() => setStage("unknown")}>Simulate transport uncertainty</Button></> : stage === "stale" ? <div className="notice" role="alert"><strong>Nothing was sent</strong><span>The audience or scope changed. Refresh and review the exact recipients again.</span></div> : stage === "unknown" ? <div className="notice" role="alert"><strong>Do not create a second campaign</strong><span>Retry uses the same preview token and idempotency key until a durable result is known.</span></div> : <p>Complete the message and choose an authorized audience. Send stays unavailable until an exact non-empty preview is reviewed.</p>}</Card></aside>
    </div>}
  </div>;
}
