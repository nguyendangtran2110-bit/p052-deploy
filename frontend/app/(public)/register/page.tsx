"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Button, CheckList, FormField } from "@/src/components/primitives";
import { useStageFocus } from "@/src/components/use-stage-focus";

const stages = ["Account type", "Identity", "Verification"];

export default function RegisterPage() {
  const [stage, setStage] = useState(0);
  const [role, setRole] = useState<"resident" | "manager">("resident");
  const [message, setMessage] = useState("");
  const [challengeState, setChallengeState] = useState<"ready" | "invalid" | "expired" | "limited" | "unavailable">("ready");
  const stageRef = useStageFocus(String(stage));
  const next = (event: FormEvent) => { event.preventDefault(); setStage((current) => Math.min(2, current + 1)); };
  return (
    <div ref={stageRef} className="public-form-page">
      <section className="public-form-card reveal">
        <header><h1>Activate your account</h1><p>Use the identity details issued by your building. Administrator registration is not available here.</p></header>
        <ol className="stepper" aria-label="Registration progress">{stages.map((item, index) => <li key={item} aria-current={index === stage ? "step" : undefined} className={index <= stage ? "active" : ""}><span>{index + 1}</span>{item}</li>)}</ol>
        {stage === 0 ? <form onSubmit={next} className="stack">
          <fieldset className="choice-field"><legend>Choose your account type</legend><label className={role === "resident" ? "choice selected" : "choice"}><input type="radio" name="role" checked={role === "resident"} onChange={() => setRole("resident")} /><strong>Resident</strong><span>Access onboarding, benefits, assistant, tickets, and notifications.</span></label><label className={role === "manager" ? "choice selected" : "choice"}><input type="radio" name="role" checked={role === "manager"} onChange={() => setRole("manager")} /><strong>Manager</strong><span>Work only within your assigned building and floor pairs.</span></label></fieldset><Button>Continue</Button>
        </form> : null}
        {stage === 1 ? <form onSubmit={next} className="stack"><h2 data-stage-focus tabIndex={-1}>Confirm your building identity</h2><FormField label={role === "resident" ? "Building-issued resident ID" : "Building-issued manager ID"} hint="This preview does not contact a real registry."><input required placeholder={role === "resident" ? "SYN-RES-000" : "SYN-MGR-000"} /></FormField><FormField label="Username"><input required /></FormField><FormField label="Passphrase" hint="Use at least 12 characters in an integrated environment."><input type="password" required minLength={12} /></FormField><FormField label="Contact for verification"><input required placeholder="Synthetic contact only" /></FormField><div className="form-actions"><Button kind="quiet" type="button" onClick={() => setStage(0)}>Back</Button><Button>Send verification</Button></div></form> : null}
        {stage === 2 ? <form onSubmit={(event) => { event.preventDefault(); if (challengeState !== "ready") return; setMessage("Synthetic activation complete. Continue to sign in with a demo identity."); }} className="stack"><h2 data-stage-focus tabIndex={-1}>Enter your verification code</h2><div className="notice"><strong>Verification challenge created</strong><span>A real environment would show the server-selected masked destination and expiry here.</span></div>{challengeState !== "ready" ? <div className="error-summary" role="alert"><strong>{challengeState === "invalid" ? "Code invalid" : challengeState === "expired" ? "Challenge expired" : challengeState === "limited" ? "Too many attempts" : "Verification provider unavailable"}</strong><span>{challengeState === "limited" ? "Wait for the server-provided retry time." : "Nothing was activated. Retry or request a fresh synthetic challenge."}</span></div> : null}<FormField id="register-otp" label="One-time code" error={challengeState === "invalid" ? "Check the code and try again." : undefined}><input inputMode="numeric" autoComplete="one-time-code" required /></FormField><Button>Verify and activate</Button><div className="edge-controls" aria-label="Synthetic challenge states"><Button kind="quiet" type="button" onClick={() => setChallengeState("invalid")}>Invalid code</Button><Button kind="quiet" type="button" onClick={() => setChallengeState("expired")}>Expired</Button><Button kind="quiet" type="button" onClick={() => setChallengeState("limited")}>Rate limited</Button><Button kind="quiet" type="button" onClick={() => setChallengeState("unavailable")}>Provider unavailable</Button>{challengeState !== "ready" ? <Button kind="secondary" type="button" onClick={() => setChallengeState("ready")}>Request fresh challenge</Button> : null}</div>{message ? <div className="success-message" role="status">{message}</div> : null}</form> : null}
        <CheckList items={["Resident and Manager only", "Generic identity-safe errors", "Server-confirmed role and scope"]} />
        <p className="back-link">Already active? <Link href="/login">Sign in</Link></p>
      </section>
    </div>
  );
}
