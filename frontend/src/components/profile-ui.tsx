"use client";

import { FormEvent, useState } from "react";
import { Button, Card, FormField, StatusBadge } from "@/src/components/primitives";
import { useApp } from "@/src/components/providers";
import type { DemoAccount } from "@/src/mock/data";

type Panel = "preferences" | "contact" | "password" | "zalo";

export function ProfileUI({ account }: { account: DemoAccount }) {
  const { theme, setTheme } = useApp();
  const [panel, setPanel] = useState<Panel>("preferences");
  const [name, setName] = useState(account.name);
  const [contact, setContact] = useState("");
  const [password, setPassword] = useState("");
  const [zalo, setZalo] = useState("");
  const [challenge, setChallenge] = useState(false);
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const saveContact = (event: FormEvent) => {
    event.preventDefault();
    if (!challenge) { setChallenge(true); setMessage("Synthetic verification challenge created. The destination remains masked and no provider was called."); return; }
    if (otp !== "246810") { setError("The synthetic code is invalid or expired. Use 246810 to exercise the verified success state."); return; }
    setError(""); setMessage("Contact replacement verified. The synthetic profile now shows the new masked destination."); setChallenge(false); setOtp("");
  };
  const savePassword = (event: FormEvent) => { event.preventDefault(); setMessage("Passphrase changed for this synthetic flow. Other sessions would be revoked by the backend."); setPassword(""); };
  const saveZalo = (event: FormEvent) => {
    event.preventDefault();
    if (zalo && !/^https:\/\/zalo\.me\/[A-Za-z0-9._-]+$/.test(zalo)) { setError("Enter a structurally valid https://zalo.me/... link. This checks format only, not profile existence or ownership."); return; }
    setError(""); setMessage(zalo ? "Zalo link format accepted. The profile is not verified or confirmed." : "Personal Zalo link removed from this synthetic profile.");
  };
  const choosePanel = (next: Panel) => { setPanel(next); setMessage(""); setError(""); setChallenge(false); };

  return <div className="profile-layout">
    <Card className="reveal reveal-2"><h2>Verified identity</h2><p className="muted">Identity and building scope are server-controlled and cannot be edited here.</p><dl className="detail-grid"><div><dt>Account</dt><dd>{account.username}</dd></div><div><dt>Role</dt><dd><StatusBadge status={account.role === "resident" ? "Resident" : "Manager"} /></dd></div><div><dt>Building</dt><dd>{account.building}</dd></div><div><dt>{account.role === "resident" ? "Home floor" : "Assignments"}</dt><dd>{account.floors.includes("ALL_FLOORS") ? "All floors" : account.floors.join(", ")}</dd></div></dl></Card>
    <section className="profile-work reveal reveal-3"><div className="segmented profile-tabs" aria-label="Profile tasks">{(["preferences", "contact", "password", ...(account.role === "resident" ? ["zalo"] : [])] as Panel[]).map((item) => <button key={item} aria-pressed={panel === item} onClick={() => choosePanel(item)}>{item === "zalo" ? "Zalo" : item[0].toUpperCase() + item.slice(1)}</button>)}</div><Card>
      <h2>{panel === "preferences" ? "Preferences" : panel === "contact" ? "Verified contact" : panel === "password" ? "Change passphrase" : "Personal Zalo link"}</h2>
      {panel === "preferences" ? <><FormField id="display-name" label="Display name"><input value={name} onChange={(event) => setName(event.target.value)} /></FormField><fieldset className="theme-field"><legend>Appearance</legend><button onClick={() => setTheme("light")} aria-pressed={theme === "light"} className={theme === "light" ? "theme-choice selected" : "theme-choice"}><span className="theme-preview light-preview" />Light</button><button onClick={() => setTheme("dark")} aria-pressed={theme === "dark"} className={theme === "dark" ? "theme-choice selected" : "theme-choice"}><span className="theme-preview dark-preview" />Dark</button></fieldset><div className="form-actions"><Button onClick={() => setMessage("Preferences saved for this synthetic demo session.")}>Save preferences</Button></div></> : null}
      {panel === "contact" ? <form onSubmit={saveContact}><FormField id="contact-replacement" label="New phone or email" hint="The server chooses and masks the verification destination."><input required value={contact} onChange={(event) => setContact(event.target.value)} /></FormField>{challenge ? <FormField id="contact-otp" label="One-time code" error={error}><input inputMode="numeric" autoComplete="one-time-code" required value={otp} onChange={(event) => setOtp(event.target.value)} /></FormField> : null}<div className="form-actions"><Button>{challenge ? "Verify replacement" : "Start verification"}</Button></div></form> : null}
      {panel === "password" ? <form onSubmit={savePassword}><FormField id="new-password" label="New passphrase" hint="At least 12 characters. Other sessions are revoked after success."><input type="password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} /></FormField><div className="form-actions"><Button>Change passphrase</Button></div></form> : null}
      {panel === "zalo" ? <form onSubmit={saveZalo}><FormField id="zalo-link" label="Personal Zalo link" hint="Format validation only; OnBxrd does not verify profile existence or ownership." error={error}><input type="url" value={zalo} onChange={(event) => setZalo(event.target.value)} placeholder="https://zalo.me/synthetic-profile" /></FormField><div className="form-actions"><Button>Save Zalo link</Button></div></form> : null}
      {message ? <p className="success-message" role="status">{message}</p> : null}
    </Card></section>
  </div>;
}
