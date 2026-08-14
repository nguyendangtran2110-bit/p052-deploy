"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { ChatIcon } from "@/src/components/icons";
import { useApp } from "@/src/components/providers";
import { askRagAssistant, type RagAssistantResult } from "@/src/lib/rag-api";
import { holdProposal } from "@/src/lib/volatile-store";
import type { Role } from "@/src/mock/data";
import { useRouter } from "next/navigation";

type ConversationItem = {
  question: string;
  result: RagAssistantResult;
};

export function HomieAgent({ role }: { role: Role }) {
  const { account } = useApp();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState<ConversationItem[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) window.setTimeout(() => inputRef.current?.focus(), 0);
  }, [open]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = message.trim();
    if (!question || loading) return;

    setMessage("");
    setLoading(true);
    const result = await askRagAssistant(question, account, sessionId);
    setConversation((current) => [...current, { question, result }].slice(-6));
    if (result.sessionId) setSessionId(result.sessionId);
    setLoading(false);
  };

  const submitOnEnter = (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
    event.preventDefault();
    event.currentTarget.form?.requestSubmit();
  };

  const reviewProposal = (result: RagAssistantResult) => {
    if (!account || !result.proposal || role !== "resident") return;
    holdProposal(account, result.proposal);
    router.push("/resident/tickets/new");
  };

  return (
    <section className="homie-agent" aria-label="Homie Agent">
      <button
        className="homie-agent-launcher"
        type="button"
        aria-controls="homie-agent-panel"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ChatIcon />
        <span>Homie Agent</span>
      </button>
      {open ? <aside id="homie-agent-panel" className="homie-agent-panel" aria-label="Homie Agent workside panel">
        <header className="homie-agent-header">
          <div>
            <h2>Homie Agent</h2>
            <p>Grounded answers from approved building information.</p>
          </div>
        </header>
        <div className="homie-agent-conversation" aria-live="polite" aria-busy={loading}>
          {conversation.length ? conversation.map(({ question, result }, index) => (
            <div className="homie-agent-exchange" key={`${question}-${index}`}>
              <p className="homie-agent-message homie-agent-message-user" aria-label="Your question">{question}</p>
              <div className="homie-agent-message homie-agent-message-assistant">
                <strong>Homie Agent</strong>
                <p>{result.answer}</p>
                {result.citations.length ? <ul className="homie-agent-citations" aria-label="Approved sources">{result.citations.map((citation, citationIndex) => <li key={`${citation}-${citationIndex}`}>{citation}</li>)}</ul> : null}
                {role === "resident" && result.proposal ? <button className="homie-agent-review-proposal" type="button" onClick={() => reviewProposal(result)}>Review ticket fields</button> : null}
                {result.unavailable ? <p className="homie-agent-status" role="status">Try again shortly. {role === "resident" ? <Link className="homie-agent-manual-ticket-link" href="/resident/tickets/new?intent=new">You can also open a manual ticket.</Link> : null}</p> : null}
              </div>
            </div>
          )) : <p className="homie-agent-status">Ask about approved building information. Answers include sources when available.</p>}
          {loading ? <p className="homie-agent-status">Checking approved sources…</p> : null}
        </div>
        <form className="homie-agent-composer" onSubmit={submit}>
          <label htmlFor="homie-agent-message">Message</label>
          <textarea ref={inputRef} className="homie-agent-input" id="homie-agent-message" value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={submitOnEnter} maxLength={5000} rows={3} placeholder="Ask about your building…" />
          <button className="homie-agent-submit" type="submit" disabled={loading || !message.trim()}>{loading ? "Checking…" : "Send"}</button>
        </form>
      </aside> : null}
    </section>
  );
}
