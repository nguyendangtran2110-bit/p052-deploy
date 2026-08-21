"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, Bot, Check, FileText, Megaphone, Paperclip, Plus, Sparkles } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ChatComposer } from "@/components/chat-composer";
import { Badge, Button, Card, IconButton, PageHeader } from "@/components/ui";
import { useManagerAssistantConversation } from "@/features/ai-chat/queries";
import { isApiError } from "@/lib/api-client";
import { cancelAIWorkflow, downloadAttachment, isConflict, sendManagerAssistantMessage, type AIWorkflowMessageInput } from "@/lib/data";
import { getAccount } from "@/lib/auth-session";
import { fromNow } from "@/lib/format";
import { USE_MOCKS } from "@/lib/api-client";
import type { AIAction, AIWorkflowMessage, AIWorkflowResponse, AIWorkflowConversationResponse } from "@/types";
import { useUiStore } from "@/stores/ui-store";

function randomKey() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `manager-assistant-${Date.now()}`;
}

function toWorkflow(response: AIWorkflowConversationResponse): AIWorkflowResponse {
  return { ...response, message: null };
}

function value(workflow: AIWorkflowResponse | null, key: string) {
  const draft = workflow?.draft as Record<string, unknown> | undefined;
  const item = draft?.[key];
  if (item === undefined || item === null || item === "") return "Not provided";
  if (Array.isArray(item)) return item.map((entry) => typeof entry === "object" && entry ? JSON.stringify(entry) : String(entry)).join(" · ");
  return String(item);
}

function tone(state?: string) {
  if (state === "published") return "success" as const;
  if (state === "failed" || state === "cancelled") return "danger" as const;
  if (state === "awaiting_confirmation" || state === "awaiting_publish_confirmation" || state === "publishing") return "warning" as const;
  return "info" as const;
}

function actionLabel(action: AIAction | null | undefined) {
  if (!action) return "Review";
  if (action.type === "publish_announcement") return "Confirm publish";
  if (action.type === "update_announcement") return "Confirm update";
  return "Create draft";
}

