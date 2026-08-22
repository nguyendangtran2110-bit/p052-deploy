"use client";

import { Check, ClipboardCheck, Circle, Clock3, Eye, EyeOff, MinusCircle } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, EmptyState, PageHeader } from "@/components/ui";
import { ErrorState } from "@/components/feedback";
import { useResidentOnboarding, useUpdateOnboardingItem } from "@/features/onboarding/queries";
import type { OnboardingItem, OnboardingUpdateStatus } from "@/types";
import type { CSSProperties } from "react";

export default function ResidentOnboardingPage() {
  const onboarding = useResidentOnboarding();
  const update = useUpdateOnboardingItem();
  const checklists = onboarding.data?.items ?? [];
  const totalItems = checklists.reduce((total, checklist) => total + checklist.required_item_count, 0);
  const completedItems = checklists.reduce((total, checklist) => total + checklist.completed_item_count, 0);

  return <AppShell><PageHeader eyebrow="Resident space / Onboarding" title="Your building welcome" description="Work through the checklist attached to your verified home. Updates are saved to OnBxrd." actions={checklists.length ? <Badge tone="info">{completedItems} / {totalItems} complete</Badge> : undefined} />
    {onboarding.isLoading ? <Card><div className="loading-copy" role="status">Loading your onboarding checklist…</div></Card> : onboarding.isError ? <ErrorState message="We could not load onboarding for your current account scope." onRetry={() => void onboarding.refetch()} /> : !checklists.length ? <Card><EmptyState icon={<ClipboardCheck size={22} />} title="No onboarding checklist yet" description="Your building team has not published an onboarding checklist for this account." /></Card> : <div className="onboarding-list">{checklists.map((checklist) => <Card key={checklist.id}><div className="onboarding-card-heading"><div><div className="eyebrow">{checklist.unit.building} · {checklist.unit.unit_number}</div><h2>Welcome checklist</h2><p>{checklist.completed_item_count} of {checklist.required_item_count} required steps complete · updated {new Date(checklist.updated_at).toLocaleDateString("en-GB")}</p></div><div className="onboarding-progress" style={{ "--onboarding-progress": `${checklist.progress_percent}%` } as CSSProperties} aria-label={`${checklist.progress_percent}% complete`}><strong>{checklist.progress_percent}%</strong><span /></div></div><div className="onboarding-items">{checklist.items.slice().sort((a, b) => a.sort_order - b.sort_order).map((item) => <OnboardingItemRow key={item.id} item={item} pending={update.isPending && update.variables?.id === item.id} onStatus={(status) => update.mutate({ id: item.id, status })} />)}</div></Card>)}</div>}
  </AppShell>;
}

function OnboardingItemRow({ item, pending, onStatus }: { item: OnboardingItem; pending: boolean; onStatus: (status: OnboardingUpdateStatus) => void }) {
  const icon = item.status === "completed" ? <Check size={17} /> : item.status === "read" ? <Eye size={17} /> : item.status === "not_applicable" ? <MinusCircle size={17} /> : item.status === "unread" ? <Circle size={17} /> : <Clock3 size={17} />;
  const label = item.status === "completed" ? "Completed" : item.status === "read" ? "Read" : item.status === "not_applicable" ? "Skipped" : item.status === "unread" ? "Unread" : "Pending";
  return <article className={`onboarding-item onboarding-item-${item.status}`}><span className="onboarding-item-icon" aria-hidden="true">{icon}</span><div className="onboarding-item-copy"><div className="onboarding-item-title"><h3>{item.title}</h3><Badge tone={item.status === "completed" || item.status === "read" ? "success" : item.status === "not_applicable" ? "neutral" : "warning"}>{label}</Badge></div><p>{item.summary}</p>{item.handbook_reference && <small>Reference: {item.handbook_reference}</small>}</div>{item.item_type === "task" ? <label className="onboarding-status-control"><span className="sr-only">Status for {item.title}</span><select value={item.status === "not_applicable" ? "skipped" : item.status} disabled={pending} onChange={(event) => onStatus(event.target.value as "pending" | "completed" | "skipped")}><option value="pending">Pending</option><option value="completed">Completed</option><option value="skipped">Skipped</option></select></label> : <Button variant="outline" disabled={pending} onClick={() => onStatus(item.status === "read" ? "unread" : "read")}>{item.status === "read" ? <EyeOff size={15} /> : <Eye size={15} />}{item.status === "read" ? "Mark unread" : "Mark as read"}</Button>}</article>;
}
