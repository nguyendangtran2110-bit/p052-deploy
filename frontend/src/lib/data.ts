import { del, get, isApiError, patch, post, USE_MOCKS } from "@/lib/api-client";
import {
  demoAccount,
  demoAnnouncements,
  demoConversation,
  demoDashboard,
  demoKnowledge,
  demoManagementAccounts,
  demoManagementAccount,
  demoProfile,
  demoResidents,
  demoTickets,
  demoUnit,
  makeAnnouncement,
} from "@/lib/mock-data";
import type {
  Account,
  AIAction,
  AIWorkflowCancelResponse,
  AIWorkflowConversationResponse,
  AIWorkflowMessage,
  AIWorkflowResponse,
  Announcement,
  AnnouncementScope,
  AttachmentDownloadResponse,
  AttachmentUploadResponse,
  ChatResponse,
  Conversation,
  ConversationAssignmentResponse,
  ConversationHandoffResponse,
  ConversationSummary,
  DashboardMetrics,
  KnowledgeDocument,
  KnowledgeFilters,
  ListResponse,
  ManagementResident,
  ResidentProfile,
  Ticket,
  Unit,
  TokenResponse,
} from "@/types";

type QueryValue = string | number | boolean | undefined | null;

function queryString(filters: Record<string, QueryValue>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  }
  return query.size ? `?${query.toString()}` : "";
}

function mockOr<T>(mockValue: T, request: () => Promise<T>) {
  return USE_MOCKS ? Promise.resolve(mockValue) : request();
}

function createIdempotencyKey() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `idempotency-${Date.now()}`;
}

export function fetchAccount() {
  return mockOr(demoAccount, () => get<Account>("/auth/me"));
}

export function login(email: string, password: string) {
  const isManagement = email.toLowerCase().includes("management") || email.toLowerCase().includes("admin");
  const mockAccount = email.toLowerCase().includes("admin")
    ? demoManagementAccounts.find((item) => item.management_profile?.management_role === "admin") ?? demoManagementAccount
    : isManagement
      ? demoManagementAccount
      : demoAccount;
  return mockOr<TokenResponse>(
    {
      token_type: "bearer",
      access_token: "demo-access-token",
      refresh_token: "demo-refresh-token",
      expires_in: 3600,
      account: mockAccount,
    },
    () => post<TokenResponse>("/auth/login", { email, password }),
  );
}

export function requestRegistration(payload: { resident_code: string; email: string; password: string }) {
  return mockOr({ message: "Mã xác nhận đã được gửi tới email của bạn." }, () => post<{ message: string }>("/auth/register/request", payload));
}

export function resendVerification(email: string) {
  return mockOr({ message: "Nếu thông tin hợp lệ, mã mới đã được gửi." }, () => post<{ message: string }>("/auth/register/resend-code", { email }));
}

export function verifyRegistration(email: string, code: string) {
  return mockOr<TokenResponse>(
    { token_type: "bearer", access_token: "demo-access-token", refresh_token: "demo-refresh-token", expires_in: 3600, account: demoAccount },
    () => post<TokenResponse>("/auth/register/verify-email", { email, code }),
  );
}

export function forgotPassword(email: string) {
  return mockOr({ message: "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu sẽ được gửi." }, () => post<{ message: string }>("/auth/forgot-password", { email }));
}

export function resetPassword(token: string, new_password: string) {
  return mockOr(undefined, () => post<void>("/auth/reset-password", { token, new_password }));
}

export function changePassword(current_password: string, new_password: string) {
  return mockOr(undefined, () => post<void>("/auth/change-password", { current_password, new_password }));
}

export function logoutSession(refresh_token?: string | null) {
  if (USE_MOCKS || !refresh_token) return Promise.resolve(undefined);
  return post<void>("/auth/logout", { refresh_token });
}

export function logoutAll() {
  return mockOr(undefined, () => post<void>("/auth/logout-all"));
}

export function fetchResidentProfile() {
  return mockOr(demoProfile, () => get<ResidentProfile>("/residents/me"));
}

export function fetchTickets(filters: Record<string, QueryValue> = {}) {
  const mock: ListResponse<Ticket> = { items: demoTickets, total: demoTickets.length, offset: 0, limit: 20 };
  return mockOr(mock, () => get<ListResponse<Ticket>>(`/tickets${queryString(filters)}`));
}

