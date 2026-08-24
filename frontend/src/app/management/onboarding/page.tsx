"use client";

import { ClipboardCheck, Search } from "lucide-react";
import { Badge, Card, EmptyState, Input, PageHeader } from "@/components/ui";
import { ErrorState } from "@/components/feedback";
import { useManagementOnboarding } from "@/features/onboarding/queries";
import { useState } from "react";

export default function ManagementOnboardingPage() {
  const [search, setSearch] = useState("");
  const onboarding = useManagementOnboarding({ search: search || undefined, limit: 50 });
  const items = onboarding.data?.items ?? [];
  return <><PageHeader eyebrow="Management / Onboarding" title="Onboarding oversight" description="Read-only progress for residents inside your authorized management scope." />
    <Card padding={false}><div className="onboarding-filter"><div className="filter-search"><Search size={15} /><Input aria-label="Search onboarding" placeholder="Resident name or code…" value={search} onChange={(event) => setSearch(event.target.value)} /></div></div>{onboarding.isLoading ? <div className="loading-copy" role="status">Loading onboarding progress…</div> : onboarding.isError ? <ErrorState message="We could not load onboarding for your current management scope." onRetry={() => void onboarding.refetch()} /> : !items.length ? <EmptyState icon={<ClipboardCheck size={22} />} title="No onboarding progress" description="There are no onboarding checklists in the current authorized scope." /> : <div className="onboarding-management-list">{items.map((checklist) => <article className="onboarding-management-row" key={checklist.id}><div className="onboarding-management-main"><div className="row-title">{checklist.resident_name}</div><div className="row-subtitle">{checklist.resident_code} · {checklist.unit.building} · {checklist.unit.unit_number}</div></div><div className="onboarding-management-progress"><strong>{checklist.progress_percent}%</strong><span>{checklist.completed_item_count}/{checklist.required_item_count} required</span></div><Badge tone={checklist.completed_at ? "success" : "info"}>{checklist.completed_at ? "Complete" : "In progress"}</Badge></article>)}</div>}</Card>
  </>;
}
