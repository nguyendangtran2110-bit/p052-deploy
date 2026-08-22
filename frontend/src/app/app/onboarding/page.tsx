"use client";

import Link from "next/link";
import { BookOpen, Check, Circle, ExternalLink, Home, Info, RotateCcw } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, EmptyState, PageHeader, ProgressBar } from "@/components/ui";
import { useOnboarding, useUpdateOnboardingItem } from "@/features/onboarding/queries";
import type { OnboardingCategory, OnboardingChecklist, OnboardingItem } from "@/types";
import { useUiStore } from "@/stores/ui-store";

const categoryLabels: Record<OnboardingCategory, string> = {
  handover: "Handover",
  utilities: "Utilities",
  guidance: "Information",
};

const categoryOrder: OnboardingCategory[] = ["handover", "utilities", "guidance"];

export default function ResidentOnboardingPage() {
  const onboarding = useOnboarding();
  const update = useUpdateOnboardingItem();
  const showToast = useUiStore((state) => state.showToast);

  async function changeStatus(item: OnboardingItem, status: OnboardingItem["status"]) {
    try {
      await update.mutateAsync({ itemId: item.id, status });
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Could not update checklist." });
    }
  }

  return <AppShell>
    <PageHeader
      eyebrow="Resident / Move-in"
      title="Your move-in checklist"
      description="Track practical handover tasks and read the key information for your apartment. Management can see your progress, but does not need to approve each item."
      actions={<Link href="/app/chat"><Button variant="outline"><BookOpen size={16} /> Ask the assistant</Button></Link>}
    />
    {onboarding.isLoading ? <div className="empty-state"><p>Loading checklist...</p></div> : onboarding.isError ? <div className="error-state"><Info size={18} /><div><strong>Could not load your checklist.</strong><p>Try again after checking that your account has an active unit.</p></div></div> : onboarding.data?.items.length ? <div className="dashboard-grid">{onboarding.data.items.map((checklist) => <ChecklistCard key={checklist.id} checklist={checklist} onChange={changeStatus} updating={update.isPending} />)}</div> : <EmptyState icon={<Home size={20} />} title="No active unit yet" description="Your move-in checklist appears after management links an active unit to your resident profile." />}
  </AppShell>;
}

function ChecklistCard({ checklist, onChange, updating }: { checklist: OnboardingChecklist; onChange: (item: OnboardingItem, status: OnboardingItem["status"]) => Promise<void>; updating: boolean }) {
  const grouped = categoryOrder.map((category) => ({ category, items: checklist.items.filter((item) => item.category === category) })).filter((group) => group.items.length);
  return <Card>
    <div className="section-heading">
      <div><div style={{ display: "flex", alignItems: "center", gap: 8 }}><Home size={16} color="var(--teal)" /><h2>{checklist.unit.unit_number}</h2><Badge tone="neutral">Building {checklist.unit.building}</Badge></div><p>{checklist.completed_item_count} of {checklist.required_item_count} required items completed</p></div>
      <strong style={{ color: "var(--teal)", fontSize: 22 }}>{checklist.progress_percent}%</strong>
    </div>
    <ProgressBar value={checklist.progress_percent} />
    <div style={{ display: "grid", gap: 20, marginTop: 24 }}>{grouped.map((group) => <section key={group.category}><div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}><span className="eyebrow">{categoryLabels[group.category]}</span></div><div style={{ display: "grid", gap: 8 }}>{group.items.map((item) => <ChecklistItem key={item.id} item={item} onChange={onChange} updating={updating} />)}</div></section>)}</div>
  </Card>;
}

function ChecklistItem({ item, onChange, updating }: { item: OnboardingItem; onChange: (item: OnboardingItem, status: OnboardingItem["status"]) => Promise<void>; updating: boolean }) {
  const isDone = item.item_type === "task" ? ["completed", "not_applicable"].includes(item.status) : item.status === "read";
  const nextStatus = item.item_type === "task" ? (isDone ? "pending" : "completed") : (isDone ? "unread" : "read");
  return <div style={{ display: "flex", alignItems: "flex-start", gap: 11, padding: "13px 0", borderTop: "1px solid var(--line)" }}>
    <div style={{ width: 28, height: 28, display: "grid", placeItems: "center", flex: "0 0 auto", color: isDone ? "var(--teal)" : "#9aa9ad", background: isDone ? "var(--mint)" : "#f3f6f6", borderRadius: 8 }}>{isDone ? <Check size={16} /> : item.item_type === "information" ? <BookOpen size={15} /> : <Circle size={14} />}</div>
    <div style={{ minWidth: 0, flex: 1 }}><div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}><strong style={{ color: "var(--ink-strong)", fontSize: 13 }}>{item.title}</strong>{item.is_required && <Badge tone="info">Required</Badge>}{isDone && <Badge tone="success">{item.item_type === "task" ? "Completed" : "Read"}</Badge>}</div><p style={{ marginTop: 5, color: "var(--muted)", fontSize: 12, lineHeight: 1.45 }}>{item.summary}</p>{item.handbook_reference && <Link href={`/app/chat?topic=${encodeURIComponent(item.handbook_reference)}`} style={{ display: "inline-flex", alignItems: "center", gap: 5, marginTop: 7, color: "var(--teal)", fontSize: 11, fontWeight: 700 }}><ExternalLink size={12} /> Ask about this</Link>}</div>
    <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap", justifyContent: "flex-end" }}><Button variant={isDone ? "ghost" : "secondary"} size="sm" disabled={updating} onClick={() => void onChange(item, nextStatus)}>{isDone ? <><RotateCcw size={13} /> Undo</> : <><Check size={13} /> {item.item_type === "task" ? "Complete" : "Mark read"}</>}</Button>{item.item_type === "task" && !isDone && <Button variant="ghost" size="sm" disabled={updating} onClick={() => void onChange(item, "not_applicable")}>N/A</Button>}</div>
  </div>;
}