export function fetchTicket(ticketId: string) {
  const mock = demoTickets.find((ticket) => ticket.id === ticketId) ?? demoTickets[0];
  return mockOr(mock, () => get<Ticket>(`/tickets/${ticketId}`));
}

export function fetchTicketConversation(ticketId: string) {
  const mock = { ...demoConversation, ticket: demoTickets.find((ticket) => ticket.id === ticketId) ?? demoTickets[0] };
  return mockOr(mock, () => get<Conversation>(`/tickets/${ticketId}/conversation`));
}

export function fetchConversationById(conversationId: string) {
  return mockOr(demoConversation, () => get<Conversation>(`/conversations/${conversationId}`));
}

export function fetchConversation(ticketId: string) {
  return fetchTicketConversation(ticketId);
}

export interface CreateTicketInput {
  unit_id: string;
  category: string;
  priority: string;
  title: string;
  description: string;
  location: string;
  attachment_ids?: string[];
}

export function createTicket(payload: CreateTicketInput, idempotencyKey = createIdempotencyKey()) {
  const mock: Ticket = {
    ...demoTickets[1],
    id: `ticket-${Date.now()}`,
    ticket_code: `TCK-${String(Date.now()).slice(-5)}`,
    unit_id: payload.unit_id,
    category: payload.category,
    priority: payload.priority as Ticket["priority"],
    title: payload.title,
    description: payload.description,
    location: payload.location,
    source: "form",
    status: "submitted",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  return mockOr(mock, () => post<Ticket>("/tickets", payload, { headers: { "Idempotency-Key": idempotencyKey } }));
}

export function sendTicketMessage(ticketId: string, payload: { message: string; conversation_id?: string; unit_id?: string; attachment_ids?: string[] }) {
  const mock: ChatResponse = {
    conversation_id: demoConversation.conversation_id,
    response: "Đã nhận được thông tin bổ sung. Ban quản lý sẽ phản hồi trong conversation này.",
    citations: [],
    action: null,
    ticket: demoTickets[0],
  };
  return mockOr(mock, () => post<ChatResponse>(`/tickets/${ticketId}/messages`, payload));
}

export interface ChatInput {
  message: string;
  conversation_id?: string;
  unit_id?: string;
  ticket_id?: string;
  confirm_action?: boolean;
  workflow_id?: string;
  workflow_version?: number;
  confirmed_action_id?: string;
  idempotency_key?: string;
  attachment_ids?: string[];
}

export function sendChat(payload: ChatInput) {
  const answer = payload.message.toLowerCase().includes("gym")
    ? "Phòng gym mở cửa từ 05:30 đến 22:00 mỗi ngày. Cư dân vui lòng dùng thẻ cư dân và giữ vệ sinh sau khi sử dụng."
    : "Mình có thể giúp bạn tra handbook, quy định tiện ích hoặc ghi nhận vấn đề cần ban quản lý hỗ trợ.";
  const wantsTicket = /ticket|sự cố|hỏng|rò rỉ|sửa chữa/i.test(payload.message);
  const mock: ChatResponse = {
    conversation_id: payload.conversation_id ?? "conversation-general-demo",
    response: payload.confirm_action ? "Ticket đã được tạo và chuyển vào danh sách theo dõi của bạn." : answer,
    citations: wantsTicket ? [] : [{ title: "Handbook cư dân OnBxrd", section: "Sử dụng tiện ích", page: 18 }],
    action: wantsTicket && !payload.confirm_action
      ? { type: "confirm_ticket", payload: { category: "maintenance", priority: "medium", title: "Yêu cầu hỗ trợ từ chatbot", description: payload.message, location: "Căn hộ demo" } }
      : null,
    ticket: payload.confirm_action ? demoTickets[1] : null,
  };
  return mockOr(mock, () => post<ChatResponse>("/chat/messages", payload));
}

export type AIWorkflowMessageInput = Omit<ChatInput, "conversation_id" | "unit_id" | "ticket_id"> & {
  message: string;
};

function normalizeAction(action: ChatResponse["action"] | null | undefined): AIAction | null {
  if (!action?.type || !action.action_id) return null;
  return {
    type: action.type,
    action_id: action.action_id,
    requires_confirmation: Boolean(action.requires_confirmation),
    payload: action.payload ?? {},
    next_action: normalizeAction(action.next_action),
  };
}

function workflowMessageFromResponse(response: ChatResponse): AIWorkflowMessage | null {
  if (response.message) return response.message;
  if (!response.response) return null;
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    author_id: null,
    content: response.response,
    intent: null,
    citations: response.citations ?? [],
    action_payload: response.action?.payload ?? null,
    attachment_ids: [],
    workflow_id: response.workflow_id ?? null,
    workflow_state: response.state ?? null,
    workflow_version: response.workflow_version ?? null,
    created_at: new Date().toISOString(),
  };
}

