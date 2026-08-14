"use client";

import type { DemoAccount } from "@/src/mock/data";
import { sanitizeModelText, validateAssistantResult, type AssistantResult } from "@/src/lib/mock-llm";

type RAGCitation = {
  source_file?: unknown;
  page_number?: unknown;
  section_title?: unknown;
  relevance?: unknown;
};

type RAGChunk = {
  source_file?: unknown;
  page_number?: unknown;
  section_title?: unknown;
  text?: unknown;
};

type RAGChatResponse = {
  answer?: unknown;
  citations?: unknown;
  chunks?: unknown;
  session_id?: unknown;
  proposal?: unknown;
};

export type RagAssistantResult = AssistantResult & { sessionId?: string; unavailable: boolean };

export async function askRagAssistant(message: string, account: DemoAccount | null, sessionId?: string | null): Promise<RagAssistantResult> {
  if (!account) {
    return unavailableResult("Please sign in before using Homie Agent.");
  }

  try {
    const response = await fetch("/api/rag/chat", {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-OnBxrd-Demo-Principal": account.id,
      },
      body: JSON.stringify({ message, ...(sessionId ? { session_id: sessionId } : {}) }),
    });
    const payload = await safeJson(response);

    if (!response.ok) return unavailableResult("Homie Agent is unavailable right now. Please try again shortly.");
    return toAssistantResult(payload, account.role);
  } catch {
    return unavailableResult("Homie Agent is unavailable right now. Please try again shortly.");
  }
}

function toAssistantResult(payload: unknown, role: DemoAccount["role"]): RagAssistantResult {
  const record = isRecord(payload) ? payload as RAGChatResponse : {};
  const citations = citationLabels(record.citations, record.chunks);
  if (!citations.length) return unavailableResult("Homie Agent could not verify an approved source for that answer. Please try again shortly.");
  const result = validateAssistantResult({
    answer: sanitizeModelText(record.answer),
    citations,
    blocked: [],
    proposal: record.proposal,
  });
  const sessionId = typeof record.session_id === "string" && record.session_id.length <= 120 ? record.session_id : undefined;
  const managerSafeResult = role === "manager" ? { ...result, proposal: undefined } : result;
  return { ...managerSafeResult, ...(sessionId ? { sessionId } : {}), unavailable: false };
}

function citationLabels(citations: unknown, chunks: unknown) {
  const fromCitations = Array.isArray(citations) ? citations.map(formatCitation).filter(Boolean) : [];
  if (fromCitations.length) return fromCitations;
  return Array.isArray(chunks) ? chunks.slice(0, 3).map(formatChunk).filter(Boolean) : [];
}

function formatCitation(value: unknown) {
  if (!isRecord(value)) return "";
  return formatSource(value as RAGCitation);
}

function formatChunk(value: unknown) {
  if (!isRecord(value)) return "";
  const chunk = value as RAGChunk;
  const source = formatSource(chunk);
  const excerpt = sanitizeModelText(chunk.text).slice(0, 180).trim();
  return source && excerpt ? `${source}: ${excerpt}` : source;
}

function formatSource(value: RAGCitation | RAGChunk) {
  const source = sanitizeModelText(value.source_file).trim();
  const pageNumber = typeof value.page_number === "number" && value.page_number > 0 ? `p.${value.page_number}` : "";
  const sectionTitle = sanitizeModelText(value.section_title).trim();
  const relevance = "relevance" in value ? sanitizeModelText(value.relevance).slice(0, 140).trim() : "";
  return [source, pageNumber, sectionTitle, relevance].filter(Boolean).join(" - ");
}

function unavailableResult(answer: string): RagAssistantResult {
  return { answer, citations: [], blocked: [], unavailable: true };
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function isRecord(value: unknown) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
