import { beforeEach, describe, expect, it } from "vitest";
import { demoAccounts } from "@/src/mock/data";
import { getDraft, getTicket, listTickets, resetMockTicketStateForTests, startDraft, submitDraft, updateDraft } from "@/src/mock/server-ticket-store";

const lagoon = demoAccounts.find((account) => account.id === "demo-resident-lagoon")!;
const ember = demoAccounts.find((account) => account.id === "demo-resident-ember")!;
const managerEight = demoAccounts.find((account) => account.id === "demo-manager-eight")!;

describe("server-owned synthetic ticket drafts", () => {
  beforeEach(resetMockTicketStateForTests);

  it("keeps one versioned account draft outside browser storage and reports stale conflicts", () => {
    const started = startDraft(lagoon);
    const saved = updateDraft(lagoon, started.draft.draftId, started.draft.version, { subject: "Durable subject", content: "Durable content" });
    if (!("draft" in saved) || !saved.draft) throw new Error("expected saved draft");
    expect(saved.draft.value.subject).toBe("Durable subject");
    expect(getDraft(lagoon)?.value.content).toBe("Durable content");

    const stale = updateDraft(lagoon, started.draft.draftId, started.draft.version, { urgency: "High" });
    expect(stale).toMatchObject({ error: "ticket_draft_conflict" });
    if ("current" in stale) expect(stale.current?.value.urgency).toBe("Normal");
  });

  it("creates unique durable tickets visible in history/detail and exact Manager scope", () => {
    const first = createTicket("First durable ticket", "idem-first");
    const second = createTicket("Second durable ticket", "idem-second");
    expect(first.id).not.toBe(second.id);
    expect(listTickets(lagoon).map((ticket) => ticket.id)).toEqual(expect.arrayContaining([first.id, second.id]));
    expect(getTicket(lagoon, first.id)?.subject).toBe("First durable ticket");
    expect(getTicket(ember, first.id)).toBeNull();
    expect(getTicket(managerEight, first.id)?.id).toBe(first.id);
  });

  it("returns the original committed ticket when an outcome-unknown submission retries the same key", () => {
    const started = startDraft(lagoon).draft;
    const saved = updateDraft(lagoon, started.draftId, started.version, { subject: "[simulate outcome unknown] retry", content: "Committed once" });
    if (!("draft" in saved) || !saved.draft) throw new Error("expected saved draft");
    const first = submitDraft(lagoon, saved.draft.draftId, saved.draft.version, saved.draft.fieldFingerprint, "stable-submit-key");
    expect(first).toMatchObject({ simulatedUnknown: true });
    const retry = submitDraft(lagoon, saved.draft.draftId, saved.draft.version, saved.draft.fieldFingerprint, "stable-submit-key");
    expect(retry).toMatchObject({ simulatedUnknown: false });
    if (!("ticket" in first) || !first.ticket || !("ticket" in retry) || !retry.ticket) throw new Error("expected idempotent ticket result");
    expect(retry.ticket.id).toBe(first.ticket.id);
  });
});

function createTicket(subject: string, key: string) {
  const started = startDraft(lagoon).draft;
  const saved = updateDraft(lagoon, started.draftId, started.version, { subject, content: `${subject} content` });
  if (!("draft" in saved) || !saved.draft) throw new Error("expected saved draft");
  const submitted = submitDraft(lagoon, saved.draft.draftId, saved.draft.version, saved.draft.fieldFingerprint, key);
  if (!("ticket" in submitted) || !submitted.ticket) throw new Error("expected submitted ticket");
  return submitted.ticket;
}
