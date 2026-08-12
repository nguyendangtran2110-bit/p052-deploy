"use client";

import { useMemo, useState } from "react";
import { useApp } from "@/src/components/providers";
import { Card, EmptyState, PageHeader, StatusBadge } from "@/src/components/primitives";
import { residentProfiles } from "@/src/mock/data";

export default function ManagerResidentsPage() {
  const { account } = useApp();
  const [query, setQuery] = useState("");
  const residents = useMemo(() => residentProfiles.filter((resident) => account && resident.building === account.building && (account.floors.includes("ALL_FLOORS") || account.floors.includes(resident.floor))).filter((resident) => resident.name.toLowerCase().includes(query.toLowerCase()) || resident.room.includes(query)), [account, query]);
  return <div className="page manager-page"><PageHeader title="Resident directory" description="Privacy-safe resident summaries inside your exact building-floor grants." /><Card className="filter-band reveal reveal-2"><label className="field inline-field"><span className="field-label">Search scoped residents</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name or room" /></label></Card>{residents.length ? <div className="data-list reveal reveal-3"><div className="data-list-head"><span>Resident</span><span>Building</span><span>Floor</span><span>Onboarding</span><span /></div>{residents.map((resident) => <div className="data-row" key={resident.id}><span className="row-title"><strong>{resident.name}</strong><small>Synthetic resident · Room {resident.room}</small></span><span data-label="Building">{resident.building}</span><span data-label="Floor">{resident.floor}</span><span data-label="Onboarding"><StatusBadge status={resident.state} /></span><span /></div>)}</div> : <EmptyState title="No residents in this view" description="No resident is available in the current exact scope or filter. No out-of-scope identity is disclosed." />}</div>;
}
