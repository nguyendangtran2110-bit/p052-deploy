"use client";

import { FormEvent, KeyboardEvent, ReactNode, useState } from "react";
import Link from "next/link";
import { ChatIcon, ShieldIcon } from "@/src/components/icons";
import { Button, Card, PageHeader } from "@/src/components/primitives";
import type { AssistantResult } from "@/src/lib/mock-llm";
import { askRagAssistant } from "@/src/lib/rag-api";
import { useApp } from "@/src/components/providers";
import { holdProposal } from "@/src/lib/volatile-store";
import { useRouter } from "next/navigation";

export default function AssistantPage() {
  const { account } = useApp();
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [submittedMessage, setSubmittedMessage] = useState("");
  const [result, setResult] = useState<AssistantResult | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const question = message.trim();
    if (!question) return;
    setSubmittedMessage(question);
    setMessage("");
    setLoading(true);
    const nextResult = await askRagAssistant(question, account, sessionId);
    setResult(nextResult);
    if (nextResult.sessionId) setSessionId(nextResult.sessionId);
    setLoading(false);
  };

  return (
    <div className="page">
      <PageHeader
        title="Homie Agent"
        description="Ask about approved building information or prepare a ticket proposal you review yourself."
        action={<Link className="button button-secondary" href="/resident/tickets/new?intent=new">Open manual ticket</Link>}
      />
      <div className="assistant-layout">
        <Card className={`assistant-thread reveal reveal-2 ${result ? "assistant-thread-active" : ""}`}>
          <div className="assistant-intro">
            <span><ChatIcon /></span>
            <h2>What can I help you find?</h2>
            <p>Try “When can I collect a parcel?” or describe a building issue.</p>
          </div>

          {result ? (
            <div className="assistant-exchange" aria-live="polite">
              {submittedMessage ? (
                <div className="assistant-question-row">
                  <div className="assistant-question">
                    <span>You</span>
                    <p>{submittedMessage}</p>
                  </div>
                </div>
              ) : null}
              <div className="assistant-answer">
                <span className="assistant-avatar"><ChatIcon /></span>
                <div className="assistant-response">
                  <AssistantText text={result.answer} />
                  {result.citations.length ? <CitationList citations={result.citations} /> : null}
                  {result.blocked.length ? (
                    <div className="safety-block">
                      <ShieldIcon />
                      <span><strong>Untrusted output contained</strong>{result.blocked.join(" · ")}</span>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ) : loading && submittedMessage ? (
            <div className="assistant-exchange" aria-live="polite">
              <div className="assistant-question-row">
                <div className="assistant-question">
                  <span>You</span>
                  <p>{submittedMessage}</p>
                </div>
              </div>
              <div className="assistant-answer">
                <span className="assistant-avatar"><ChatIcon /></span>
                <div className="assistant-response">
                  <div className="assistant-copy">
                    <p>Checking approved sources…</p>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          <form onSubmit={submit} className="assistant-form">
            <label>
              <span className="sr-only">Message</span>
              <textarea value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={submitOnEnter} placeholder="Ask about your building or describe an issue…" rows={3} />
            </label>
            <Button disabled={loading}>{loading ? "Checking approved sources…" : "Send message"}</Button>
          </form>
        </Card>

        <aside className="proposal-zone reveal reveal-3">
          {result?.proposal ? (
            <Card className="proposal-card">
              <span className="proposal-label">Homie Agent proposal · not submitted</span>
              <h2>Review ticket fields</h2>
              <dl>
                <div><dt>Subject</dt><dd>{result.proposal.subject}</dd></div>
                <div><dt>Content</dt><dd>{result.proposal.content}</dd></div>
                <div><dt>Urgency</dt><dd>{result.proposal.urgency}</dd></div>
              </dl>
              <button className="button button-primary" onClick={() => { if (account && result.proposal) { holdProposal(account, result.proposal); router.push("/resident/tickets/new"); } }}>Review in ticket workspace</button>
            </Card>
          ) : (
            <Card>
              <h2>Bounded by design</h2>
              <p>Homie Agent can propose Subject, Content, and Urgency. It cannot change verified identity, contact details, location, or submit a ticket.</p>
            </Card>
          )}
        </aside>
      </div>
    </div>
  );
}

function submitOnEnter(event: KeyboardEvent<HTMLTextAreaElement>) {
  if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
  event.preventDefault();
  event.currentTarget.form?.requestSubmit();
}

function AssistantText({ text }: { text: string }) {
  const lines = text.split(/\n+/).map((line) => line.trim()).filter(Boolean);
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(<ul key={`list-${blocks.length}`}>{listItems.map((item) => <li key={item}>{inlineMarkdown(item)}</li>)}</ul>);
    listItems = [];
  };

  lines.forEach((line) => {
    const listMatch = line.match(/^[-•]\s+(.+)$/);
    if (listMatch) {
      listItems.push(listMatch[1]);
      return;
    }
    flushList();
    blocks.push(<p key={`p-${blocks.length}`}>{inlineMarkdown(line)}</p>);
  });
  flushList();

  return <div className="assistant-copy">{blocks}</div>;
}

function CitationList({ citations }: { citations: string[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="citations" aria-label="Approved sources">
      <div className="citation-heading">
        <strong>Approved sources</strong>
        <span>{citations.length} refs</span>
      </div>
      <div className="citation-list">
        {citations.map((citation, index) => {
          const expanded = openIndex === index;
          const parsed = parseCitation(citation);
          return (
            <article className="citation-item" key={`${citation}-${index}`}>
              <button className="citation-toggle" type="button" aria-expanded={expanded} onClick={() => setOpenIndex(expanded ? null : index)}>
                <span className="citation-source">{parsed.source}</span>
                <span className="citation-page">{parsed.page}</span>
                <span className="citation-arrow" aria-hidden="true">›</span>
              </button>
              {expanded ? <p className="citation-detail">{parsed.detail}</p> : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function parseCitation(citation: string) {
  const [head, ...detailParts] = citation.split(": ");
  const detail = detailParts.join(": ").trim() || citation;
  const parts = head.split(" - ").map((part) => part.trim()).filter(Boolean);
  const source = parts[0] ?? "Resident handbook";
  const page = parts.find((part) => /^p\.\d+/i.test(part)) ?? "Source";
  const section = parts.filter((part) => part !== source && part !== page).join(" - ");
  return { source, page, detail: section ? `${section}. ${detail}` : detail };
}

function inlineMarkdown(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    return part;
  });
}
