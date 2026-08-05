const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export type DraftPayload = { id: string; title: string; category: string; priority: string; location: string; description: string; status: string };

export async function queryAgent(message: string, actorRole: "resident" | "manager") {
  const response = await fetch(`${API_BASE}/chat/query`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, actor_role: actorRole }) });
  if (!response.ok) throw new Error("OnBxrd could not process this message.");
  return response.json();
}

export async function createDraft(message: string): Promise<DraftPayload> {
  const response = await fetch(`${API_BASE}/ticket-drafts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, actor_role: "resident" }) });
  if (!response.ok) throw new Error("Unable to create ticket draft.");
  return response.json();
}

export async function submitDraft(draftId: string) {
  const response = await fetch(`${API_BASE}/ticket-drafts/${draftId}/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_role: "resident" }) });
  if (!response.ok) throw new Error("Unable to submit ticket draft.");
  return response.json();
}

export async function updateTicket(ticketId: string, status: string, note?: string) {
  const response = await fetch(`${API_BASE}/tickets/${ticketId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_role: "manager", status, note }) });
  if (!response.ok) throw new Error("Unable to update ticket.");
  return response.json();
}

export async function contactResident(ticketId: string) {
  const response = await fetch(`${API_BASE}/tickets/${ticketId}/contact-resident`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_role: "manager" }) });
  if (!response.ok) throw new Error("Unable to contact resident.");
  return response.json();
}
