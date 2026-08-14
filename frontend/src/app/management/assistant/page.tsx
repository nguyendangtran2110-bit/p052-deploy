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

export default function ManagementAssistantPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [authorized, setAuthorized] = useState(false);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    const account = getAccount();
    const allowed = USE_MOCKS || (account?.role === "management" && ["manager", "admin"].includes(account.management_profile?.management_role ?? ""));
    if (!allowed) router.replace(account?.role === "resident" ? "/app" : "/management");
    setAuthorized(allowed);
  }, [router]);

  async function startConversation() {
    setPending(true);
    try {
      const response = await createManagerAssistantConversation();
      router.push(`/management/assistant/${response.conversation_id}`);
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Could not create an assistant conversation." });
    } finally {
      setPending(false);
    }
  }

  if (!authorized) return <AppShell><div className="workspace-loading" style={{ minHeight: 280 }}><span>Checking management access...</span></div></AppShell>;
  return <AppShell>
    <PageHeader eyebrow="Management / AI assistant" title="Draft an announcement with AI" description="Describe the announcement in chat. The assistant collects the required fields, creates a draft after confirmation, and asks for a separate publish confirmation." />
    <div className="editor-layout">
      <Card><div className="workflow-panel"><div className="section-heading"><div><h2>Announcement assistant</h2><p>Manager and admin only</p></div><Bot size={21} color="#087f77" /></div><div className="assistant-note">The assistant never publishes automatically. You review the audience, attachments, expiry and content at both confirmation steps.</div><div className="workflow-grid"><div className="workflow-field"><span>Step 1</span><strong>Extract title, content, type, priority and audience</strong></div><div className="workflow-field"><span>Step 2</span><strong>Create a draft after your confirmation</strong></div><div className="workflow-field"><span>Step 3</span><strong>Publish only after a separate confirmation</strong></div><div className="workflow-field"><span>Files</span><strong>Upload through private S3 presigned URLs</strong></div></div><Button onClick={() => void startConversation()} disabled={pending}><Bot size={16} /> {pending ? "Opening assistant..." : "Start announcement assistant"} <ArrowRight size={15} /></Button></div></Card>
      <Card className="editor-preview"><div className="preview-label">Guardrails</div><div className="queue-list"><div className="queue-item"><div className="activity-icon"><ShieldCheck size={15} /></div><div className="queue-copy"><strong>Backend validates role and workflow version</strong><p>UI is not the authority for permission or audience.</p></div><Badge tone="success">JWT / RBAC</Badge></div><div className="queue-item"><div className="activity-icon"><FileText size={15} /></div><div className="queue-copy"><strong>Draft and publish are separate actions</strong><p>A stale revision returns a conflict instead of overwriting data.</p></div></div><div className="queue-item"><div className="activity-icon"><Megaphone size={15} /></div><div className="queue-copy"><strong>Announcement lifecycle remains auditable</strong><p>Normal announcement APIs remain available for advanced edits.</p></div></div></div></Card>
    </div>
  </AppShell>;
}
