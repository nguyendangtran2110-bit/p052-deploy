"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Button, FormField } from "@/src/components/primitives";
import { useStageFocus } from "@/src/components/use-stage-focus";

type RecoveryStage = "identity" | "verify" | "complete";
type ChallengeState = "ready" | "invalid" | "expired" | "limited" | "unavailable";

export default function RecoveryPage() {
  const [stage, setStage] = useState<RecoveryStage>("identity");
  const [challengeState, setChallengeState] = useState<ChallengeState>("ready");
  const stageRef = useStageFocus(stage);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (stage === "verify" && challengeState !== "ready") return;
    setStage(stage === "identity" ? "verify" : "complete");
  };

  return (
    <div ref={stageRef} className="public-form-page">
      <section className="public-form-card reveal">
        <header><h1>Recover account access</h1><p>Responses remain generic so account existence and registry details are never disclosed.</p></header>
        {stage !== "complete" ? (
          <form onSubmit={submit} className="stack">
            {stage === "identity" ? (
              <><FormField label="Username or building-issued ID"><input required /></FormField><Button>Start recovery</Button></>
            ) : (
              <>
                <h2 data-stage-focus tabIndex={-1}>Verify your recovery request</h2>
                <div className="notice"><strong>If the identity is eligible, a challenge was created.</strong><span>Enter the code and a new passphrase. No real provider is called in this preview.</span></div>
                {challengeState !== "ready" ? <div className="error-summary" role="alert"><strong>{challengeTitle(challengeState)}</strong><span>No account detail is disclosed and no passphrase was changed.</span></div> : null}
                <FormField id="recovery-otp" label="One-time code" error={challengeState === "invalid" ? "Check the code and try again." : undefined}><input inputMode="numeric" required /></FormField>
                <FormField label="New passphrase"><input type="password" minLength={12} required /></FormField>
                <Button>Complete recovery</Button>
                <div className="edge-controls" aria-label="Synthetic recovery states">
                  <Button kind="quiet" type="button" onClick={() => setChallengeState("invalid")}>Invalid code</Button>
                  <Button kind="quiet" type="button" onClick={() => setChallengeState("expired")}>Expired</Button>
                  <Button kind="quiet" type="button" onClick={() => setChallengeState("limited")}>Rate limited</Button>
                  <Button kind="quiet" type="button" onClick={() => setChallengeState("unavailable")}>Provider unavailable</Button>
                  {challengeState !== "ready" ? <Button kind="secondary" type="button" onClick={() => setChallengeState("ready")}>Request fresh challenge</Button> : null}
                </div>
              </>
            )}
          </form>
        ) : (
          <div className="result-panel"><span className="result-mark">✓</span><h2 data-stage-focus tabIndex={-1}>Recovery flow complete</h2><p>This synthetic result demonstrates the durable success state. Other sessions would be revoked by the backend.</p><Link className="button button-primary" href="/login">Return to sign in</Link></div>
        )}
        <p className="back-link"><Link href="/login">Back to sign in</Link></p>
      </section>
    </div>
  );
}

function challengeTitle(state: ChallengeState) {
  if (state === "invalid") return "Code invalid";
  if (state === "expired") return "Challenge expired";
  if (state === "limited") return "Too many attempts";
  return "Recovery provider unavailable";
}
