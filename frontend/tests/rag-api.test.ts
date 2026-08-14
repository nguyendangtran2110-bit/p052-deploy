import { describe, expect, it, vi } from "vitest";
import { askRagAssistant } from "@/src/lib/rag-api";
import { demoAccounts } from "@/src/mock/data";
import { POST } from "@/app/api/rag/chat/route";

const resident = demoAccounts.find((account) => account.role === "resident") ?? null;
const manager = demoAccounts.find((account) => account.role === "manager") ?? null;

describe("RAG assistant client", () => {
  it("maps backend RAG responses into the assistant UI contract", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      answer: "Hồ bơi mở từ 06h00.",
      citations: [{ source_file: "so-tay.pdf", page_number: 17, section_title: "Hồ bơi" }],
      session_id: "session-1",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const result = await askRagAssistant("giờ hồ bơi", resident, null);

    expect(fetchMock).toHaveBeenCalledWith("/api/rag/chat", expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-OnBxrd-Demo-Principal": resident?.id }),
    }));
    expect(result.answer).toBe("Hồ bơi mở từ 06h00.");
    expect(result.citations).toEqual(["so-tay.pdf - p.17 - Hồ bơi"]);
    expect(result.sessionId).toBe("session-1");
    expect(result.unavailable).toBe(false);

    fetchMock.mockRestore();
  });

  it("allows a Manager to use the same endpoint but strips resident ticket proposals", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      answer: "The handbook lists the lobby hours.",
      citations: [{ source_file: "handbook.pdf", section_title: "Lobby" }],
      proposal: { subject: "Broken door", content: "The door is broken.", urgency: "High" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const result = await askRagAssistant("lobby hours", manager, null);

    expect(fetchMock).toHaveBeenCalledWith("/api/rag/chat", expect.objectContaining({
      headers: expect.objectContaining({ "X-OnBxrd-Demo-Principal": manager?.id }),
    }));
    expect(result.proposal).toBeUndefined();
    expect(result.citations).toEqual(["handbook.pdf - Lobby"]);

    fetchMock.mockRestore();
  });

  it("preserves an allowed ticket proposal for a Resident only", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      answer: "I can suggest ticket fields for you to review.",
      citations: [{ source_file: "handbook.pdf", section_title: "Support requests" }],
      proposal: { subject: "Broken door", content: "The door is broken.", urgency: "High" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const result = await askRagAssistant("the door is broken", resident, null);

    expect(result.proposal).toEqual({ subject: "Broken door", content: "The door is broken.", urgency: "High" });
    fetchMock.mockRestore();
  });

  it("returns a safe unavailable answer when the proxy fails", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("offline"));

    const result = await askRagAssistant("giờ hồ bơi", resident, null);

    expect(result.answer).toContain("unavailable");
    expect(result.citations).toEqual([]);

    fetchMock.mockRestore();
  });

  it("authorizes a Manager server-side and returns a no-store grounded response without a proposal", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      answer: "Approved answer.",
      citations: [{ source_file: "handbook.pdf" }],
      proposal: { subject: "Must not reach a Manager", content: "Must not reach a Manager", urgency: "High" },
      ticket_patch: { subject: "Must not reach a Manager", content: "Must not reach a Manager", urgency: "High" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const response = await POST(new Request("http://localhost/api/rag/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-OnBxrd-Demo-Principal": manager?.id ?? "" },
      body: JSON.stringify({ message: "What is approved?", session_id: "manager-session" }),
    }));

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/rag/chat", expect.objectContaining({
      cache: "no-store",
      body: JSON.stringify({ message: "What is approved?", session_id: "manager-session" }),
    }));
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    await expect(response.json()).resolves.toEqual({ answer: "Approved answer.", citations: [{ source_file: "handbook.pdf" }] });

    fetchMock.mockRestore();
  });

  it("allows only grounded Manager fields and never reflects upstream errors", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        answer: "Approved answer.",
        citations: [{ source_file: "handbook.pdf" }],
        session_id: "manager-session",
        resident: { name: "Must not reach Manager" },
        ticket: { subject: "Must not reach Manager" },
        notification: { body: "Must not reach Manager" },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "provider credential must not reach client" }), { status: 500, headers: { "Content-Type": "application/json" } }));

    const request = (message: string) => new Request("http://localhost/api/rag/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-OnBxrd-Demo-Principal": manager?.id ?? "" },
      body: JSON.stringify({ message }),
    });
    const grounded = await POST(request("What is approved?"));
    await expect(grounded.json()).resolves.toEqual({
      answer: "Approved answer.",
      citations: [{ source_file: "handbook.pdf" }],
      session_id: "manager-session",
    });
    const unavailable = await POST(request("What failed?"));
    await expect(unavailable.json()).resolves.toEqual({ code: "rag_backend_error", message: "RAG assistant is unavailable" });

    fetchMock.mockRestore();
  });

  it("treats an uncited answer as unavailable rather than grounded", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ answer: "Uncited answer" }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const result = await askRagAssistant("What is approved?", resident, null);

    expect(result.unavailable).toBe(true);
    expect(result.answer).toContain("could not verify");
    fetchMock.mockRestore();
  });

  it("rejects an unknown principal before forwarding a RAG request", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");

    const response = await POST(new Request("http://localhost/api/rag/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-OnBxrd-Demo-Principal": "untrusted-role" },
      body: JSON.stringify({ message: "What is approved?" }),
    }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toMatchObject({ code: "assistant_session_required" });
    expect(fetchMock).not.toHaveBeenCalled();
    fetchMock.mockRestore();
  });
});
