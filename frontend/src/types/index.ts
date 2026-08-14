export type ActorRole = "resident" | "management";
export type ManagementRole = "admin" | "manager" | "staff";
export type AccountStatus = "active" | "disabled";
export type TicketStatus =
  | "submitted"
  | "approved"
  | "in_progress"
  | "resolved"
  | "rejected"
  | "cancelled";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type TicketSource = "form" | "chat";
export type HandoffStatus = "bot_active" | "waiting_management" | "management_active";
export type MessageRole = "user" | "assistant" | "management" | "system";
export type AnnouncementType =
  | "general"
  | "maintenance"
  | "facility"
  | "regulation_update"
  | "event"
  | "emergency";
export type AnnouncementPriority = "normal" | "important" | "urgent";
export type AnnouncementStatus = "draft" | "published" | "archived";
export type AnnouncementScopeType = "all_residents" | "project" | "building" | "unit";

export interface ManagementProfile {
  employee_code: string;
  full_name: string;
  phone?: string | null;
  department?: string | null;
  job_title?: string | null;
  management_role: ManagementRole;
  project_code?: string | null;
  building?: string | null;
}

export interface Account {
  id: string;
  email: string;
  role: ActorRole;
  status: AccountStatus;
  resident_id?: string | null;
  last_login_at?: string | null;
  email_verified_at?: string | null;
  created_at: string;
  updated_at: string;
  management_profile?: ManagementProfile | null;
}

export interface TokenResponse {
  token_type: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
  account: Account;
}

