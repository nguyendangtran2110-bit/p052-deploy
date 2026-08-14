"use client";

import { type KeyboardEvent, useRef, useState } from "react";
import { benefits } from "@/src/mock/data";
import { Card, PageHeader } from "@/src/components/primitives";

export default function BenefitsPage() {
  const [open, setOpen] = useState<string | null>(benefits[0].title);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const moveTab = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const last = benefits.length - 1;
    const next = event.key === "Home" ? 0 : event.key === "End" ? last : event.key === "ArrowRight" || event.key === "ArrowDown" ? (index + 1) % benefits.length : event.key === "ArrowLeft" || event.key === "ArrowUp" ? (index - 1 + benefits.length) % benefits.length : null;
    if (next === null) return;
    event.preventDefault();
    setOpen(benefits[next].title);
    tabRefs.current[next]?.focus();
  };
  return <div className="page"><PageHeader title="Benefits for your home" description="Only the services applicable to your verified building context appear here." /><div className="benefit-layout reveal reveal-2"><div className="benefit-index" role="tablist" aria-label="Building benefits">{benefits.map((benefit, index) => { const selected = open === benefit.title; const key = benefit.title.toLowerCase().replaceAll(" ", "-"); return <button ref={(element) => { tabRefs.current[index] = element; }} id={`benefit-tab-${key}`} role="tab" aria-selected={selected} aria-controls={`benefit-panel-${key}`} tabIndex={selected ? 0 : -1} className={selected ? "benefit-tab selected" : "benefit-tab"} key={benefit.title} onClick={() => setOpen(benefit.title)} onKeyDown={(event) => moveTab(event, index)}><span>{String(index + 1).padStart(2, "0")}</span><strong>{benefit.title}</strong><small>{benefit.category}</small></button>; })}</div><Card className="benefit-detail">{benefits.filter((benefit) => benefit.title === open).map((benefit) => { const key = benefit.title.toLowerCase().replaceAll(" ", "-"); return <div id={`benefit-panel-${key}`} role="tabpanel" aria-labelledby={`benefit-tab-${key}`} key={benefit.title}><span className="benefit-symbol" aria-hidden="true"><i/><i/><i/></span><h2>{benefit.title}</h2><p>{benefit.body}</p><dl className="detail-grid"><div><dt>Access</dt><dd>Verified Resident</dd></div><div><dt>Building</dt><dd>Your assigned home</dd></div><div><dt>Availability</dt><dd>See building guidance</dd></div></dl></div>; })}</Card></div></div>;
}
