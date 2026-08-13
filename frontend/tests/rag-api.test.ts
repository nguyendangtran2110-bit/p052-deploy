import { describe, expect, it, vi } from "vitest";
import { askRagAssistant } from "@/src/lib/rag-api";
import { demoAccounts } from "@/src/mock/data";

const resident = demoAccounts.find((account) => account.role === "resident") ?? null;

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

    fetchMock.mockRestore();
  });

  it("returns a safe unavailable answer when the proxy fails", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("offline"));

    const result = await askRagAssistant("giờ hồ bơi", resident, null);

    expect(result.answer).toContain("unavailable");
    expect(result.citations).toEqual([]);

    fetchMock.mockRestore();
  });
});
