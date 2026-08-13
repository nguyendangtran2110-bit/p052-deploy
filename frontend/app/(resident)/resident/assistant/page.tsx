"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ChatIcon, ShieldIcon } from "@/src/components/icons";
import { Button, Card, PageHeader } from "@/src/components/primitives";
import { mockLLM, type AssistantResult } from "@/src/lib/mock-llm";
import { useApp } from "@/src/components/providers";
import { holdProposal } from "@/src/lib/volatile-store";
import { useRouter } from "next/navigation";

export default function AssistantPage() {
  const { account } = useApp();
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<AssistantResult | null>(null);
  const [loading, setLoading] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!message.trim()) return; setLoading(true); setResult(await mockLLM(message, account?.building)); setLoading(false); };
  return <div className="page"><PageHeader title="Building assistant" description="Ask about approved building information or prepare a ticket proposal you review yourself." action={<Link className="button button-secondary" href="/resident/tickets/new?intent=new">Open manual ticket</Link>} /><div className="assistant-layout"><Card className="assistant-thread reveal reveal-2"><div className="assistant-intro"><span><ChatIcon /></span><h2>What can I help you find?</h2><p>Try “When can I collect a parcel?” or describe a building issue.</p></div>{result ? <div className="assistant-answer" aria-live="polite"><span className="assistant-avatar"><ChatIcon /></span><div><p>{result.answer}</p>{result.citations.length ? <div className="citations"><strong>Approved sources</strong>{result.citations.map((citation) => <span key={citation}>{citation}</span>)}</div> : null}{result.blocked.length ? <div className="safety-block"><ShieldIcon /><span><strong>Untrusted output contained</strong>{result.blocked.join(" · ")}</span></div> : null}</div></div> : null}<form onSubmit={submit} className="assistant-form"><label><span className="sr-only">Message</span><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask about your building or describe an issue…" rows={3} /></label><Button disabled={loading}>{loading ? "Checking approved sources…" : "Send message"}</Button></form></Card><aside className="proposal-zone reveal reveal-3">{result?.proposal ? <Card className="proposal-card"><span className="proposal-label">Assistant proposal · not submitted</span><h2>Review ticket fields</h2><dl><div><dt>Subject</dt><dd>{result.proposal.subject}</dd></div><div><dt>Content</dt><dd>{result.proposal.content}</dd></div><div><dt>Urgency</dt><dd>{result.proposal.urgency}</dd></div></dl><button className="button button-primary" onClick={() => { if (account && result.proposal) { holdProposal(account, result.proposal); router.push("/resident/tickets/new"); } }}>Review in ticket workspace</button></Card> : <Card><h2>Bounded by design</h2><p>The assistant can propose Subject, Content, and Urgency. It cannot change verified identity, contact details, location, or submit a ticket.</p></Card>}</aside></div></div>;
}
