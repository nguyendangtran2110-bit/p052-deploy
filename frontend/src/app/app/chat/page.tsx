"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, BookOpen, Bot, Check, HelpCircle, Info, MessageCircle, Paperclip, Send, Sparkles, Ticket, WandSparkles } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ChatAttachments } from "@/components/chat-attachments";
import { Badge, Button, Card, IconButton, PageHeader } from "@/components/ui";
import { useAIWorkflow, useResidentAssistantConversation } from "@/features/ai-chat/queries";
import { isApiError, USE_MOCKS } from "@/lib/api-client";
import { cancelAIWorkflow, downloadAttachment, isConflict, sendResidentAssistantMessage, type ChatInput } from "@/lib/data";
import { getAccount } from "@/lib/auth-session";
import { fromNow } from "@/lib/format";
import { useResidentProfile } from "@/features/resident/queries";
import type { AIAction, AIWorkflowMessage, AIWorkflowResponse, ConversationMessage } from "@/types";
import { useUiStore } from "@/stores/ui-store";

type DisplayMessage = ConversationMessage | AIWorkflowMessage;

function localId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function randomKey() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `chat-${Date.now()}`;
}

function displayAction(action: AIAction | null | undefined) {
  return action && action.requires_confirmation ? action : null;
}

function stateTone(state?: string) {
  if (state === "completed" || state === "published") return "success" as const;
  if (state === "failed" || state === "cancelled") return "danger" as const;
  if (state === "awaiting_confirmation" || state === "executing") return "warning" as const;
  return "info" as const;
}

function draftValue(workflow: AIWorkflowResponse | null, key: string) {
  const draft = workflow?.draft as Record<string, unknown> | undefined;
  const value = draft?.[key];
  if (Array.isArray(value)) return value.join(", ");
  return value === undefined || value === null || value === "" ? "Not provided" : String(value);
}

function workflowAttachmentIds(workflow: AIWorkflowResponse) {
  const value = (workflow.draft as Record<string, unknown>).attachment_ids;
  return Array.isArray(value) ? value.filter((id): id is string => typeof id === "string") : [];
}

