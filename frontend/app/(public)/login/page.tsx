"use client";

import { FormEvent, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowIcon, ShieldIcon } from "@/src/components/icons";
import { Button, FormField } from "@/src/components/primitives";
import { login } from "@/src/lib/session";
import { demoAccounts } from "@/src/mock/data";
import { useApp } from "@/src/components/providers";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshSession } = useApp();
  const [username, setUsername] = useState("");
  const [passphrase, setPassphrase] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const errorSummary = useRef<HTMLDivElement>(null);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    window.setTimeout(() => {
      const account = login(username.trim(), passphrase);
      if (!account) {
        setError("We could not sign you in with those credentials. Check both fields and try again.");
        setSubmitting(false);
        window.setTimeout(() => errorSummary.current?.focus(), 0);
        return;
      }
      refreshSession();
      const requested = searchParams.get("returnTo");
      const allowed = requested?.startsWith(`/${account.role}/`) ? requested : null;
      router.push(allowed ?? (account.role === "resident" ? "/resident/onboarding" : "/manager/dashboard"));
    }, 120);
  };

  const fillDemo = (accountId: string) => {
    const account = demoAccounts.find((candidate) => candidate.id === accountId);
    if (!account) return;
    setUsername(account.username);
    setPassphrase(account.passphrase);
    setError("");
  };

  return (
    <div className="auth-stage">
      <section className="auth-story reveal">
        <div className="signal-demo" aria-hidden="true"><span className="signal-node node-a"/><span className="signal-node node-b"/><span className="signal-node node-c"/><i /></div>
        <h1>A clear signal for every building task.</h1>
        <p>Onboarding, support, and scoped operations live in one calm workspace where every change has a visible state.</p>
        <div className="trust-note"><ShieldIcon /><span><strong>Safe synthetic preview</strong><small>No production identities, contacts, tokens, or external services.</small></span></div>
      </section>
      <section className="auth-panel reveal reveal-2" aria-labelledby="login-title">
        <div>
          <Link className="auth-home-link" href="/">Back to OnBxrd home</Link>
          <h2 id="login-title">Welcome back</h2>
          <p>Sign in to your Resident or Manager workspace.</p>
        </div>
        {error ? <div ref={errorSummary} className="error-summary" role="alert" tabIndex={-1}><strong>Sign-in unsuccessful</strong><a href="#login-username">Username: check this field.</a><a href="#login-passphrase">Passphrase: check this field.</a><span>{error}</span></div> : null}
        <form onSubmit={submit}>
          <FormField id="login-username" label="Username" error={error ? "Check the username and passphrase." : undefined}><input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></FormField>
          <FormField id="login-passphrase" label="Passphrase" error={error ? "Check the username and passphrase." : undefined}><input autoComplete="current-password" type="password" value={passphrase} onChange={(event) => setPassphrase(event.target.value)} required /></FormField>
          <Button type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}<ArrowIcon /></Button>
        </form>
        <div className="auth-links"><Link href="/register">Create an account</Link><Link href="/recovery">Recover access</Link></div>
        <div className="demo-accounts">
          <h3>Six synthetic demo identities</h3>
          <p>Select an identity to fill its conspicuously demo-only credentials, then use Sign in.</p>
          <div className="demo-grid">
            {demoAccounts.map((account) => <button type="button" key={account.id} onClick={() => fillDemo(account.id)}><span className={`demo-role ${account.role}`}>{account.role}</span><strong>{account.name}</strong><small>{account.label}</small></button>)}
          </div>
        </div>
      </section>
    </div>
  );
}
