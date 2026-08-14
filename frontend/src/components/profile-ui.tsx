"use client";

import { FormEvent, useState } from "react";
import { Button, Card, FormField, StatusBadge } from "@/src/components/primitives";
import { useApp } from "@/src/components/providers";
import type { DemoAccount } from "@/src/mock/data";

export function ProfileUI({ account }: { account: DemoAccount }) {
  const { theme, setTheme } = useApp();
  const [name, setName] = useState(account.name);
  const [contact, setContact] = useState("");
  const [password, setPassword] = useState("");
  const [zalo, setZalo] = useState("");
  const [challenge, setChallenge] = useState(false);
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");
  const [contactError, setContactError] = useState("");
  const [zaloError, setZaloError] = useState("");

  const saveContact = (event: FormEvent) => {
    event.preventDefault();
    if (!challenge) { setChallenge(true); setMessage("Synthetic verification challenge created. The destination remains masked and no provider was called."); return; }
    if (otp !== "246810") { setContactError("The synthetic code is invalid or expired. Use 246810 to exercise the verified success state."); return; }
    setContactError(""); setMessage("Contact replacement verified. The synthetic profile now shows the new masked destination."); setChallenge(false); setOtp("");
  };
  const savePassword = (event: FormEvent) => { event.preventDefault(); setMessage("Passphrase changed for this synthetic flow. Other sessions would be revoked by the backend."); setPassword(""); };
  const saveZalo = (event: FormEvent) => {
    event.preventDefault();
    if (zalo && !/^https:\/\/zalo\.me\/[A-Za-z0-9._-]+$/.test(zalo)) { setZaloError("Enter a structurally valid https://zalo.me/... link. This checks format only, not profile existence or ownership."); return; }
    setZaloError(""); setMessage(zalo ? "Zalo link format accepted. The profile is not verified or confirmed." : "Personal Zalo link removed from this synthetic profile.");
  };
  const clearFeedback = () => setMessage("");

  return <div className="profile-layout">
    <Card className="profile-identity reveal reveal-2"><h2>Verified identity</h2><p className="muted">Identity and building scope are server-controlled and cannot be edited here.</p><dl className="detail-grid"><div><dt>Account</dt><dd>{account.username}</dd></div><div><dt>Role</dt><dd><StatusBadge status={account.role === "resident" ? "Resident" : "Manager"} /></dd></div><div><dt>Building</dt><dd>{account.building}</dd></div><div><dt>{account.role === "resident" ? "Home floor" : "Assignments"}</dt><dd>{account.floors.includes("ALL_FLOORS") ? "All floors" : account.floors.join(", ")}</dd></div></dl></Card>
    <section className="profile-work reveal reveal-3" aria-label="Profile settings">
      <Card className="profile-section"><h2>Preferences</h2><p>Choose how this demo workspace looks. Your saved display name stays local to this session.</p><FormField id="display-name" label="Display name"><input value={name} onChange={(event) => { setName(event.target.value); clearFeedback(); }} /></FormField><fieldset className="theme-field"><legend>Appearance</legend><button type="button" onClick={() => setTheme("light")} aria-pressed={theme === "light"} className={theme === "light" ? "theme-choice selected" : "theme-choice"}><span className="theme-preview light-preview" />Light</button><button type="button" onClick={() => setTheme("dark")} aria-pressed={theme === "dark"} className={theme === "dark" ? "theme-choice selected" : "theme-choice"}><span className="theme-preview dark-preview" />Dark</button></fieldset><div className="form-actions"><Button type="button" onClick={() => setMessage("Preferences saved for this synthetic demo session.")}>Save preferences</Button></div></Card>
      <Card className="profile-section"><h2>Verified contact</h2><p>Replace the contact destination using the synthetic verification flow.</p><form onSubmit={saveContact}><FormField id="contact-replacement" label="New phone or email" hint="The server chooses and masks the verification destination."><input required value={contact} onChange={(event) => { setContact(event.target.value); clearFeedback(); }} /></FormField>{challenge ? <FormField id="contact-otp" label="One-time code" error={contactError}><input inputMode="numeric" autoComplete="one-time-code" required value={otp} onChange={(event) => { setOtp(event.target.value); setContactError(""); }} /></FormField> : null}<div className="form-actions"><Button>{challenge ? "Verify replacement" : "Start verification"}</Button></div></form></Card>
      <Card className="profile-section"><h2>Change passphrase</h2><p>Use at least 12 characters. The live system would revoke other sessions after success.</p><form onSubmit={savePassword}><FormField id="new-password" label="New passphrase" hint="At least 12 characters. Other sessions are revoked after success."><input type="password" required minLength={12} value={password} onChange={(event) => { setPassword(event.target.value); clearFeedback(); }} /></FormField><div className="form-actions"><Button>Change passphrase</Button></div></form></Card>
      {account.role === "resident" ? <Card className="profile-section"><h2>Personal Zalo link</h2><p>Add an optional personal link. OnBxrd checks only its format, not profile ownership.</p><form onSubmit={saveZalo}><FormField id="zalo-link" label="Personal Zalo link" hint="Format validation only; OnBxrd does not verify profile existence or ownership." error={zaloError}><input type="url" value={zalo} onChange={(event) => { setZalo(event.target.value); setZaloError(""); clearFeedback(); }} placeholder="https://zalo.me/synthetic-profile" /></FormField><div className="form-actions"><Button>Save Zalo link</Button></div></form></Card> : null}
      {message ? <p className="success-message" role="status">{message}</p> : null}
    </section>
  </div>;
}
