import { apiRequest, API_BASE_URL, isApiError, USE_MOCKS } from "@/lib/api-client";
import { getAccessToken, refreshAccessToken } from "@/lib/auth-session";
import type { TokenResponse } from "@/types";

export type RealtimeState = "connected" | "connecting" | "offline";
export interface RealtimeEvent {
  event: string;
  data: Record<string, unknown>;
}
export type RealtimeListener = (state: RealtimeState, event?: RealtimeEvent) => void;

let activeController: AbortController | null = null;
let activeStop: (() => void) | null = null;

export function connectRealtime(listener: RealtimeListener) {
  disconnectRealtime();
  if (USE_MOCKS) {
    listener("connected");
    return () => undefined;
  }

  let active = true;
  let attempt = 0;

  const stop = () => {
    active = false;
    activeController?.abort();
    activeController = null;
    if (activeStop === stop) activeStop = null;
  };
  activeStop = stop;

  const run = async () => {
    while (active) {
      const token = getAccessToken();
      if (!token) {
        listener("offline");
        return;
      }
      listener("connecting");
      activeController = new AbortController();
      try {
        const response = await fetch(`${API_BASE_URL}/realtime/stream`, {
          headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream" },
          signal: activeController.signal,
        });
        if (response.status === 401) {
          const refreshed = await refreshAccessToken((refreshToken) =>
            apiRequest<TokenResponse>("/auth/refresh", {
              method: "POST",
              body: JSON.stringify({ refresh_token: refreshToken }),
              skipRefresh: true,
            }),
          );
          if (!refreshed) {
            listener("offline");
            return;
          }
          continue;
        }
        if (response.status === 403 || response.status === 404) {
          listener("offline");
          return;
        }
        if (!response.ok || !response.body) throw new Error(`SSE ${response.status}`);
        attempt = 0;
        listener("connected");
        await readStream(response.body, listener, () => active);
      } catch (error) {
        if (!active || (error instanceof DOMException && error.name === "AbortError")) return;
        if (isApiError(error) && error.status === 401) {
          const refreshed = await refreshAccessToken((refreshToken) =>
            apiRequest<TokenResponse>("/auth/refresh", {
              method: "POST",
              body: JSON.stringify({ refresh_token: refreshToken }),
              skipRefresh: true,
            }),
          );
          if (!refreshed) {
            listener("offline");
            return;
          }
          continue;
        }
      } finally {
        activeController = null;
      }
      if (!active) return;
      attempt += 1;
      listener("connecting");
      await delay(Math.min(30_000, 800 * 2 ** Math.min(attempt, 5)));
    }
  };

  void run();
  return stop;
}

export function disconnectRealtime() {
  activeStop?.();
  activeStop = null;
  activeController?.abort();
  activeController = null;
}

async function readStream(body: ReadableStream<Uint8Array>, listener: RealtimeListener, isActive: () => boolean) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (isActive()) {
    const { done, value } = await reader.read();
    if (done) return;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split(/\r?\n\r?\n/);
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const event = parseSseChunk(chunk);
      if (event) listener("connected", event);
    }
  }
}

export function parseSseChunk(chunk: string): RealtimeEvent | null {
  const event = chunk.match(/^event:\s*(.+)$/m)?.[1]?.trim();
  if (!event) return null;
  const dataLines = chunk.split(/\r?\n/).filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim());
  const rawData = dataLines.join("\n");
  let data: Record<string, unknown> = {};
  if (rawData) {
    try {
      const parsed = JSON.parse(rawData);
      if (parsed && typeof parsed === "object") data = parsed as Record<string, unknown>;
    } catch {
      // Ignore malformed event data but preserve the event signal.
    }
  }
  return { event, data };
}

function delay(ms: number) {
  return new Promise<void>((resolve) => window.setTimeout(resolve, ms));
}