export default function ManagementAssistantConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const conversation = useManagerAssistantConversation(conversationId);
  const [authorized, setAuthorized] = useState(false);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<AIWorkflowMessage[]>([]);
  const [workflow, setWorkflow] = useState<AIWorkflowResponse | null>(null);
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [attachmentsUploading, setAttachmentsUploading] = useState(false);
  const [clearAttachmentsSignal, setClearAttachmentsSignal] = useState(0);
  const [pending, setPending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const retryKey = useRef<string | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const account = getAccount();
    const allowed = USE_MOCKS || (account?.role === "management" && ["manager", "admin"].includes(account.management_profile?.management_role ?? ""));
    if (!allowed) router.replace(account?.role === "resident" ? "/app" : "/management");
    setAuthorized(allowed);
  }, [router]);

  useEffect(() => {
    if (!conversation.data) return;
    setMessages(conversation.data.messages);
    setWorkflow(toWorkflow(conversation.data));
  }, [conversation.data]);

  const currentAction = workflow?.action?.requires_confirmation
    ? workflow.action
    : workflow?.action?.next_action?.requires_confirmation
      ? workflow.action.next_action
      : null;
  const terminal = workflow?.state === "published" || workflow?.state === "cancelled";
  const isPublishStep = workflow?.state === "awaiting_publish_confirmation" || currentAction?.type === "publish_announcement";
  const scopeSummary = useMemo(() => value(workflow, "scopes"), [workflow]);

  function appendUser(content: string, ids: string[]) {
    setMessages((current) => [...current, {
      id: `manager-user-${Date.now()}`,
      role: "user",
      author_id: null,
      content,
      intent: null,
      citations: [],
      action_payload: null,
      attachment_ids: ids,
      workflow_id: workflow?.workflow_id ?? null,
      workflow_state: workflow?.state ?? null,
      workflow_version: workflow?.workflow_version ?? null,
      created_at: new Date().toISOString(),
    }]);
  }

  async function send(messageOverride?: string, confirm = false) {
    const content = (messageOverride ?? draft).trim();
    if (!content || !conversationId || pending) return;
    if (confirm && (!workflow?.workflow_id || !currentAction)) {
      setErrorMessage("The current action is no longer available. Reload the conversation.");
      return;
    }
    setPending(true);
    setErrorMessage(null);
    const key = retryKey.current ?? randomKey();
    retryKey.current = key;
    const payload: AIWorkflowMessageInput = {
      message: content,
      workflow_id: workflow?.workflow_id,
      workflow_version: workflow?.workflow_version,
      confirmed_action_id: confirm ? currentAction?.action_id : undefined,
      confirm_action: confirm,
      idempotency_key: key,
      attachment_ids: confirm ? [] : attachmentIds,
    };
    appendUser(content, confirm ? [] : attachmentIds);
    try {
      const response = await sendManagerAssistantMessage(conversationId, payload);
      setWorkflow(response);
      if (response.message) setMessages((current) => [...current, response.message!]);
      setDraft("");
      setAttachmentIds([]);
      setClearAttachmentsSignal((value) => value + 1);
      retryKey.current = null;
      await conversation.refetch();
    } catch (error) {
      if (isConflict(error)) {
        await conversation.refetch();
        showToast({ tone: "error", message: "This assistant workflow changed elsewhere. The draft and attachments were kept for review." });
      } else if (isApiError(error) && error.status === 422) {
        setErrorMessage(Object.values(error.fieldErrors ?? {})[0] ?? error.message);
      } else {
        setErrorMessage(error instanceof Error ? error.message : "Could not send the assistant message.");
      }
    } finally {
      setPending(false);
    }
  }

  async function cancelWorkflow() {
    if (!workflow || pending || terminal) return;
    setPending(true);
    try {
      const response = await cancelAIWorkflow(workflow.workflow_id);
      setWorkflow((current) => current ? { ...current, state: response.state, workflow_version: response.workflow_version, action: null } : current);
      showToast({ tone: "info", message: "Assistant workflow cancelled." });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not cancel the workflow.");
    } finally {
      setPending(false);
    }
  }

  function startNewConversation() {
    router.push("/management/assistant");
  }

  async function download(id: string) {
    try {
      const response = await downloadAttachment(id);
      if (response.download_url && response.download_url !== "#") window.open(response.download_url, "_blank", "noopener,noreferrer");
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Could not download the attachment." });
    }
  }

  if (!authorized) return <AppShell><div className="workspace-loading" style={{ minHeight: 280 }}><span>Checking management access...</span></div></AppShell>;
  if (conversation.isError) return <AppShell><div className="error-state">Could not load this manager assistant conversation.</div></AppShell>;
  if (!workflow) return <AppShell><div className="workspace-loading" style={{ minHeight: 280 }}><span>Loading assistant conversation...</span></div></AppShell>;

  return <AppShell>
    <PageHeader eyebrow="Management / AI assistant" title="Announcement assistant" description={`${conversationId} · workflow revision ${workflow.workflow_version}`} actions={<Link href="/management/assistant"><Button variant="ghost"><ArrowLeft size={16} /> Assistant home</Button></Link>} />
    <div className="chat-layout">
      <aside className="chat-sidebar"><Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Announcement workflow</h3><p>Draft and publish are separate</p></div><Megaphone size={19} color="#087f77" /></div><Badge tone={tone(workflow.state)}>{workflow.state}</Badge><div className="workflow-panel" style={{ marginTop: 13 }}><div className="workflow-field"><span>Workflow ID</span><strong>{workflow.workflow_id}</strong></div><div className="workflow-field"><span>Revision</span><strong>{workflow.workflow_version}</strong></div><div className="assistant-note">Use normal chat messages to edit the draft. The backend re-extracts and validates fields before each action.</div></div></Card><Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Publishing guardrail</h3></div><FileText size={17} color="#7754b8" /></div><p style={{ color: "var(--muted)", fontSize: 11, lineHeight: 1.55 }}>The first confirmation creates a draft only. A second confirmation is required to publish it.</p></Card></aside>
      <section className="chat-window"><header className="chat-header"><div className="chat-header-title"><div className="bot-avatar"><Bot size={18} /></div><div><strong>Manager announcement assistant</strong><span>{isPublishStep ? "Review before publish" : "Collecting announcement details"}</span></div></div><IconButton label="Cancel workflow" onClick={() => void cancelWorkflow()} disabled={pending || terminal}><AlertTriangle size={17} /></IconButton></header><div className="chat-messages">{messages.length === 0 && <div className="chat-empty"><div className="bot-avatar"><Sparkles size={19} /></div><h2>What should residents know?</h2><p>Describe the announcement, its audience, urgency and any attached files.</p></div>}{messages.map((message) => <ManagerMessage key={message.id} message={message} onDownload={download} />)}{pending && <div className="message message-assistant"><div className="message-body"><div className="message-author"><div className="bot-avatar"><Bot size={14} /></div><span>OnBxrd Assistant</span></div><div className="typing"><span /><span /><span /></div></div></div>}{errorMessage && <div className="error-state" role="alert">{errorMessage}</div>}<AnnouncementPreview workflow={workflow} action={currentAction} isPublishStep={isPublishStep} pending={pending} scopeSummary={scopeSummary} onConfirm={() => void send(isPublishStep ? "Confirm publish" : "Confirm draft creation", true)} onEdit={() => { composerRef.current?.focus(); setDraft("Please update the announcement: "); }} onCancel={() => void cancelWorkflow()} onStartNew={startNewConversation} onDownload={download} /></div><ChatComposer id="manager-assistant-message" textareaRef={composerRef} value={draft} onChange={setDraft} onSubmit={() => send()} placeholder="Ask a follow-up..." workflowId={workflow.workflow_id} disabled={pending || terminal} pending={pending} attachmentsUploading={attachmentsUploading} clearAttachmentsSignal={clearAttachmentsSignal} onAttachmentChange={setAttachmentIds} onUploadingChange={setAttachmentsUploading} /></section>
    </div>
  </AppShell>;
}

