"use client";

import { CheckCircle2, Clock3, Search, Users } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Card, Input, PageHeader, ProgressBar, Select } from "@/components/ui";
import { useOnboardingProgress } from "@/features/onboarding/queries";

export default function ManagementOnboardingPage() {
  const [search, setSearch] = useState("");
  const [completion, setCompletion] = useState("");
  const progress = useOnboardingProgress({ search: search || undefined, is_completed: completion === "" ? undefined : completion === "true", limit: 50 });
  const items = progress.data?.items ?? [];
  return <AppShell>
    <PageHeader eyebrow="Management / Resident progress" title="Move-in progress" description="Read-only overview of resident self-confirmations. No manager approval is required for individual checklist items." />
    <Card padding={false}>
      <div style={{ padding: 16, borderBottom: "1px solid var(--line)" }}><div className="filter-bar"><div className="filter-search"><Search size={15} /><Input aria-label="Search onboarding progress" placeholder="Name, resident code or unit..." value={search} onChange={(event) => setSearch(event.target.value)} /></div><Select aria-label="Completion status" value={completion} onChange={(event) => setCompletion(event.target.value)}><option value="">All progress</option><option value="true">Completed</option><option value="false">In progress</option></Select></div></div>
      {progress.isError ? <div className="error-state">Could not load onboarding progress.</div> : progress.isLoading ? <div className="empty-state"><p>Loading progress...</p></div> : items.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Resident</th><th>Unit</th><th>Progress</th><th>Status</th><th>Updated</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><div style={{ display: "flex", alignItems: "center", gap: 9 }}><div className="avatar avatar-small">{item.resident_name.split(" ").map((part) => part[0]).slice(-2).join("")}</div><div><div className="row-title">{item.resident_name}</div><div className="row-subtitle">{item.resident_code}</div></div></div></td><td><div className="row-title">{item.unit.unit_number}</div><div className="row-subtitle">{item.unit.project_code} / Building {item.unit.building}</div></td><td style={{ minWidth: 190 }}><div style={{ display: "flex", justifyContent: "space-between", marginBottom: 7, color: "var(--muted)", fontSize: 11 }}><span>{item.completed_item_count}/{item.required_item_count} required</span><strong style={{ color: "var(--teal)" }}>{item.progress_percent}%</strong></div><ProgressBar value={item.progress_percent} /></td><td>{item.completed_at ? <Badge tone="success"><CheckCircle2 size={12} /> Completed</Badge> : <Badge tone="warning"><Clock3 size={12} /> In progress</Badge>}</td><td>{new Date(item.updated_at).toLocaleDateString("en-GB")}</td></tr>)}</tbody></table></div> : <div className="empty-state"><Users size={24} /><h3>No checklist progress</h3><p>Residents with an active unit will appear here after their checklist is initialized.</p></div>}
      <div className="pagination"><span>{progress.data?.total ?? 0} resident-unit checklist(s)</span></div>
    </Card>
  </AppShell>;
}
