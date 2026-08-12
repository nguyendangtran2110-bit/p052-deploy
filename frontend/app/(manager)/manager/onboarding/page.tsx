"use client";

import { useApp } from "@/src/components/providers";
import { EmptyState, PageHeader, StatusBadge } from "@/src/components/primitives";
import { residentProfiles } from "@/src/mock/data";

export default function ManagerOnboardingPage() {
  const { account } = useApp();
  const residents = residentProfiles.filter((resident) => account && resident.building === account.building && (account.floors.includes("ALL_FLOORS") || account.floors.includes(resident.floor)));
  return <div className="page manager-page"><PageHeader title="Onboarding oversight" description="Inspect incomplete and blocked progress. Reminder actions are automated and not available here." />{residents.length ? <div className="progress-board reveal reveal-2">{residents.map((resident) => { const progress = resident.onboarding.startsWith("5") ? "progress-100" : resident.onboarding.startsWith("3") ? "progress-60" : "progress-40"; return <article key={resident.id}><div className="progress-person"><span className="avatar">{resident.name[0]}</span><span><strong>{resident.name}</strong><small>{resident.building} · {resident.floor}-{resident.room}</small></span></div><div className="progress-track" aria-label={resident.onboarding}><span className={progress} /></div><span>{resident.onboarding}</span><StatusBadge status={resident.state} /></article>; })}</div> : <EmptyState title="No onboarding records" description="There are no scoped residents in the current manager grants." />}</div>;
}