function normalizeResidentWorkflowResponse(response: ChatResponse): AIWorkflowResponse {
  return {
    conversation_id: response.conversation_id,
    workflow_id: response.workflow_id ?? "",
    workflow_type: response.workflow_type ?? "resident_ticket",
    state: response.state ?? (response.ticket ? "completed" : "collecting"),
    workflow_version: response.workflow_version ?? 0,
    message: workflowMessageFromResponse(response),
    draft: response.draft ?? {},
    missing_fields: response.missing_fields ?? [],
    action: normalizeAction(response.action),
    citations: response.citations ?? [],
    ticket: response.ticket ?? null,
    announcement: response.announcement ?? null,
    error: null,
  };
}

const demoResidentWorkflowId = "00000000-0000-0000-0000-000000000101";
const demoResidentActionId = "00000000-0000-0000-0000-000000000102";
const demoManagerConversationId = "00000000-0000-0000-0000-000000000201";
const demoManagerWorkflowId = "00000000-0000-0000-0000-000000000202";
const demoManagerCreateActionId = "00000000-0000-0000-0000-000000000203";
const demoManagerPublishActionId = "00000000-0000-0000-0000-000000000204";
let demoResidentWorkflowState: AIWorkflowResponse | null = null;

function demoWorkflowMessage(content: string, workflowId: string, state: AIWorkflowResponse["state"], version: number, attachments: string[] = []): AIWorkflowMessage {
  return {
    id: `workflow-message-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    role: "assistant",
    author_id: null,
    content,
    intent: null,
    citations: [],
    action_payload: null,
    attachment_ids: attachments,
    workflow_id: workflowId,
    workflow_state: state,
    workflow_version: version,
    created_at: new Date().toISOString(),
  };
}

function hasResidentTicketIntent(message: string) {
  return /ticket|maintenance|repair|problem|issue|report|broken|leak|sửa|hỏng|sự cố|báo cáo/i.test(message);
}

function mockResidentWorkflow(payload: ChatInput): AIWorkflowResponse {
  const workflowId = payload.workflow_id ?? demoResidentWorkflowId;
  const conversationId = payload.conversation_id ?? "00000000-0000-0000-0000-000000000301";
  const draft = {
    unit_id: payload.unit_id ?? demoUnit.id,
    category: "maintenance",
    priority: "medium" as const,
    title: "Yêu cầu hỗ trợ từ chatbot",
    description: payload.message,
    location: "Cần xác nhận vị trí",
    attachment_ids: payload.attachment_ids ?? [],
  };
  if (!payload.confirm_action && !hasResidentTicketIntent(payload.message)) {
    const version = (payload.workflow_version ?? 0) + 1;
    return {
      conversation_id: conversationId,
      workflow_id: workflowId,
      workflow_type: "resident_ticket",
      state: "collecting",
      workflow_version: version,
      message: demoWorkflowMessage("I can answer handbook questions or help you report a resident issue when you are ready.", workflowId, "collecting", version),
      draft: {},
      missing_fields: [],
      action: null,
      citations: [],
      ticket: null,
      announcement: null,
      error: null,
    };
  }
  if (payload.confirm_action) {
    return {
      conversation_id: conversationId,
      workflow_id: workflowId,
      workflow_type: "resident_ticket",
      state: "completed",
      workflow_version: (payload.workflow_version ?? 0) + 1,
      message: demoWorkflowMessage("Ticket đã được tạo và đã chuyển vào danh sách theo dõi của bạn.", workflowId, "completed", (payload.workflow_version ?? 0) + 1, payload.attachment_ids),
      draft: { ...draft, ticket_id: demoTickets[1].id },
      missing_fields: [],
      action: { type: "completed", action_id: payload.confirmed_action_id ?? demoResidentActionId, requires_confirmation: false, payload: { ticket_id: demoTickets[1].id, ticket_code: demoTickets[1].ticket_code } },
      citations: [],
      ticket: demoTickets[1],
      announcement: null,
      error: null,
    };
  }
  const action: AIAction = {
    type: "create_ticket",
    action_id: demoResidentActionId,
    requires_confirmation: true,
    payload: draft,
    next_action: null,
  };
  return {
    conversation_id: conversationId,
    workflow_id: workflowId,
    workflow_type: "resident_ticket",
    state: "awaiting_confirmation",
    workflow_version: (payload.workflow_version ?? 0) + 1,
    message: demoWorkflowMessage("Mình đã chuẩn bị bản nháp ticket. Bạn kiểm tra thông tin rồi xác nhận để tạo ticket nhé.", workflowId, "awaiting_confirmation", (payload.workflow_version ?? 0) + 1),
    draft,
    missing_fields: [],
    action,
    citations: [],
    ticket: null,
    announcement: null,
    error: null,
  };
}

let demoManagerWorkflow: AIWorkflowConversationResponse = {
  conversation_id: demoManagerConversationId,
  workflow_id: demoManagerWorkflowId,
  workflow_type: "manager_announcement",
  state: "collecting",
  workflow_version: 0,
  messages: [],
  draft: {},
  missing_fields: ["title", "content", "scopes"],
  action: null,
  citations: [],
  ticket: null,
  announcement: null,
  error: null,
};

function hasAnnouncementIntent(message: string) {
  return /announcement|notice|draft|publish|title|content|audience|resident|maintenance|thông báo|bảo trì|cư dân|gửi/i.test(message);
}

function mockManagerAssistantMessage(payload: AIWorkflowMessageInput): AIWorkflowResponse {
  const version = demoManagerWorkflow.workflow_version + 1;
  const isCreateConfirmation = payload.confirm_action && payload.confirmed_action_id === demoManagerCreateActionId;
  const isPublishConfirmation = payload.confirm_action && payload.confirmed_action_id === demoManagerPublishActionId;
  if (isPublishConfirmation) {
    const result: AIWorkflowResponse = {
      ...demoManagerWorkflow,
      state: "published",
      workflow_version: version,
      action: { type: "published", action_id: demoManagerPublishActionId, requires_confirmation: false, payload: { announcement_id: demoAnnouncements[0].id } },
      announcement: { ...demoAnnouncements[0], status: "published" },
      message: demoWorkflowMessage("Announcement đã được publish thành công.", demoManagerWorkflowId, "published", version),
    };
    demoManagerWorkflow = { ...result, messages: [...demoManagerWorkflow.messages, result.message!], action: result.action };
    return result;
  }
  if (!payload.confirm_action && !hasAnnouncementIntent(payload.message)) {
    const result: AIWorkflowResponse = {
      ...demoManagerWorkflow,
      workflow_version: version,
      message: demoWorkflowMessage("Describe the announcement you want to prepare, and I will collect the required details.", demoManagerWorkflowId, demoManagerWorkflow.state, version),
    };
    demoManagerWorkflow = { ...result, messages: [...demoManagerWorkflow.messages, result.message!], action: result.action };
    return result;
  }
  const draft = {
    title: payload.message.length > 8 ? payload.message.slice(0, 80) : "Thông báo mới từ ban quản lý",
    content: payload.message,
    type: "general" as const,
    priority: "normal" as const,
    scopes: [{ scope_type: "all_residents" as const }],
    expires_at: null,
    attachment_ids: payload.attachment_ids ?? [],
  };
  if (isCreateConfirmation) {
    const action: AIAction = { type: "publish_announcement", action_id: demoManagerPublishActionId, requires_confirmation: true, payload: draft, next_action: null };
    const result: AIWorkflowResponse = {
      ...demoManagerWorkflow,
      state: "awaiting_publish_confirmation",
      workflow_version: version,
      draft: { ...draft, announcement_id: demoAnnouncements[0].id },
      missing_fields: [],
      action,
      message: demoWorkflowMessage("Draft announcement đã được tạo. Bạn cần xác nhận riêng trước khi publish.", demoManagerWorkflowId, "awaiting_publish_confirmation", version),
    };
    demoManagerWorkflow = { ...result, messages: [...demoManagerWorkflow.messages, result.message!], action };
    return result;
  }
  const action: AIAction = { type: "create_announcement_draft", action_id: demoManagerCreateActionId, requires_confirmation: true, payload: draft, next_action: null };
  const result: AIWorkflowResponse = {
    ...demoManagerWorkflow,
    state: "awaiting_confirmation",
    workflow_version: version,
    draft,
    missing_fields: [],
    action,
    message: demoWorkflowMessage("Mình đã chuẩn bị bản nháp announcement. Kiểm tra nội dung và xác nhận tạo draft.", demoManagerWorkflowId, "awaiting_confirmation", version),
  };
  demoManagerWorkflow = { ...result, messages: [...demoManagerWorkflow.messages, result.message!], action };
  return result;
}

export function sendResidentAssistantMessage(payload: ChatInput) {
  if (USE_MOCKS) {
    const response = mockResidentWorkflow(payload);
    demoResidentWorkflowState = response;
    return Promise.resolve(response);
  }
  return post<ChatResponse>("/chat/messages", payload).then(normalizeResidentWorkflowResponse);
}

export function createManagerAssistantConversation() {
  if (USE_MOCKS) {
    demoManagerWorkflow = {
      conversation_id: demoManagerConversationId,
      workflow_id: demoManagerWorkflowId,
      workflow_type: "manager_announcement",
      state: "collecting",
      workflow_version: 0,
      messages: [],
      draft: {},
      missing_fields: ["title", "content", "scopes"],
      action: null,
      citations: [],
      ticket: null,
      announcement: null,
      error: null,
    };
    return Promise.resolve(demoManagerWorkflow);
  }
  const mock = { ...demoManagerWorkflow, messages: [] };
  return mockOr(mock, () => post<AIWorkflowConversationResponse>("/management/assistant/conversations", {}));
}

export function fetchManagerAssistantConversation(conversationId: string) {
  return mockOr({ ...demoManagerWorkflow, conversation_id: conversationId }, () => get<AIWorkflowConversationResponse>(`/management/assistant/conversations/${conversationId}`));
}

export function sendManagerAssistantMessage(conversationId: string, payload: AIWorkflowMessageInput) {
  if (USE_MOCKS) return Promise.resolve(mockManagerAssistantMessage(payload));
  return post<AIWorkflowResponse>(`/management/assistant/conversations/${conversationId}/messages`, payload);
}

export function fetchAIWorkflow(workflowId: string) {
  if (USE_MOCKS) {
    return Promise.resolve(demoResidentWorkflowState?.workflow_id === workflowId
      ? demoResidentWorkflowState
      : { conversation_id: demoManagerConversationId, workflow_id: workflowId, workflow_type: "resident_ticket", state: "collecting", workflow_version: 0, message: null, draft: {}, missing_fields: [], action: null, citations: [], ticket: null, announcement: null, error: null } satisfies AIWorkflowResponse);
  }
  return get<AIWorkflowResponse>(`/ai/workflows/${workflowId}`);
}

export function cancelAIWorkflow(workflowId: string) {
  const mock: AIWorkflowCancelResponse = { workflow_id: workflowId, state: "cancelled", workflow_version: demoManagerWorkflow.workflow_version + 1 };
  return mockOr(mock, () => post<AIWorkflowCancelResponse>(`/ai/workflows/${workflowId}/cancel`));
}

export function fetchAnnouncements(filters: Record<string, QueryValue> = {}, management = false) {
  const mock: ListResponse<Announcement> = { items: demoAnnouncements, total: demoAnnouncements.length, offset: 0, limit: 20 };
  return mockOr(mock, () => get<ListResponse<Announcement>>(`${management ? "/management/announcements" : "/announcements"}${queryString(filters)}`));
}

export function fetchAnnouncement(id: string, management = false) {
  const mock = demoAnnouncements.find((announcement) => announcement.id === id) ?? demoAnnouncements[0];
  return mockOr(mock, () => get<Announcement>(`${management ? "/management/announcements" : "/announcements"}/${id}`));
}

export function markAnnouncementRead(id: string) {
  if (USE_MOCKS) {
    const item = demoAnnouncements.find((announcement) => announcement.id === id);
    if (item) item.is_read = true;
    return Promise.resolve({ announcement_id: id, resident_id: demoProfile.id, read_at: new Date().toISOString() });
  }
  return post(`/announcements/${id}/read`);
}

export function fetchUnreadCount() {
  return mockOr(
    { unread_count: demoAnnouncements.filter((item) => !item.is_read).length },
    () => get<{ unread_count: number }>("/announcements/unread-count"),
  );
}

export function fetchDashboard() {
  return mockOr(demoDashboard, () => get<DashboardMetrics>("/management/dashboard"));
}

export function fetchManagementTickets(filters: Record<string, QueryValue> = {}) {
  return fetchTickets(filters);
}

export function fetchHandoffs(filters: Record<string, QueryValue> = {}) {
  const mock: ListResponse<ConversationSummary> = {
    items: [{
      conversation_id: demoConversation.conversation_id,
      resident_id: demoProfile.id,
      unit_id: demoUnit.id,
      status: demoConversation.status,
      handoff_status: demoConversation.handoff_status,
      handoff_requested_at: demoConversation.handoff_requested_at,
      assigned_manager_id: demoConversation.assigned_manager_id,
      conversation_version: demoConversation.conversation_version,
      last_message_at: demoConversation.last_message_at,
      ticket_id: demoTickets[0].id,
      ticket_code: demoTickets[0].ticket_code,
    }],
    total: 1,
    offset: 0,
    limit: 20,
  };
  return mockOr(mock, () => get<ListResponse<ConversationSummary>>(`/management/conversations/handoffs${queryString(filters)}`));
}

export function fetchManagementConversation(conversationId: string) {
  return fetchConversationById(conversationId);
}

export function takeoverConversation(conversationId: string, conversation_version: number) {
  const mock: ConversationHandoffResponse = {
    conversation_id: conversationId,
    handoff_status: "management_active",
    assigned_manager_id: demoManagementAccount.id,
    conversation_version: conversation_version + 1,
    message: null,
  };
  return mockOr(mock, () => post<ConversationHandoffResponse>(`/management/conversations/${conversationId}/takeover`, { conversation_version }));
}

export function handbackConversation(conversationId: string, conversation_version: number, note?: string) {
  const mock: ConversationHandoffResponse = {
    conversation_id: conversationId,
    handoff_status: "bot_active",
    assigned_manager_id: null,
    conversation_version: conversation_version + 1,
    message: null,
  };
  return mockOr(mock, () => post<ConversationHandoffResponse>(`/management/conversations/${conversationId}/handoff-to-bot`, { conversation_version, note }));
}

export function sendManagementMessage(conversationId: string, payload: { message: string; conversation_version: number; attachment_ids?: string[] }) {
  const mock = {
    id: `message-${Date.now()}`,
    role: "management" as const,
    author_id: demoManagementAccount.id,
    content: payload.message,
    citations: [],
    action_payload: null,
    attachment_ids: payload.attachment_ids ?? [],
    created_at: new Date().toISOString(),
    conversation_version: payload.conversation_version + 1,
  };
  return mockOr(mock, () => post(`/management/conversations/${conversationId}/messages`, payload));
}

export function assignTicket(ticketId: string, assignee_account_id: string | null, due_at: string | null = null) {
  const mock = { ...demoTickets[0], id: ticketId, assigned_to_id: assignee_account_id, due_at };
  return mockOr(mock, () => patch<Ticket>(`/management/tickets/${ticketId}/assignment`, { assignee_account_id, due_at }));
}

export function updateTicketStatus(ticketId: string, status: string, comment?: string) {
  const mock = { ...demoTickets[0], id: ticketId, status: status as Ticket["status"], updated_at: new Date().toISOString() };
  return mockOr(mock, () => patch<Ticket>(`/tickets/${ticketId}/status`, { status, comment }));
}

export function fetchResidents(filters: { search?: string; is_active?: boolean; offset?: number; limit?: number } = {}) {
  const mock: ListResponse<ManagementResident> = { items: demoResidents as ManagementResident[], total: demoResidents.length, offset: 0, limit: 20 };
  return mockOr(mock, () => get<ListResponse<ManagementResident>>(`/management/residents${queryString(filters)}`));
}

export function fetchResident(id: string) {
  const mock = demoResidents.find((resident) => resident.id === id) ?? demoResidents[0];
  return mockOr(mock, () => get<ManagementResident>(`/management/residents/${id}`));
}

export function updateResident(id: string, payload: Record<string, unknown>) {
  const mock = { ...(demoResidents.find((resident) => resident.id === id) ?? demoResidents[0]), ...payload } as ManagementResident;
  return mockOr(mock, () => patch<ManagementResident>(`/management/residents/${id}`, payload));
}

export function createResident(payload: Record<string, unknown>) {
  const mock = { ...demoResidents[0], ...payload, id: `resident-${Date.now()}`, account: null } as ManagementResident;
  return mockOr(mock, () => post<ManagementResident>("/residents", payload));
}

export function deleteResidentAccount(residentId: string) {
  return mockOr(undefined, () => del<void>(`/management/residents/${residentId}/account`));
}

export function fetchManagementAccounts(filters: { status?: string; management_role?: string; offset?: number; limit?: number } = {}) {
  const mock: ListResponse<Account> = { items: demoManagementAccounts, total: demoManagementAccounts.length, offset: 0, limit: 20 };
  return mockOr(mock, () => get<ListResponse<Account>>(`/management/accounts${queryString(filters)}`));
}

export function createManagementAccount(payload: Record<string, unknown>) {
  const mock = {
    ...demoManagementAccount,
    id: `account-${Date.now()}`,
    email: String(payload.email ?? "new@onbxrd.local"),
    management_profile: {
      ...demoManagementAccount.management_profile!,
      full_name: String(payload.full_name ?? "Nhân sự mới"),
      employee_code: String(payload.employee_code ?? "NEW-001"),
      management_role: (payload.management_role as "admin" | "manager" | "staff") ?? "manager",
    },
  } as Account;
  return mockOr(mock, () => post<Account>("/management/accounts", payload));
}

export function updateManagementAccount(id: string, payload: Record<string, unknown>) {
  const mock = { ...demoManagementAccount, id, ...payload } as Account;
  return mockOr(mock, () => patch<Account>(`/management/accounts/${id}`, payload));
}

export function deleteManagementAccount(id: string) {
  return mockOr(undefined, () => del<void>(`/management/accounts/${id}`));
}

export interface AnnouncementCreateInput {
  title: string;
  content: string;
  type: string;
  priority: string;
  scopes: Array<Pick<AnnouncementScope, "scope_type" | "project_code" | "building" | "unit_id">>;
  attachment_ids?: string[];
  expires_at?: string | null;
}

export type AnnouncementUpdateInput = Partial<Omit<AnnouncementCreateInput, "scopes">> & {
  version: number;
  scopes?: AnnouncementCreateInput["scopes"];
};

export function createAnnouncement(payload: AnnouncementCreateInput) {
  const created = makeAnnouncement({
    title: payload.title,
    content: payload.content,
    type: payload.type as Announcement["type"],
    priority: payload.priority as Announcement["priority"],
    scopes: payload.scopes.map((scope, index) => ({ ...scope, id: `scope-${Date.now()}-${index}` })),
  });
  return mockOr(created, () => post<Announcement>("/management/announcements", payload));
}

export function updateAnnouncement(id: string, payload: AnnouncementUpdateInput) {
  const current = demoAnnouncements.find((announcement) => announcement.id === id) ?? demoAnnouncements[0];
  const updated = { ...current, ...payload, version: payload.version + 1, updated_at: new Date().toISOString() } as Announcement;
  return mockOr(updated, () => patch<Announcement>(`/management/announcements/${id}`, payload));
}

export function publishAnnouncement(id: string, version: number) {
  const current = demoAnnouncements.find((announcement) => announcement.id === id) ?? demoAnnouncements[0];
  const updated = { ...current, status: "published" as const, published_at: new Date().toISOString(), version: version + 1, updated_at: new Date().toISOString() };
  return mockOr(updated, () => post<Announcement>(`/management/announcements/${id}/publish`, { version }));
}

export function archiveAnnouncement(id: string, version: number) {
  const current = demoAnnouncements.find((announcement) => announcement.id === id) ?? demoAnnouncements[0];
  return mockOr({ ...current, status: "archived" as const, version: version + 1 }, () => post<Announcement>(`/management/announcements/${id}/archive`, { version }));
}

export function deleteAnnouncement(id: string) {
  return mockOr(undefined, () => del<void>(`/management/announcements/${id}`));
}

export function fetchAnnouncementStatistics(id: string) {
  return mockOr(
    { announcement_id: id, eligible_resident_count: 462, read_count: 327, unread_count: 135 },
    () => get<{ announcement_id: string; eligible_resident_count: number; read_count: number; unread_count: number }>(`/management/announcements/${id}/statistics`),
  );
}

export function fetchKnowledge(filters: KnowledgeFilters = {}) {
  const mock: ListResponse<KnowledgeDocument> = { items: demoKnowledge, total: demoKnowledge.length, offset: 0, limit: 20 };
  return mockOr(mock, () => get<ListResponse<KnowledgeDocument>>(`/knowledge/documents${queryString(filters as Record<string, QueryValue>)}`));
}

export function fetchKnowledgeDocument(id: string) {
  const mock = demoKnowledge.find((document) => document.id === id) ?? demoKnowledge[0];
  return mockOr(mock, () => get<KnowledgeDocument>(`/knowledge/documents/${id}`));
}

export function updateKnowledgeStatus(id: string, status: KnowledgeDocument["status"]) {
  const mock = { ...(demoKnowledge.find((document) => document.id === id) ?? demoKnowledge[0]), status, updated_at: new Date().toISOString() };
  return mockOr(mock, () => patch<KnowledgeDocument>(`/knowledge/documents/${id}/status`, { status }));
}

export function uploadKnowledge(file: File, metadata: { title: string; version: string; document_type: string; project_code?: string; building?: string; effective_date?: string }) {
  const form = new FormData();
  form.append("file", file);
  form.append("title", metadata.title);
  form.append("version", metadata.version);
  form.append("document_type", metadata.document_type);
  if (metadata.project_code) form.append("project_code", metadata.project_code);
  if (metadata.building) form.append("building", metadata.building);
  if (metadata.effective_date) form.append("effective_date", metadata.effective_date);
  const mock = { ...demoKnowledge[0], id: `knowledge-${Date.now()}`, title: metadata.title, version: metadata.version, original_filename: file.name, status: "pending" as const, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
  return mockOr(mock, () => post<KnowledgeDocument>("/knowledge/documents", form));
}

export function fetchUnits(filters: { project_code?: string; building?: string; is_active?: boolean; offset?: number; limit?: number } = {}) {
  const mock = [demoUnit, { ...demoUnit, id: "unit-b-0918", building: "B", unit_number: "B-0918" }];
  return mockOr(mock, () => get<Unit[]>(`/units${queryString({ offset: filters.offset, limit: filters.limit })}`));
}

export function createUnit(payload: { project_code: string; building: string; floor?: string | null; unit_number: string; is_active?: boolean }) {
  const mock: Unit = { ...demoUnit, ...payload, id: `unit-${Date.now()}`, is_active: payload.is_active ?? true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
  return mockOr(mock, () => post<Unit>("/units", payload));
}

export function validateAttachment(file: File) {
  const allowed = ["image/", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
  if (!file.size) return "File rỗng không thể upload.";
  if (file.size > 10 * 1024 * 1024) return "File không được lớn hơn 10 MB.";
  if (!allowed.some((mime) => mime.endsWith("/") ? file.type.startsWith(mime) : file.type === mime)) return "Định dạng file chưa được hỗ trợ.";
  return null;
}

export interface AttachmentUploadParent {
  ticket_id?: string;
  announcement_id?: string;
  workflow_id?: string;
}

export async function uploadAttachment(file: File, parent?: AttachmentUploadParent, onProgress?: (progress: number) => void) {
  if (USE_MOCKS) {
    onProgress?.(100);
    return { id: `attachment-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, filename: file.name, mime_type: file.type, size_bytes: file.size, upload_url: "" } satisfies AttachmentUploadResponse;
  }
  const presign = await post<AttachmentUploadResponse>("/attachments/presign", {
    filename: file.name,
    content_type: file.type || "application/octet-stream",
    size_bytes: file.size,
    ticket_id: parent?.ticket_id ?? null,
    announcement_id: parent?.announcement_id ?? null,
    workflow_id: parent?.workflow_id ?? null,
  });
  onProgress?.(8);
  if (onProgress && typeof XMLHttpRequest !== "undefined") {
    await uploadWithProgress(presign.upload_url, file, file.type || "application/octet-stream", onProgress);
  } else {
    const upload = await fetch(presign.upload_url, { method: "PUT", headers: { "Content-Type": file.type || "application/octet-stream" }, body: file });
    if (!upload.ok) throw new Error("Upload file that bai");
  }
  onProgress?.(100);
  return presign;
}

function uploadWithProgress(url: string, file: File, contentType: string, onProgress: (progress: number) => void) {
  return new Promise<void>((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("PUT", url);
    request.setRequestHeader("Content-Type", contentType);
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    };
    request.onload = () => request.status >= 200 && request.status < 300 ? resolve() : reject(new Error("Upload file that bai"));
    request.onerror = () => reject(new Error("Upload file that bai"));
    request.onabort = () => reject(new Error("Upload file da bi huy"));
    request.send(file);
  });
}

export function downloadAttachment(attachmentId: string) {
  const mock: AttachmentDownloadResponse = { id: attachmentId, filename: "attachment", download_url: "#" };
  return mockOr(mock, () => get<AttachmentDownloadResponse>(`/attachments/${attachmentId}/download`));
}

export function isConflict(error: unknown) {
  return isApiError(error) && error.status === 409;
}