export default function ResidentChatPage() {
  const router = useRouter();
  const profile = useResidentProfile();
  const showToast = useUiStore((state) => state.showToast);
  const [authorized, setAuthorized] = useState(false);
  const [conversationId, setConversationId] = useState<string>();
  const [workflowId, setWorkflowId] = useState<string>();
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [workflow, setWorkflow] = useState<AIWorkflowResponse | null>(null);
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [attachmentsUploading, setAttachmentsUploading] = useState(false);
  const [clearAttachmentsSignal, setClearAttachmentsSignal] = useState(0);
  const [pending, setPending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const retryKey = useRef<string | null>(null);
  const actionKeys = useRef(new Map<string, string>());

  useEffect(() => {
    const account = getAccount();
    const allowed = USE_MOCKS || account?.role === "resident";
    if (!allowed) router.replace(account?.role === "management" ? "/management" : "/login");
    setAuthorized(allowed);
  }, [router]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setConversationId(params.get("conversation_id") ?? undefined);
    setWorkflowId(params.get("workflow_id") ?? undefined);
  }, []);

  const conversation = useResidentAssistantConversation(conversationId);
  const workflowQuery = useAIWorkflow(workflowId);

  useEffect(() => {
    if (profile.data?.units.length && !selectedUnitId) {
      setSelectedUnitId(profile.data.units.find((unit) => unit.is_primary)?.id ?? profile.data.units[0].id);
    }
  }, [profile.data, selectedUnitId]);

  useEffect(() => {
    if (conversation.data) setMessages(conversation.data.messages);
  }, [conversation.data]);

  useEffect(() => {
    if (workflowQuery.data) setWorkflow(workflowQuery.data);
  }, [workflowQuery.data]);

  const selectedUnit = useMemo(() => profile.data?.units.find((unit) => unit.id === selectedUnitId), [profile.data?.units, selectedUnitId]);
  const pendingAction = displayAction(workflow?.action);
  const handoffActive = conversation.data?.handoff_status === "management_active";
  const terminal = workflow?.state === "completed" || workflow?.state === "cancelled" || workflow?.state === "published";

  function updateUrl(nextConversationId: string, nextWorkflowId: string) {
    const params = new URLSearchParams();
    params.set("conversation_id", nextConversationId);
    params.set("workflow_id", nextWorkflowId);
    router.replace(`/app/chat?${params.toString()}`, { scroll: false });
  }

  function actionIdempotencyKey(actionId: string) {
    const existing = actionKeys.current.get(actionId);
    if (existing) return existing;
    const key = randomKey();
    actionKeys.current.set(actionId, key);
    return key;
  }

  function appendUserMessage(content: string, ids: string[]) {
    const message: ConversationMessage = {
      id: localId("user-message"),
      role: "user",
      author_id: null,
      content,
      intent: null,
      citations: [],
      action_payload: null,
      attachment_ids: ids,
      created_at: new Date().toISOString(),
      conversation_version: null,
    };
    setMessages((current) => [...current, message]);
  }

  async function submit(messageOverride?: string, confirm = false) {
    const content = (messageOverride ?? draft).trim();
    if (!content || pending || handoffActive) return;
    if (!selectedUnitId) {
      setErrorMessage("Select a unit from your resident profile before sending a ticket request.");
      return;
    }
    if (confirm && (!workflow?.workflow_id || !workflow.action?.action_id)) {
      setErrorMessage("The current workflow is no longer available. Refresh and review the draft again.");
      return;
    }
    setPending(true);
    setErrorMessage(null);
    const stableKey = retryKey.current ?? actionIdempotencyKey(confirm ? workflow!.action!.action_id : randomKey());
    retryKey.current = stableKey;
    const payload: ChatInput = {
      message: content,
      conversation_id: conversationId,
      unit_id: selectedUnitId,
      workflow_id: workflow?.workflow_id || workflowId,
      workflow_version: workflow?.workflow_version,
      confirmed_action_id: confirm ? workflow?.action?.action_id : undefined,
      confirm_action: confirm,
      idempotency_key: stableKey,
      attachment_ids: confirm ? [] : attachmentIds,
    };
    if (confirm) appendUserMessage(content, []);
    else appendUserMessage(content, attachmentIds);
    try {
      const response = await sendResidentAssistantMessage(payload);
      setWorkflow(response);
      if (response.conversation_id && response.workflow_id) {
        setConversationId(response.conversation_id);
        setWorkflowId(response.workflow_id);
        updateUrl(response.conversation_id, response.workflow_id);
      }
      if (response.message) setMessages((current) => [...current, response.message!]);
      setDraft("");
      setAttachmentIds([]);
      setClearAttachmentsSignal((value) => value + 1);
      retryKey.current = null;
      if (conversationId) await conversation.refetch();
      if (workflowId) await workflowQuery.refetch();
    } catch (error) {
      if (isConflict(error)) {
        await Promise.all([conversation.refetch(), workflowQuery.refetch()]);
        showToast({ tone: "error", message: "The workflow changed in another session. The draft and attachments were kept; review the latest version." });
      } else if (isApiError(error) && error.status === 422) {
        setErrorMessage(Object.values(error.fieldErrors ?? {})[0] ?? error.message);
      } else {
        setErrorMessage(error instanceof Error ? error.message : "Could not send the message.");
      }
    } finally {
      setPending(false);
    }
  }

  async function cancelWorkflow() {
    if (!workflow?.workflow_id || pending || terminal) return;
    setPending(true);
    try {
      const response = await cancelAIWorkflow(workflow.workflow_id);
      setWorkflow((current) => current ? { ...current, state: response.state, workflow_version: response.workflow_version, action: null } : current);
      showToast({ tone: "info", message: "Workflow cancelled. No ticket was created." });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not cancel the workflow.");
    } finally {
      setPending(false);
    }
  }

  async function download(id: string) {
    try {
      const response = await downloadAttachment(id);
      if (response.download_url && response.download_url !== "#") window.open(response.download_url, "_blank", "noopener,noreferrer");
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Could not download the attachment." });
    }
  }

  const currentAction = pendingAction;
  if (!authorized) return <AppShell><div className="workspace-loading" style={{ minHeight: 280 }}><span>Checking resident access...</span></div></AppShell>;
  return <AppShell>
    <PageHeader eyebrow="Resident space / AI chat" title="Ask the resident assistant" description="Use handbook answers or describe a problem. Ticket creation always requires your confirmation." actions={<Link href="/app/tickets/new"><Button variant="outline"><Ticket size={16} /> Create ticket directly</Button></Link>} />
    <div className="chat-layout">
      <aside className="chat-sidebar">
        <Card className="chat-sidebar-card"><div className="section-heading"><div><h3>OnBxrd Assistant</h3><p>Handbook and resident support</p></div><Bot size={19} color="#087f77" /></div><label className="field-label" htmlFor="chat-unit">Unit for this request</label><select id="chat-unit" className="select" value={selectedUnitId} onChange={(event) => setSelectedUnitId(event.target.value)} disabled={profile.isLoading || pending}><option value="">Select a unit</option>{profile.data?.units.map((unit) => <option value={unit.id} key={unit.id}>{unit.unit_number} · Building {unit.building}</option>)}</select>{selectedUnit && <p className="field-hint">{selectedUnit.project_code} · {selectedUnit.id}</p>}<div className="suggestion-list"><button className="suggestion" type="button" onClick={() => void submit("What are the gym opening hours?")}>Ask about gym opening hours</button><button className="suggestion" type="button" onClick={() => void submit("I want to report a maintenance problem")}>Report a maintenance problem</button><button className="suggestion" type="button" onClick={() => void submit("What are the quiet hours?")}>Ask about quiet hours</button></div></Card>
        <Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Workflow rules</h3></div><Info size={17} color="#087f77" /></div><p style={{ color: "var(--muted)", fontSize: 11, lineHeight: 1.55 }}>The assistant asks for missing required fields and shows a draft before any ticket is created.</p></Card>
        <Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Knowledge base</h3><p>Handbook sources are returned by API</p></div><BookOpen size={18} color="#7754b8" /></div><Badge tone="success"><Check size={12} /> Available</Badge></Card>
      </aside>
      <section className="chat-window">
        <header className="chat-header"><div className="chat-header-title"><div className="bot-avatar"><Bot size={18} /></div><div><strong>Resident assistant</strong><span>{workflow?.workflow_id ? `Workflow ${workflow.workflow_id.slice(0, 8)} · revision ${workflow.workflow_version}` : "New conversation"}</span></div></div><IconButton label="Assistant information"><HelpCircle size={18} /></IconButton></header>
        {handoffActive && <div className="notice-card" style={{ margin: 12 }}><AlertTriangle size={17} /><div><strong>Management is handling this conversation.</strong><p>Messages are not sent back to the AI agent while a manager is active.</p></div></div>}
        <div className="chat-messages">
          {conversation.isError && <div className="error-state">Could not load this conversation. Check the conversation ID and your access.</div>}
          {workflowQuery.isError && <div className="error-state">Could not load the workflow. The server remains the source of truth.</div>}
          {messages.length === 0 && !conversation.isError && <div className="chat-empty"><div className="bot-avatar"><WandSparkles size={19} /></div><h2>What do you need help with?</h2><p>Ask about handbook rules, amenities, or describe a problem in your unit.</p></div>}
          {messages.map((message) => <ChatMessage key={message.id} message={message} onDownload={download} />)}
          {pending && <div className="message"><div className="bot-avatar" style={{ width: 27, height: 27 }}><Bot size={14} /></div><div className="typing"><span /><span /><span /></div></div>}
          {errorMessage && <div className="error-state" role="alert">{errorMessage}</div>}
          {workflow && <WorkflowCard workflow={workflow} action={currentAction} pending={pending} onConfirm={() => void submit("Confirm ticket creation", true)} onCancel={() => void cancelWorkflow()} onDownload={download} />}
        </div>
        {!handoffActive && <><ChatAttachments workflowId={workflow?.workflow_id || workflowId} disabled={pending || terminal} clearSignal={clearAttachmentsSignal} onChange={setAttachmentIds} onUploadingChange={setAttachmentsUploading} /><form className="composer" onSubmit={(event) => { event.preventDefault(); void submit(); }}><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask a question or describe a problem..." rows={1} disabled={pending || terminal || attachmentsUploading} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); } }} /><Button aria-label="Send message" type="submit" disabled={pending || terminal || attachmentsUploading || !draft.trim() || !selectedUnitId}><Send size={16} /> <span className="desktop-only">Send</span></Button></form></>}
        {handoffActive && <div className="assistant-note" style={{ margin: 12 }}>The manager reply is shown in this conversation. The resident assistant is paused until management hands the conversation back.</div>}
        {attachmentIds.length > 0 && <div className="composer-attachments">{attachmentIds.length} uploaded attachment(s) will be sent with the next message.</div>}
      </section>
    </div>
  </AppShell>;
}

function ChatMessage({ message, onDownload }: { message: DisplayMessage; onDownload: (id: string) => Promise<void> }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  return <div className={`message message-${message.role}`}><>{!isUser && !isSystem && <div className="bot-avatar" style={{ width: 27, height: 27, flex: "0 0 auto" }}>{message.role === "management" ? <MessageCircle size={14} /> : <Bot size={14} />}</div>}</><div><div className="message-bubble">{message.content}{message.citations?.length > 0 && <div className="citation-list">{message.citations.map((citation, index) => <span className="citation" key={`${citation.title}-${index}`}><BookOpen size={12} />{citation.title}{citation.section ? ` · ${citation.section}` : ""}{citation.page ? ` · p. ${citation.page}` : ""}</span>)}</div>}{message.attachment_ids?.map((id) => <button className="message-attachment-link" type="button" key={id} onClick={() => void onDownload(id)}><Paperclip size={12} />Attachment</button>)}</div><div className="message-meta">{isUser ? "You" : isSystem ? "System" : message.role === "management" ? "Management" : "OnBxrd Assistant"} · {fromNow(message.created_at)}</div></div></div>;
}

function WorkflowCard({ workflow, action, pending, onConfirm, onCancel, onDownload }: { workflow: AIWorkflowResponse; action: AIAction | null; pending: boolean; onConfirm: () => void; onCancel: () => void; onDownload: (id: string) => Promise<void> }) {
  if (workflow.state === "completed" && workflow.ticket) return <div className="action-card"><strong><Check size={14} style={{ verticalAlign: "-2px" }} /> Ticket {workflow.ticket.ticket_code} created</strong><p>The ticket is now available in your ticket list.</p><Link href={`/app/tickets/${workflow.ticket.id}`}><Button size="sm"><Ticket size={14} /> Open ticket</Button></Link></div>;
  if (workflow.state === "cancelled") return <div className="assistant-note">This workflow was cancelled. No ticket was created.</div>;
  if (workflow.state === "failed") return <div className="action-card"><strong><AlertTriangle size={14} style={{ verticalAlign: "-2px" }} /> The action failed</strong><p>Review the latest draft and retry after the backend error is resolved.</p>{action && <Button size="sm" onClick={onConfirm} disabled={pending}><Sparkles size={14} /> Retry creation</Button>}</div>;
  const attachmentIds = workflowAttachmentIds(workflow);
  return <div className="action-card workflow-panel"><div><strong><Sparkles size={14} style={{ verticalAlign: "-2px" }} /> Ticket draft</strong><Badge tone={stateTone(workflow.state)}>{workflow.state}</Badge></div>{workflow.missing_fields.length > 0 && <div className="workflow-missing">Still needed: {workflow.missing_fields.join(", ")}</div>}<div className="workflow-grid">{[["Category", "category"], ["Priority", "priority"], ["Title", "title"], ["Location", "location"], ["Description", "description"]].map(([label, key]) => <div className="workflow-field" key={key}><span>{label}</span><strong>{draftValue(workflow, key)}</strong></div>)}</div>{attachmentIds.length > 0 && <><p className="field-hint">Attachments are linked to the workflow and will be linked to the ticket after confirmation.</p><div className="citation-list">{attachmentIds.map((id) => <button className="message-attachment-link" type="button" key={id} onClick={() => void onDownload(id)}><Paperclip size={12} />Attachment</button>)}</div></>}<div className="workflow-actions">{action?.requires_confirmation && workflow.state === "awaiting_confirmation" && <Button size="sm" onClick={onConfirm} disabled={pending || workflow.missing_fields.length > 0}>Confirm and create ticket</Button>}{workflow.state !== "completed" && <Button size="sm" variant="outline" onClick={onCancel} disabled={pending}>Cancel workflow</Button>}</div></div>;
}
