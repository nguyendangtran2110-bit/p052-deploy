"use client";

import { useState } from "react";
import { CheckIcon } from "@/src/components/icons";
import { Button, Card, PageHeader, StatusBadge } from "@/src/components/primitives";
import { onboardingSteps } from "@/src/mock/data";
import Link from "next/link";

export default function OnboardingPage() {
  const [completed, setCompleted] = useState(false);
  return <div className="page"><PageHeader title="Your building welcome path" description="One step at a time, with progress that stays visible across sessions." action={<StatusBadge status={completed ? "4 of 5 complete" : "3 of 5 complete"} />} /><div className="resident-split"><section className="process-list reveal reveal-2" aria-label="Onboarding steps">{onboardingSteps.map((step, index) => { const currentCompleted = completed && index === 2; const state = currentCompleted ? "Completed" : step.state; return <article className={`process-step state-${state.toLowerCase()}`} key={step.title}><span className="process-index">{state === "Completed" ? <CheckIcon /> : index + 1}</span><div><div className="process-heading"><h2>{step.title}</h2><StatusBadge status={state} /></div><p>{step.detail}</p>{state === "Current" ? <Button onClick={() => setCompleted(true)}>Mark step complete</Button> : null}</div></article>; })}</section><aside className="context-rail reveal reveal-3"><Card><h2>Next best step</h2><p>{completed ? "Review the shared-space rules when you are ready." : "Add one emergency contact. Verification happens before the change is saved."}</p><span className="signal-rule" /></Card><Card className="inverse-card"><h2>Need a hand?</h2><p>Homie Agent can explain approved guidance or help prepare a ticket.</p><Link className="button button-secondary" href="/resident/assistant">Ask Homie Agent</Link></Card></aside></div></div>;
}