export interface Unit {
  id: string;
  project_code: string;
  building: string;
  floor?: string | null;
  unit_number: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResidentUnit extends Unit {
  resident_role: "owner" | "tenant" | "family";
  is_primary: boolean;
}

export interface ResidentProfile {
  id: string;
  resident_code: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  units: ResidentUnit[];
}

export interface TicketAttachment {
  id: string;
  filename: string;
  mime_type?: string | null;
  size_bytes: number;
  created_at: string;
}

export interface TicketEvent {
  id: string;
  event_type: string;
  actor_type: string;
  actor_id?: string | null;
  from_status?: string | null;
  to_status?: string | null;
  comment?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface Ticket {
  id: string;
  ticket_code: string;
  resident_id: string;
  unit_id: string;
  conversation_id: string;
  handoff_status: HandoffStatus;
  assigned_manager_id?: string | null;
  conversation_version: number;
  source: TicketSource;
  status: TicketStatus;
  category: string;
  priority: TicketPriority;
  title: string;
  description: string;
  location: string;
  submitted_at: string;
  approved_at?: string | null;
  resolved_at?: string | null;
  assigned_to_id?: string | null;
  assigned_at?: string | null;
  due_at?: string | null;
  created_at: string;
  updated_at: string;
  events: TicketEvent[];
  attachments: TicketAttachment[];
}

export interface ConversationMessage {
  id: string;
  role: MessageRole;
  author_id?: string | null;
  content: string;
  intent?: string | null;
  citations: Citation[];
  action_payload?: Record<string, unknown> | null;
  attachment_ids: string[];
  created_at: string;
  conversation_version?: number | null;
}

export interface Citation {
  title?: string;
  section?: string;
  page?: string | number;
  source?: string;
}

export interface Conversation {
  conversation_id: string;
  resident_id?: string | null;
  unit_id?: string | null;
  status: "active" | "closed";
  handoff_status: HandoffStatus;
  handoff_requested_at?: string | null;
  assigned_manager_id?: string | null;
  conversation_version: number;
  last_message_at: string;
  ticket?: Ticket | null;
  messages: ConversationMessage[];
}

export interface ConversationSummary {
  conversation_id: string;
  resident_id: string;
  unit_id?: string | null;
  status: "active" | "closed";
  handoff_status: HandoffStatus;
  handoff_requested_at?: string | null;
  assigned_manager_id?: string | null;
  conversation_version: number;
  last_message_at: string;
  ticket_id?: string | null;
  ticket_code?: string | null;
}

export interface ConversationAssignmentResponse {
  conversation_id: string;
  handoff_status: HandoffStatus;
  assigned_manager_id?: string | null;
  conversation_version: number;
  message?: ConversationMessage | null;
}

export interface ConversationHandoffResponse extends ConversationAssignmentResponse {
  handoff_requested_at?: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  citations: Citation[];
  action?: {
    type?: string;
    action_id?: string;
    requires_confirmation?: boolean;
    payload?: Record<string, unknown>;
    next_action?: ChatResponse["action"];
  } | null;
  ticket?: Ticket | null;
  announcement?: Announcement | null;
  workflow_id?: string | null;
  workflow_type?: AIWorkflowType | null;
  state?: AIWorkflowState | null;
  workflow_version?: number | null;
  draft?: Record<string, unknown>;
  missing_fields?: string[];
  message?: AIWorkflowMessage | null;
}

export type AIWorkflowType = "resident_ticket" | "manager_announcement";
export type AIWorkflowState =
  | "collecting"
  | "awaiting_confirmation"
  | "executing"
  | "completed"
  | "cancelled"
  | "failed"
  | "awaiting_publish_confirmation"
  | "publishing"
  | "published";

export type AIActionType =
  | "ask_clarification"
  | "preview_ticket"
  | "create_ticket"
  | "completed"
  | "preview_announcement"
  | "create_announcement_draft"
  | "announcement_draft_created"
  | "update_announcement"
  | "publish_announcement"
  | "published"
  | "cancelled";

export interface AIAction {
  type: AIActionType | string;
  action_id: string;
  requires_confirmation: boolean;
  payload: Record<string, unknown>;
  next_action?: AIAction | null;
}

export interface TicketWorkflowDraft {
  unit_id?: string | null;
  category?: string | null;
  priority?: TicketPriority | null;
  title?: string | null;
  description?: string | null;
  location?: string | null;
  attachment_ids?: string[];
  ticket_id?: string | null;
}

export interface AnnouncementWorkflowScope {
  scope_type: AnnouncementScopeType;
  project_code?: string | null;
  building?: string | null;
  unit_id?: string | null;
}

export interface AnnouncementWorkflowDraft {
  title?: string | null;
  content?: string | null;
  type?: AnnouncementType | null;
  priority?: AnnouncementPriority | null;
  scopes?: AnnouncementWorkflowScope[];
  expires_at?: string | null;
  attachment_ids?: string[];
  announcement_id?: string | null;
}

export type AIWorkflowDraft = TicketWorkflowDraft | AnnouncementWorkflowDraft;

export interface AIWorkflowMessage {
  id: string;
  role: MessageRole;
  author_id?: string | null;
  content: string;
  intent?: string | null;
  citations: Citation[];
  action_payload?: Record<string, unknown> | null;
  attachment_ids: string[];
  workflow_id?: string | null;
  workflow_state?: AIWorkflowState | null;
  workflow_version?: number | null;
  created_at: string;
}

export interface AIWorkflowResponse {
  conversation_id: string;
  workflow_id: string;
  workflow_type: AIWorkflowType;
  state: AIWorkflowState;
  workflow_version: number;
  message?: AIWorkflowMessage | null;
  draft: AIWorkflowDraft;
  missing_fields: string[];
  action?: AIAction | null;
  citations: Citation[];
  ticket?: Ticket | null;
  announcement?: Announcement | null;
  error?: Record<string, unknown> | null;
}

export interface AIWorkflowConversationResponse extends Omit<AIWorkflowResponse, "message"> {
  messages: AIWorkflowMessage[];
}

export interface AIWorkflowCancelResponse {
  workflow_id: string;
  state: AIWorkflowState;
  workflow_version: number;
}

export interface AttachmentUploadResponse {
  id: string;
  filename: string;
  mime_type?: string | null;
  size_bytes: number;
  object_key?: string;
  upload_url: string;
  expires_in?: number;
  created_at?: string;
}

export interface AttachmentDownloadResponse {
  id: string;
  filename: string;
  download_url: string;
  expires_in?: number;
}

export interface AnnouncementScope {
  id: string;
  scope_type: AnnouncementScopeType;
  project_code?: string | null;
  building?: string | null;
  unit_id?: string | null;
}

export interface AnnouncementAttachment {
  id: string;
  filename: string;
  mime_type?: string | null;
  size_bytes: number;
  created_at: string;
}

export interface AnnouncementEvent {
  id: string;
  event_type: string;
  actor_type: string;
  actor_id?: string | null;
  from_status?: AnnouncementStatus | null;
  to_status?: AnnouncementStatus | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface Announcement {
  id: string;
  announcement_code: string;
  title: string;
  content: string;
  type: AnnouncementType;
  priority: AnnouncementPriority;
  status: AnnouncementStatus;
  author_id?: string | null;
  published_at?: string | null;
  expires_at?: string | null;
  version: number;
  is_read: boolean;
  scopes: AnnouncementScope[];
  attachments: AnnouncementAttachment[];
  events: AnnouncementEvent[];
  created_at: string;
  updated_at: string;
}

export interface DashboardMetrics {
  ticket_total: number;
  ticket_status_counts: Record<string, number>;
  ticket_priority_counts: Record<string, number>;
  unassigned_tickets: number;
  overdue_tickets: number;
  active_residents: number;
  active_units: number;
  active_management_accounts: number;
  knowledge_documents_requiring_attention: number;
}

export interface ManagementResident extends ResidentProfile {
  account?: Account | null;
}

export interface KnowledgeFilters {
  status?: string;
  document_type?: string;
  project_code?: string;
  building?: string;
  offset?: number;
  limit?: number;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  document_type: string;
  version: string;
  project_code?: string | null;
  building?: string | null;
  original_filename: string;
  mime_type?: string | null;
  checksum_sha256: string;
  status: "pending" | "indexing" | "indexed" | "failed" | "archived";
  effective_date?: string | null;
  document_metadata: Record<string, unknown>;
  error_message?: string | null;
  indexed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
