"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Bot, FileText, Megaphone, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, PageHeader } from "@/components/ui";
import { createManagerAssistantConversation } from "@/lib/data";
import { getAccount } from "@/lib/auth-session";
import { USE_MOCKS } from "@/lib/api-client";
import { useUiStore } from "@/stores/ui-store";

const ASSISTANT_START_TIMEOUT_MS = 15000;

function withTimeout<T>(promise: Promise<T>, timeoutMs: number) {
  return new Promise<T>((resolve, reject) => {
    const timeout = window.setTimeout(() => reject(new Error("The assistant took too long to start. Please try again.")), timeoutMs);
    promise.then(
      (value) => {
        window.clearTimeout(timeout);
        resolve(value);
      },
      (error) => {
        window.clearTimeout(timeout);
        reject(error);
      },
    );
  });
}

export default function ManagementAssistantPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [authorized, setAuthorized] = useState(false);
  const [pending, setPending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const account = getAccount();
    const allowed = USE_MOCKS || (account?.role === "management" && ["manager", "admin"].includes(account.management_profile?.management_role ?? ""));
    if (!allowed) router.replace(account?.role === "resident" ? "/app" : "/management");
    setAuthorized(allowed);
  }, [router]);

  async function startConversation() {
    setPending(true);
    setErrorMessage(null);
    try {
      const response = await withTimeout(createManagerAssistantConversation(), ASSISTANT_START_TIMEOUT_MS);
      if (!response.conversation_id) throw new Error("The assistant conversation was created without an ID.");

      const destination = `/management/assistant/${encodeURIComponent(response.conversation_id)}`;
      router.replace(destination);

      // A dev-server compile or a stale client transition can leave the URL unchanged.
      // Full navigation is a last-resort fallback so the button cannot remain stuck.
      window.setTimeout(() => {
        if (window.location.pathname !== destination) window.location.assign(destination);
      }, 1500);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not create an assistant conversation.";
      setErrorMessage(message);
      showToast({ tone: "error", message });
    } finally {
      setPending(false);
    }
  }

  if (!authorized) return <AppShell><div className="workspace-loading" style={{ minHeight: 280 }}><span>Checking management access...</span></div></AppShell>;
  return <AppShell>
    <PageHeader eyebrow="Management / AI assistant" title="Draft an announcement with AI" description="Describe the announcement in chat. The assistant collects the required fields, creates a draft after confirmation, and asks for a separate publish confirmation." />
    <div className="editor-layout">
      <Card><div className="workflow-panel"><div className="section-heading"><div><h2>Announcement assistant</h2><p>Manager and admin only</p></div><Bot size={21} color="#087f77" /></div><div className="assistant-note">The assistant never publishes automatically. You review the audience, attachments, expiry and content at both confirmation steps.</div><div className="workflow-grid"><div className="workflow-field"><span>Step 1</span><strong>Extract title, content, type, priority and audience</strong></div><div className="workflow-field"><span>Step 2</span><strong>Create a draft after your confirmation</strong></div><div className="workflow-field"><span>Step 3</span><strong>Publish only after a separate confirmation</strong></div><div className="workflow-field"><span>Files</span><strong>Upload through private S3 presigned URLs</strong></div></div><Button type="button" onClick={() => void startConversation()} disabled={pending}><Bot size={16} /> {pending ? "Opening assistant..." : "Start announcement assistant"} <ArrowRight size={15} /></Button>{errorMessage && <div className="error-state" role="alert" style={{ marginTop: 12 }}>{errorMessage}</div>}</div></Card>
      <Card className="editor-preview"><div className="preview-label">Guardrails</div><div className="queue-list"><div className="queue-item"><div className="activity-icon"><ShieldCheck size={15} /></div><div className="queue-copy"><strong>Backend validates role and workflow version</strong><p>UI is not the authority for permission or audience.</p></div><Badge tone="success">JWT / RBAC</Badge></div><div className="queue-item"><div className="activity-icon"><FileText size={15} /></div><div className="queue-copy"><strong>Draft and publish are separate actions</strong><p>A stale revision returns a conflict instead of overwriting data.</p></div></div><div className="queue-item"><div className="activity-icon"><Megaphone size={15} /></div><div className="queue-copy"><strong>Announcement lifecycle remains auditable</strong><p>Normal announcement APIs remain available for advanced edits.</p></div></div></div></Card>
    </div>
  </AppShell>;
}