function ManagerMessage({ message, onDownload }: { message: AIWorkflowMessage; onDownload: (id: string) => Promise<void> }) {
  const isUser = message.role === "user";
  return <div className={`message message-${message.role}`}><div className="message-body">{!isUser && <div className="message-author"><div className="bot-avatar"><Bot size={14} /></div><span>OnBxrd Assistant</span></div>}<div className="message-bubble"><div className="message-content">{message.content}</div></div>{message.attachment_ids.length > 0 && <div className="message-attachments">{message.attachment_ids.map((id) => <button className="message-attachment-link" type="button" key={id} onClick={() => void onDownload(id)}><Paperclip size={12} />Attachment</button>)}</div>}<div className="message-meta">{isUser ? "You · " : ""}{fromNow(message.created_at)}</div></div></div>;
}

function AnnouncementPreview({ workflow, action, isPublishStep, pending, scopeSummary, onConfirm, onEdit, onCancel, onStartNew, onDownload }: { workflow: AIWorkflowResponse; action: AIAction | null; isPublishStep: boolean; pending: boolean; scopeSummary: string; onConfirm: () => void; onEdit: () => void; onCancel: () => void; onStartNew: () => void; onDownload: (id: string) => Promise<void> }) {
  if (workflow.state === "collecting" && !action) return null;
  if (workflow.state === "cancelled") return <div className="assistant-note"><p>This workflow was cancelled. No announcement was created.</p><Button size="sm" variant="outline" onClick={onStartNew}><Plus size={14} /> Start new announcement</Button></div>;
  if (workflow.state === "published" && workflow.announcement) return <div className="action-card"><strong><Check size={14} style={{ verticalAlign: "-2px" }} /> Announcement published</strong><p>{workflow.announcement.title}</p><div className="workflow-actions"><Link href={`/management/announcements/${workflow.announcement.id}`}><Button size="sm"><Megaphone size={14} /> Open announcement</Button></Link><Button size="sm" variant="outline" onClick={onStartNew}><Plus size={14} /> Start another announcement</Button></div></div>;
  const attachmentIds = Array.isArray((workflow.draft as Record<string, unknown>).attachment_ids) ? ((workflow.draft as Record<string, unknown>).attachment_ids as unknown[]).filter((id): id is string => typeof id === "string") : [];
  return <div className="action-card workflow-panel"><div><strong><Sparkles size={14} style={{ verticalAlign: "-2px" }} /> Announcement preview</strong> <Badge tone={tone(workflow.state)}>{workflow.state}</Badge></div>{workflow.missing_fields.length > 0 && <div className="workflow-missing">Still needed: {workflow.missing_fields.join(", ")}</div>}<div className="workflow-grid"><div className="workflow-field"><span>Title</span><strong>{value(workflow, "title")}</strong></div><div className="workflow-field"><span>Type</span><strong>{value(workflow, "type")}</strong></div><div className="workflow-field"><span>Priority</span><strong>{value(workflow, "priority")}</strong></div><div className="workflow-field"><span>Audience scopes</span><strong>{scopeSummary}</strong></div><div className="workflow-field"><span>Expires at</span><strong>{value(workflow, "expires_at")}</strong></div><div className="workflow-field"><span>Attachments</span><strong>{attachmentIds.length ? `${attachmentIds.length} file(s)` : "None"}</strong></div></div><div className="workflow-field"><span>Content</span><strong>{value(workflow, "content")}</strong></div>{attachmentIds.length > 0 && <div className="citation-list">{attachmentIds.map((id) => <button className="message-attachment-link" type="button" key={id} onClick={() => void onDownload(id)}><Paperclip size={12} />Attachment</button>)}</div>}{action?.requires_confirmation && <div className="workflow-actions">{workflow.missing_fields.length === 0 && <Button size="sm" onClick={onConfirm} disabled={pending}>{actionLabel(action)}</Button>}<Button size="sm" variant="outline" onClick={onEdit} disabled={pending}><FileText size={14} /> Edit in chat</Button><Button size="sm" variant="ghost" onClick={onCancel} disabled={pending}>Cancel</Button></div>}{!action?.requires_confirmation && workflow.state !== "completed" && workflow.state !== "published" && <p className="field-hint">Continue describing the announcement to complete missing fields.</p>}{isPublishStep && <p className="field-hint">Publishing requires the current workflow revision and publish action ID.</p>}</div>;
}
