import { clearSession, getAccessToken, refreshAccessToken } from "@/lib/auth-session";
import type { TokenResponse } from "@/types";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");
export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export class ApiError extends Error {
  status: number;
  code?: string;
  fieldErrors?: Record<string, string>;

  constructor(message: string, status: number, code?: string, fieldErrors?: Record<string, string>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

type RequestOptions = RequestInit & { skipRefresh?: boolean };

export async function apiRequest<T>(path: string, options: RequestOptions = {}, retried = false): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("Không thể kết nối đến máy chủ. Vui lòng thử lại.", 0, "network_error");
  }

  if (response.status === 401 && !retried && !options.skipRefresh && path !== "/auth/refresh") {
    const refreshed = await refreshAccessToken((refreshToken) =>
      apiRequest<TokenResponse>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
        skipRefresh: true,
      }),
    );
    if (refreshed) return apiRequest<T>(path, options, true);
    clearSession();
  }

  if (!response.ok) throw await parseApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function parseApiError(response: Response) {
  let payload: { error?: { code?: string; message?: string; fields?: Record<string, string> }; detail?: string | Array<{ loc?: Array<string | number>; msg?: string }> } = {};
  try {
    payload = await response.json();
  } catch {
    // Keep the status-specific fallback below.
  }
  const fieldErrors = payload.error?.fields ?? detailFieldErrors(payload.detail);
  const detailMessage = Array.isArray(payload.detail) ? payload.detail.map((item) => item.msg).filter(Boolean).join("; ") : payload.detail;
  const message = payload.error?.message ?? detailMessage ?? statusMessage(response.status);
  return new ApiError(message, response.status, payload.error?.code, fieldErrors);
}

function detailFieldErrors(detail: { loc?: Array<string | number>; msg?: string }[] | string | undefined) {
  if (!Array.isArray(detail)) return undefined;
  const fields: Record<string, string> = {};
  for (const item of detail) {
    const key = item.loc?.at(-1);
    if (key !== undefined && item.msg) fields[String(key)] = item.msg;
  }
  return Object.keys(fields).length ? fields : undefined;
}

function statusMessage(status: number) {
  if (status === 403) return "Bạn không có quyền thực hiện thao tác này.";
  if (status === 404) return "Không tìm thấy nội dung hoặc nội dung không còn khả dụng.";
  if (status === 409) return "Dữ liệu đã thay đổi ở nơi khác. Hãy tải lại trước khi tiếp tục.";
  if (status === 422) return "Thông tin gửi lên chưa hợp lệ.";
  if (status === 429) return "Bạn thao tác quá nhanh. Vui lòng thử lại sau.";
  return "Đã có lỗi xảy ra. Vui lòng thử lại.";
}

export const get = <T>(path: string, options?: RequestOptions) => apiRequest<T>(path, { ...options, method: "GET" });
export const post = <T>(path: string, body?: unknown, options?: RequestOptions) => apiRequest<T>(path, { ...options, method: "POST", body: body instanceof FormData ? body : JSON.stringify(body) });

export async function streamPost<TEvent = unknown>(
  path: string,
  body: unknown,
  onEvent: (event: TEvent) => void,
  retried = false,
): Promise<void> {
  const headers = new Headers({ Accept: "text/event-stream", "Content-Type": "application/json" });
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Không thể kết nối đến máy chủ. Vui lòng thử lại.", 0, "network_error");
  }

  if (response.status === 401 && !retried) {
    const refreshed = await refreshAccessToken((refreshToken) =>
      apiRequest<TokenResponse>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
        skipRefresh: true,
      }),
    );
    if (refreshed) return streamPost(path, body, onEvent, true);
    clearSession();
  }
  if (!response.ok) throw await parseApiError(response);

  const reader = response.body?.getReader();
  if (!reader) throw new ApiError("Máy chủ không trả về stream.", 500, "stream_unavailable");
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const data = event.split("\n").find((line) => line.startsWith("data: "))?.slice(6);
      if (data) onEvent(JSON.parse(data) as TEvent);
    }
    if (done) break;
  }
  if (buffer.trim()) {
    const data = buffer.split("\n").find((line) => line.startsWith("data: "))?.slice(6);
    if (data) onEvent(JSON.parse(data) as TEvent);
  }
}

export const patch = <T>(path: string, body?: unknown, options?: RequestOptions) => apiRequest<T>(path, { ...options, method: "PATCH", body: JSON.stringify(body) });
export const del = <T>(path: string, options?: RequestOptions) => apiRequest<T>(path, { ...options, method: "DELETE" });

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
