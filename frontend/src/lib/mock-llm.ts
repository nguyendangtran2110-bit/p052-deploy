import assistantFixture from "@/mock-data/assistant-scenarios.json";

export type AssistantResult = {
  answer: string;
  citations: string[];
  proposal?: { subject: string; content: string; urgency: "Low" | "Normal" | "High" };
  blocked: string[];
};

type AssistantScenarioName = "hostile" | "ticket" | "parcel" | "unsupported";
type AssistantScenarioFixture = {
  answer: string;
  citations: string[];
  blocked: string[];
  proposal?: { subject: string; content: string; urgency: string };
  performPrivilegedAction?: unknown;
};

const allowedUrgencies = new Set(["Low", "Normal", "High"]);
const unsafeUrl = /(?:javascript:|data:text\/html|https?:\/\/|&#x?\w+;)(\S*)/gi;
const tags = /<[^>]*>/g;
const controlCharacters = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u202A-\u202E\u2066-\u2069]/g;

function assistantFixtureError(path: string): never {
  throw new Error(`Invalid assistant mock fixture at ${path}.`);
}

function scenarioRecord(value: unknown, path: string, allowedKeys: readonly string[]): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) assistantFixtureError(path);
  const record = value as Record<string, unknown>;
  if (Object.keys(record).some((key) => !allowedKeys.includes(key))) assistantFixtureError(`${path}.keys`);
  return record;
}

function scenarioString(value: unknown, path: string, maxLength = 1800): string {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > maxLength) assistantFixtureError(path);
  return value;
}

function scenarioStrings(value: unknown, path: string): string[] {
  if (!Array.isArray(value) || value.length > 6) assistantFixtureError(path);
  return value.map((item, index) => scenarioString(item, `${path}[${index}]`));
}

export function validateAssistantScenarios(value: unknown): Record<AssistantScenarioName, AssistantScenarioFixture> {
  const root = scenarioRecord(value, "assistant-scenarios.json", ["scenarios"]);
  const scenarios = scenarioRecord(root.scenarios, "scenarios", ["hostile", "ticket", "parcel", "unsupported"]);
  const names: AssistantScenarioName[] = ["hostile", "ticket", "parcel", "unsupported"];
  const result = {} as Record<AssistantScenarioName, AssistantScenarioFixture>;

  for (const name of names) {
    const path = `scenarios.${name}`;
    const record = scenarioRecord(scenarios[name], path, ["answer", "citations", "blocked", "proposal", "performPrivilegedAction"]);
    const proposalRecord = record.proposal === undefined ? null : scenarioRecord(record.proposal, `${path}.proposal`, ["subject", "content", "urgency"]);
    result[name] = {
      answer: scenarioString(record.answer, `${path}.answer`),
      citations: scenarioStrings(record.citations, `${path}.citations`),
      blocked: scenarioStrings(record.blocked, `${path}.blocked`),
      ...(proposalRecord ? {
        proposal: {
          subject: scenarioString(proposalRecord.subject, `${path}.proposal.subject`, 120),
          content: scenarioString(proposalRecord.content, `${path}.proposal.content`),
          urgency: scenarioString(proposalRecord.urgency, `${path}.proposal.urgency`, 40),
        },
      } : {}),
      ...(record.performPrivilegedAction !== undefined ? { performPrivilegedAction: record.performPrivilegedAction } : {}),
    };
  }

  if (result.ticket.proposal?.content !== "{{message}}" || result.ticket.proposal.urgency !== "{{urgency}}") {
    assistantFixtureError("scenarios.ticket.proposal.templates");
  }
  if (!result.ticket.citations.some((citation) => citation.includes("{{building}}"))) {
    assistantFixtureError("scenarios.ticket.citations");
  }
  if (!result.parcel.citations.some((citation) => citation.includes("{{building}}"))) {
    assistantFixtureError("scenarios.parcel.citations");
  }

  return result;
}

const assistantScenarios = validateAssistantScenarios(assistantFixture);

export function sanitizeModelText(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.replace(tags, "").replace(unsafeUrl, "[unsafe link removed]").replace(controlCharacters, "").slice(0, 1800);
}

export function validateAssistantResult(value: unknown): AssistantResult {
  const record = typeof value === "object" && value !== null ? value as Record<string, unknown> : {};
  const citations = Array.isArray(record.citations) ? record.citations.slice(0, 6).map(sanitizeModelText).filter(Boolean) : [];
  const blocked = Array.isArray(record.blocked) ? record.blocked.slice(0, 6).map(sanitizeModelText).filter(Boolean) : [];
  const proposalRecord = typeof record.proposal === "object" && record.proposal !== null ? record.proposal as Record<string, unknown> : null;
  const urgency = proposalRecord && allowedUrgencies.has(String(proposalRecord.urgency)) ? String(proposalRecord.urgency) as "Low" | "Normal" | "High" : null;
  const subject = proposalRecord ? sanitizeModelText(proposalRecord.subject).slice(0, 120).trim() : "";
  const content = proposalRecord ? sanitizeModelText(proposalRecord.content).trim() : "";
  const proposal = proposalRecord && urgency && subject && content ? { subject, content, urgency } : undefined;
  return { answer: sanitizeModelText(record.answer), citations, blocked, ...(proposal ? { proposal } : {}) };
}

function renderScenario(value: unknown, replacements: Record<string, string>): unknown {
  if (typeof value === "string") {
    return Object.entries(replacements).reduce((rendered, [placeholder, replacement]) => rendered.replaceAll(`{{${placeholder}}}`, replacement), value);
  }
  if (Array.isArray(value)) return value.map((item) => renderScenario(item, replacements));
  if (typeof value === "object" && value !== null) {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, renderScenario(item, replacements)]));
  }
  return value;
}

export async function mockLLM(message: string, building = "Assigned building"): Promise<AssistantResult> {
  await new Promise((resolve) => setTimeout(resolve, 420));
  const normalized = message.toLowerCase();
  const scenarioName: AssistantScenarioName = normalized.includes("hostile") || normalized.includes("ignore policy")
    ? "hostile"
    : normalized.includes("ticket") || normalized.includes("broken") || normalized.includes("issue")
      ? "ticket"
      : normalized.includes("parcel")
        ? "parcel"
        : "unsupported";
  const rendered = renderScenario(assistantScenarios[scenarioName], {
    building,
    message,
    urgency: normalized.includes("urgent") ? "High" : "Normal",
  });
  return validateAssistantResult(rendered);
}
