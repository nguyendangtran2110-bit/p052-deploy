import { afterEach, describe, expect, it, vi } from "vitest";
import { parseApiError } from "@/lib/api-client";
import { parseSseChunk } from "@/lib/realtime";
import { assignTicket, createAnnouncement, createManagerAssistantConversation, createTicket, fetchConversationById, fetchHandoffs, fetchManagementOnboarding, fetchResidentOnboarding, sendChat, sendManagerAssistantMessage, sendResidentAssistantMessage, updateAnnouncement, updateOnboardingItem, uploadAttachment } from "@/lib/data";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("backend connection adapters", () => {
  it("parses FastAPI validation errors into field errors", async () => {
    const error = await parseApiError(new Response(JSON.stringify({ detail: [{ loc: ["body", "unit_id"], msg: "Input should be a valid UUID" }] }), { status: 422 }));
    expect(error.status).toBe(422);
    expect(error.fieldErrors?.unit_id).toBe("Input should be a valid UUID");
  });

  it("sends ticket creation with the caller-owned idempotency key", async () => {
    const ticket = { id: "real-ticket", ticket_code: "TCK-1", unit_id: "real-unit", status: "submitted" };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(ticket), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    await createTicket({ unit_id: "real-unit", category: "maintenance", priority: "medium", title: "Door", description: "Door is broken", location: "real-unit" }, "retry-stable-key");
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect((request.headers as Headers).get("Idempotency-Key")).toBe("retry-stable-key");
    expect(String(fetchMock.mock.calls[0][0])).toContain("/tickets");
  });

  it("does not invent a conversation id for the first general chat message", async () => {
    const response = { conversation_id: "real-conversation", response: "ok", citations: [], action: null, ticket: null };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await sendChat({ message: "hello", unit_id: "real-unit" });
    const body = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(body.unit_id).toBe("real-unit");
    expect(body).not.toHaveProperty("conversation_id");
  });

  it("sends resident workflow confirmation fields to the chat endpoint", async () => {
    const response = {
      conversation_id: "conversation-id",
      response: "preview",
      citations: [],
      action: { type: "create_ticket", action_id: "action-id", requires_confirmation: true, payload: {} },
      ticket: null,
      workflow_id: "workflow-id",
      workflow_type: "resident_ticket",
      state: "awaiting_confirmation",
      workflow_version: 4,
      draft: { title: "Door" },
      missing_fields: [],
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const result = await sendResidentAssistantMessage({
      message: "Confirm ticket creation",
      conversation_id: "conversation-id",
      unit_id: "unit-id",
      workflow_id: "workflow-id",
      workflow_version: 4,
      confirmed_action_id: "action-id",
      confirm_action: true,
      idempotency_key: "stable-key",
    });
    const body = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(body).toMatchObject({ workflow_id: "workflow-id", workflow_version: 4, confirmed_action_id: "action-id", confirm_action: true, idempotency_key: "stable-key" });
    expect(result.action?.action_id).toBe("action-id");
    expect(String(fetchMock.mock.calls[0][0])).toContain("/chat/messages");
  });

  it("uses manager assistant endpoints and keeps publish confirmation separate", async () => {
    const conversation = { conversation_id: "conversation-id", workflow_id: "workflow-id", workflow_type: "manager_announcement", state: "collecting", workflow_version: 0, messages: [], draft: {}, missing_fields: [], action: null };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(conversation), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...conversation, state: "awaiting_publish_confirmation", workflow_version: 2, action: { type: "publish_announcement", action_id: "publish-id", requires_confirmation: true, payload: {} } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const created = await createManagerAssistantConversation();
    await sendManagerAssistantMessage(created.conversation_id, { message: "Confirm publish", workflow_id: created.workflow_id, workflow_version: 1, confirmed_action_id: "publish-id", confirm_action: true, idempotency_key: "publish-retry" });
    expect(String(fetchMock.mock.calls[0][0])).toContain("/management/assistant/conversations");
    const body = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(body).toMatchObject({ workflow_id: "workflow-id", workflow_version: 1, confirmed_action_id: "publish-id", confirm_action: true, idempotency_key: "publish-retry" });
    expect(String(fetchMock.mock.calls[1][0])).toContain("/management/assistant/conversations/conversation-id/messages");
  });

  it("keeps handoff list response as ConversationSummary", async () => {
    const response = { items: [{ conversation_id: "conversation-id", resident_id: "resident-id", unit_id: "unit-id", status: "active", handoff_status: "waiting_management", conversation_version: 3, last_message_at: "2026-08-12T00:00:00Z", ticket_id: null, ticket_code: null }], total: 1, offset: 0, limit: 50 };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const result = await fetchHandoffs();
    expect(result.items[0]).toMatchObject({ conversation_id: "conversation-id", ticket_id: null });
    expect(result.items[0]).not.toHaveProperty("ticket");
  });

  it("loads a general conversation by the UUID from the URL", async () => {
    const response = { conversation_id: "conversation-id", messages: [], ticket: null };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await fetchConversationById("conversation-id");
    expect(String(fetchMock.mock.calls[0][0])).toContain("/conversations/conversation-id");
  });

  it("sends announcement update fields with the server version", async () => {
    const response = { id: "announcement-id", version: 4 };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await updateAnnouncement("announcement-id", { version: 3, title: "Updated title" });
    const body = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(body).toEqual({ version: 3, title: "Updated title" });
  });

  it("creates announcement scopes without client-side audience guessing", async () => {
    const response = { id: "announcement-id", version: 0 };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    await createAnnouncement({ title: "Notice", content: "Content", type: "general", priority: "normal", scopes: [{ scope_type: "building", project_code: "P-001", building: "A" }] });
    const body = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(body.scopes).toEqual([{ scope_type: "building", project_code: "P-001", building: "A" }]);
  });

  it("sends real assignment UUID or null with due_at", async () => {
    const response = { id: "ticket-id", assigned_to_id: null };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await assignTicket("ticket-id", null, "2026-08-13T12:00:00.000Z");
    const body = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(body).toEqual({ assignee_account_id: null, due_at: "2026-08-13T12:00:00.000Z" });
  });

  it("presigns then uploads an attachment without a nonexistent complete call", async () => {
    const presign = { id: "attachment-id", filename: "photo.png", mime_type: "image/png", size_bytes: 3, upload_url: "https://storage.test/upload" };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(presign), { status: 201 }))
      .mockResolvedValueOnce(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await uploadAttachment(new File(["abc"], "photo.png", { type: "image/png" }), { ticket_id: "ticket-id" });
    const presignBody = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(presignBody).toMatchObject({ ticket_id: "ticket-id", announcement_id: null });
    expect(presignBody).not.toHaveProperty("message_id");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect((fetchMock.mock.calls[1][1] as RequestInit).method).toBe("PUT");
  });

  it("loads resident onboarding through the scoped API route", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await fetchResidentOnboarding("unit/one");
    expect(String(fetchMock.mock.calls[0][0])).toContain("/onboarding?unit_id=unit%2Fone");
  });

  it("serializes management onboarding filters without client-side scope guessing", async () => {
    const response = { items: [], total: 0, offset: 0, limit: 25 };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await fetchManagementOnboarding({ search: "A-01", building: "North", is_completed: false, limit: 25 });
    expect(String(fetchMock.mock.calls[0][0])).toContain("/management/onboarding?");
    expect(String(fetchMock.mock.calls[0][0])).toContain("search=A-01");
    expect(String(fetchMock.mock.calls[0][0])).toContain("building=North");
    expect(String(fetchMock.mock.calls[0][0])).toContain("is_completed=false");
    expect(String(fetchMock.mock.calls[0][0])).toContain("limit=25");
  });

  it("maps the UI skipped status to the backend onboarding status", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "item-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await updateOnboardingItem("item-1", "skipped");
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).toEqual({ status: "not_applicable" });
  });

  it.each(["read", "unread"] as const)("sends the backend-supported %s information status unchanged", async (status) => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "item-1", status }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await updateOnboardingItem("item-1", status);
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).toEqual({ status });
  });
});

describe("SSE parser", () => {
  it("parses event name and JSON data", () => {
    expect(parseSseChunk('event: conversation.message.created\ndata: {"conversation_id":"c-1","ticket_id":"t-1"}')).toEqual({
      event: "conversation.message.created",
      data: { conversation_id: "c-1", ticket_id: "t-1" },
    });
  });

  it("ignores a comment/heartbeat without an event", () => {
    expect(parseSseChunk(": keep-alive\ndata: {}")).toBeNull();
  });
});
