"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Card, FormField, ModalDialog, PageHeader, StatusBadge } from "@/src/components/primitives";
import { useStageFocus } from "@/src/components/use-stage-focus";
import { useApp } from "@/src/components/providers";
import { clearSubmitAttempt, createSubmitAttempt, readSubmitAttempt, replaceDraft, startDraft, submitDraft, TicketApiError, updateDraft, writeSubmitAttempt } from "@/src/lib/ticket-api";
import { takeProposal } from "@/src/lib/volatile-store";
import type { DraftRecord, DraftValue, SubmitAttempt } from "@/src/lib/ticket-contract";

const emptyDraft: DraftValue = { subject: "", content: "", urgency: "Normal" };
type SaveState = "Loading…" | "Saving…" | "Saved" | "Unavailable" | "Conflict" | "Generation gone";
type WorkspaceMode = "edit" | "review" | "submitting" | "outcome_unknown" | "submitted";
type ConflictSelections = Record<keyof DraftValue, boolean>;
const noSelections: ConflictSelections = { subject: false, content: false, urgency: false };

export default function TicketWorkspacePage() {
  const { account } = useApp();
  const searchParams = useSearchParams();
  const [draft, setDraft] = useState<DraftValue>(emptyDraft);
  const [baseline, setBaselineState] = useState<DraftRecord | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("Loading…");
  const [mode, setMode] = useState<WorkspaceMode>("edit");
  const [dialog, setDialog] = useState<"existing" | "replace" | "conflict" | null>(null);
  const [localConflict, setLocalConflict] = useState<DraftValue | null>(null);
  const [conflictSelections, setConflictSelections] = useState<ConflictSelections>(noSelections);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [createdId, setCreatedId] = useState("");
  const [attempt, setAttempt] = useState<SubmitAttempt | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const baselineRef = useRef<DraftRecord | null>(null);
  const draftRef = useRef<DraftValue>(emptyDraft);
  const pendingSave = useRef<DraftValue | null>(null);
  const saveInFlight = useRef(false);
  const flushAgain = useRef<() => void>(() => {});
  const mounted = useRef(true);
  const errorSummary = useRef<HTMLDivElement>(null);
  const stageRef = useStageFocus(mode);

  const setBaseline = useCallback((next: DraftRecord | null) => {
    baselineRef.current = next;
    setBaselineState(next);
  }, []);

  const finishSubmission = useCallback((ticketId: string) => {
    clearSubmitAttempt();
    setAttempt(null);
    setCreatedId(ticketId);
    setBaseline(null);
    pendingSave.current = null;
    setMode("submitted");
  }, [setBaseline]);

  const sendSubmission = useCallback(async (pendingAttempt: SubmitAttempt) => {
    if (!account) return;
    setAttempt(pendingAttempt);
    setMode("submitting");
    try {
      const ticket = await submitDraft(account, pendingAttempt);
      if (mounted.current) finishSubmission(ticket.id);
    } catch (error) {
      if (!mounted.current) return;
      if (!(error instanceof TicketApiError)) { setMode("outcome_unknown"); return; }
      if (error.detail.code === "field_validation_failed") {
        clearSubmitAttempt();
        setAttempt(null);
        setErrors(error.detail.fields ?? {});
        setMode("edit");
        window.setTimeout(() => errorSummary.current?.focus(), 0);
      } else if (error.detail.code === "ticket_draft_conflict" && error.detail.current) {
        clearSubmitAttempt();
        setAttempt(null);
        setBaseline(error.detail.current);
        setLocalConflict(draftRef.current);
        setConflictSelections(noSelections);
        setSaveState("Conflict");
        setMode("edit");
        setDialog("conflict");
      } else setMode("outcome_unknown");
    }
  }, [account, finishSubmission, setBaseline]);

  useEffect(() => {
    mounted.current = true;
    if (!account) return;
    let cancelled = false;
    const initialize = async () => {
      const pendingAttempt = readSubmitAttempt(account);
      if (pendingAttempt) { await sendSubmission(pendingAttempt); return; }
      try {
        const proposal = takeProposal(account);
        const result = await startDraft(account);
        if (cancelled) return;
        setBaseline(result.draft);
        setDraft(result.draft.value);
        draftRef.current = result.draft.value;
        setSaveState("Saved");
        if (result.outcome === "existing" && (searchParams.get("intent") === "new" || proposal)) {
          if (proposal) setLocalConflict(proposal);
          setDialog("existing");
          return;
        }
        if (proposal) {
          const saved = await updateDraft(account, result.draft, proposal);
          if (cancelled) return;
          setBaseline(saved);
          setDraft(saved.value);
          draftRef.current = saved.value;
        }
      } catch { if (!cancelled) setSaveState("Unavailable"); }
    };
    void initialize();
    return () => { cancelled = true; mounted.current = false; };
  }, [account, searchParams, sendSubmission, setBaseline]);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const flushSave = useCallback(async () => {
    if (!account || saveInFlight.current || saveState === "Conflict" || saveState === "Generation gone") return;
    const desired = pendingSave.current;
    const observed = baselineRef.current;
    if (!desired || !observed) return;
    pendingSave.current = null;
    saveInFlight.current = true;
    setSaveState("Saving…");
    try {
      const saved = await updateDraft(account, observed, desired);
      if (!mounted.current) return;
      setBaseline(saved);
      if (pendingSave.current) { saveInFlight.current = false; window.setTimeout(() => flushAgain.current(), 0); }
      else setSaveState("Saved");
    } catch (error) {
      if (!mounted.current) return;
      if (error instanceof TicketApiError && error.detail.code === "ticket_draft_conflict" && error.detail.current) {
        setBaseline(error.detail.current);
        setLocalConflict(desired);
        setConflictSelections(noSelections);
        setSaveState("Conflict");
        setDialog("conflict");
      } else if (error instanceof TicketApiError && error.detail.code === "ticket_draft_generation_gone") setSaveState("Generation gone");
      else { pendingSave.current = desired; setSaveState("Unavailable"); }
    } finally { saveInFlight.current = false; }
  }, [account, saveState, setBaseline]);
  useEffect(() => {
    flushAgain.current = () => { void flushSave(); };
  }, [flushSave]);

  const update = (patch: Partial<DraftValue>) => {
    if (mode === "submitting" || mode === "outcome_unknown" || saveState === "Conflict" || saveState === "Generation gone") return;
    const next = { ...draftRef.current, ...patch };
    draftRef.current = next;
    setDraft(next);
    setErrors((current) => ({ ...current, ...Object.fromEntries(Object.keys(patch).map((key) => [key, ""])) }));
    pendingSave.current = next;
    setSaveState("Saving…");
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { timer.current = null; void flushSave(); }, 750);
  };

  const saveOnBlur = () => {
    if (timer.current) { clearTimeout(timer.current); timer.current = null; }
    void flushSave();
  };

  const review = (event: FormEvent) => {
    event.preventDefault();
    if (saveState !== "Saved") { if (saveState === "Conflict") setDialog("conflict"); return; }
    const nextErrors: Record<string, string> = {};
    if (!draft.subject.trim()) nextErrors.subject = "Enter a short subject.";
    if (!draft.content.trim()) nextErrors.content = "Describe what happened and what help you need.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) { window.setTimeout(() => errorSummary.current?.focus(), 0); return; }
    setMode("review");
  };

  const submit = async () => {
    if (!account || !baseline || mode === "submitting" || mode === "outcome_unknown" || saveState !== "Saved") return;
    const nextAttempt = await createSubmitAttempt(account, baseline);
    writeSubmitAttempt(nextAttempt);
    await sendSubmission(nextAttempt);
  };

  const reconcile = async () => {
    if (!account || !baseline || !localConflict) return;
    const changes = Object.fromEntries((Object.keys(conflictSelections) as Array<keyof DraftValue>)
      .filter((field) => conflictSelections[field] && localConflict[field] !== baseline.value[field])
      .map((field) => [field, localConflict[field]])) as Partial<DraftValue>;
    const next = { ...baseline.value, ...changes };
    if (!Object.keys(changes).length) {
      draftRef.current = next; setDraft(next); setLocalConflict(null); setSaveState("Saved"); setDialog(null); return;
    }
    setSaveState("Saving…");
    try {
      const saved = await updateDraft(account, baseline, changes);
      setBaseline(saved); draftRef.current = saved.value; setDraft(saved.value); setLocalConflict(null); setConflictSelections(noSelections); setSaveState("Saved"); setDialog(null);
    } catch (error) {
      if (error instanceof TicketApiError && error.detail.current) setBaseline(error.detail.current);
      setLocalConflict(next); setConflictSelections(noSelections); setSaveState("Conflict");
    }
  };

  const confirmReplacement = async () => {
    if (!account || !baseline) return;
    try {
      const next = await replaceDraft(account, baseline);
      setBaseline(next); draftRef.current = next.value; setDraft(next.value); setLocalConflict(null); setSaveState("Saved"); setMode("edit"); setDialog(null);
    } catch (error) {
      if (error instanceof TicketApiError && error.detail.current) { setBaseline(error.detail.current); setLocalConflict(draftRef.current); setSaveState("Conflict"); setDialog("conflict"); }
      else setSaveState("Generation gone");
    }
  };

  if (mode === "submitted") return <div ref={stageRef} className="page"><div className="durable-result reveal" role="status"><span className="result-mark">✓</span><h1 data-stage-focus tabIndex={-1}>Ticket submitted</h1><p>Your request is Pending. This durable synthetic result appears in ticket history and remains available after reload.</p><dl className="detail-grid"><div><dt>Ticket</dt><dd>{createdId}</dd></div><div><dt>Status</dt><dd><StatusBadge status="Pending" /></dd></div></dl><Link className="button button-primary" href={`/resident/tickets/${createdId}`}>View ticket</Link></div></div>;

  const locked = mode === "submitting" || mode === "outcome_unknown";
  const editorLocked = locked || saveState === "Loading…" || saveState === "Conflict" || saveState === "Generation gone";
  const canReview = saveState === "Saved" && !locked;
  return <div ref={stageRef} className="page">
    <PageHeader title={mode === "review" || locked ? "Review your ticket" : "Create a support ticket"} description="Your server-owned draft is account-scoped and shared between browser sessions." action={<span className={`save-state save-state-${saveState.toLowerCase().replaceAll(" ", "-").replace("…", "")}`} role={saveState === "Conflict" || saveState === "Unavailable" || saveState === "Generation gone" ? "alert" : "status"}>{saveState}</span>} />
    {saveState === "Unavailable" ? <div className="notice" role="alert"><strong>Draft service unavailable</strong><span>Your text remains only in this tab. Other sessions and devices can see only the last server-saved values.</span><Button kind="quiet" onClick={() => void flushSave()}>Retry save</Button></div> : null}
    {saveState === "Conflict" ? <div className="notice" role="alert"><strong>Draft conflict requires review</strong><span>Autosave, review, and submission are paused. Server values are selected by default.</span><Button kind="quiet" onClick={() => setDialog("conflict")}>Review conflict</Button></div> : null}
    {saveState === "Generation gone" ? <div className="notice" role="alert"><strong>The expected draft is no longer active</strong><span>It may have been replaced, discarded, or submitted elsewhere. No cause is inferred.</span><Link href="/resident/tickets">Check ticket history</Link></div> : null}
    {mode === "submitting" ? <div className="notice" role="status"><strong>Submitting ticket</strong><span>Fields are locked while the server confirms the durable result.</span></div> : null}
    {mode === "outcome_unknown" ? <div className="notice" role="alert"><strong>Submission outcome unknown</strong><span>The request may have committed. Keep the fields locked and retry the same account-bound request.</span><Button onClick={() => attempt && void sendSubmission(attempt)}>Retry same submission</Button><Link href="/resident/tickets">Check ticket history</Link></div> : null}
    {Object.values(errors).some(Boolean) ? <div ref={errorSummary} className="error-summary" role="alert" tabIndex={-1}><strong>Check the ticket fields</strong>{errors.subject ? <a href="#ticket-subject">Subject: {errors.subject}</a> : null}{errors.content ? <a href="#ticket-content">Content: {errors.content}</a> : null}</div> : null}
    <div className="ticket-workspace">
      {mode === "edit" ? <form className="ticket-editor reveal reveal-2" onSubmit={review}><Card><h2 data-stage-focus tabIndex={-1}>Describe the request</h2><FormField id="ticket-subject" label="Subject" error={errors.subject}><input value={draft.subject} disabled={editorLocked} onChange={(event) => update({ subject: event.target.value })} onBlur={saveOnBlur} maxLength={120} /></FormField><FormField id="ticket-content" label="Content" error={errors.content} hint="Do not include passwords, access codes, or unrelated personal information."><textarea rows={8} value={draft.content} disabled={editorLocked} onChange={(event) => update({ content: event.target.value })} onBlur={saveOnBlur} maxLength={4000} /></FormField><FormField id="ticket-urgency" label="Urgency"><select value={draft.urgency} disabled={editorLocked} onChange={(event) => update({ urgency: event.target.value as DraftValue["urgency"] })} onBlur={saveOnBlur}><option>Low</option><option>Normal</option><option>High</option></select></FormField><div className="form-actions"><Button kind="quiet" type="button" disabled={!baseline || locked} onClick={() => setDialog("replace")}>Discard and start new</Button><Button type="submit" disabled={!canReview}>Review ticket</Button></div></Card></form> : <Card className="review-card reveal reveal-2" role="status"><span className="proposal-label">Review · nothing submitted yet</span><h2 data-stage-focus tabIndex={-1}>{draft.subject}</h2><p>{draft.content}</p><dl className="detail-grid"><div><dt>Urgency</dt><dd>{draft.urgency}</dd></div><div><dt>Resident</dt><dd>{account?.name}</dd></div><div><dt>Building</dt><dd>{account?.building}</dd></div><div><dt>Floor</dt><dd>{account?.floors[0]}</dd></div></dl><div className="form-actions"><Button kind="quiet" disabled={locked} onClick={() => setMode("edit")}>Return to editing</Button><Button disabled={locked || saveState !== "Saved"} onClick={() => void submit()}>{mode === "submitting" ? "Submitting…" : "Submit ticket"}</Button></div></Card>}
      <aside className="verified-context reveal reveal-3"><Card><h2>Verified context</h2><p>These values are filled by the server and cannot be edited by you or the assistant.</p><dl><div><dt>Resident</dt><dd>{account?.name}</dd></div><div><dt>Building</dt><dd>{account?.building}</dd></div><div><dt>Floor</dt><dd>{account?.floors[0]}</dd></div><div><dt>Draft generation</dt><dd>{baseline ? `${baseline.draftId.slice(0, 18)} · v${baseline.version}` : "Loading"}</dd></div></dl></Card></aside>
    </div>
    <ModalDialog open={dialog === "existing"} title="Continue your active draft?" description={baseline ? `Last saved ${new Date(baseline.updatedAt).toLocaleString("en-GB")}.` : undefined} onClose={() => setDialog(null)}><p>This explicit new-ticket action found your account&apos;s existing server draft. Resume is the safe default; replacement requires confirmation.</p><div className="form-actions"><Button data-safe-focus onClick={() => { setLocalConflict(null); setDialog(null); }}>Resume draft</Button><Button kind="danger" onClick={() => setDialog("replace")}>Discard and start new</Button></div></ModalDialog>
    <ModalDialog open={dialog === "replace"} title="Discard the active draft?" description="This atomically replaces the server draft. The previous generation cannot be restored." onClose={() => setDialog(null)}><div className="form-actions"><Button kind="quiet" data-safe-focus onClick={() => setDialog(null)}>Cancel</Button><Button kind="danger" onClick={() => void confirmReplacement()}>Confirm replacement</Button></div></ModalDialog>
    <ModalDialog open={dialog === "conflict"} title="Another session changed this draft" description="Select only the local fields you want to reapply. Every field defaults to the latest server value." onClose={() => setDialog(null)}><div className="conflict-compare">{(["subject", "content", "urgency"] as Array<keyof DraftValue>).map((field) => <Card key={field}><h3>{field[0].toUpperCase() + field.slice(1)}</h3><p><strong>Latest server value:</strong> {baseline?.value[field] || "Empty"}</p><p><strong>Unsaved local value:</strong> {localConflict?.[field] || "Empty"}</p>{baseline?.value[field] !== localConflict?.[field] ? <label><input type="checkbox" checked={conflictSelections[field]} onChange={(event) => setConflictSelections((current) => ({ ...current, [field]: event.target.checked }))} /> Reapply my local {field}</label> : <p>No difference to reconcile.</p>}</Card>)}</div><div className="form-actions"><Button kind="quiet" data-safe-focus onClick={() => setDialog(null)}>Decide later</Button><Button onClick={() => void reconcile()}>Apply selected local values</Button></div></ModalDialog>
  </div>;
}
