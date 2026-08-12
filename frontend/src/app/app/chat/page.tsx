"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, Bot, Check, HelpCircle, Info, Paperclip, Send, Sparkles, Ticket, WandSparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, IconButton, PageHeader } from "@/components/ui";
import { sendChat, uploadAttachment, validateAttachment, type ChatInput } from "@/lib/data";
import { useConversationById } from "@/features/tickets/queries";
import { useResidentProfile } from "@/features/resident/queries";
import { USE_MOCKS } from "@/lib/api-client";
import { demoConversation } from "@/lib/mock-data";
import type { ChatResponse, ConversationMessage } from "@/types";
import { fromNow } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";

function localId(prefix: string) { return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`; }
function messageFromChat(response: ChatResponse): ConversationMessage { return { id: localId("message"), role: "assistant", author_id: null, content: response.response, intent: null, citations: response.citations ?? [], action_payload: response.action?.payload ?? null, attachment_ids: [], created_at: new Date().toISOString(), conversation_version: null }; }

export default function ChatPage() {
  const router = useRouter();
  const profile = useResidentProfile();
  const [conversationId, setConversationId] = useState<string>();
  const conversation = useConversationById(conversationId);
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [messages, setMessages] = useState<ConversationMessage[]>(USE_MOCKS ? demoConversation.messages.filter((message) => message.role !== "management") : []);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [action, setAction] = useState<ChatResponse["action"]>(null);
  const [createdTicket, setCreatedTicket] = useState<ChatResponse["ticket"]>(null);
  const [actionIdempotencyKey, setActionIdempotencyKey] = useState<string>();
  const showToast = useUiStore((state) => state.showToast);

  useEffect(() => { const params = new URLSearchParams(window.location.search); setConversationId(params.get("conversation_id") ?? undefined); }, []);
  useEffect(() => { if (!selectedUnitId && profile.data?.units[0]) setSelectedUnitId(profile.data.units[0].id); }, [profile.data?.units, selectedUnitId]);
  useEffect(() => { if (conversation.data) setMessages(conversation.data.messages); }, [conversation.data]);

  async function submit(message = draft, confirmAction = false, actionPayload?: Record<string, unknown>) {
    if (!message.trim() || pending) return;
    if (!selectedUnitId) return showToast({ tone: "error", message: "Hồ sơ chưa có unit hợp lệ để gửi chat." });
    const userMessage: ConversationMessage = { id: localId("message"), role: "user", author_id: profile.data?.id ?? null, content: message, citations: [], action_payload: null, attachment_ids: attachmentIds, created_at: new Date().toISOString() };
    setMessages((current) => [...current, userMessage]); setDraft(""); setPending(true);
    const input: ChatInput = { message, conversation_id: conversationId, unit_id: selectedUnitId, ticket_id: typeof actionPayload?.ticket_id === "string" ? actionPayload.ticket_id : undefined, confirm_action: confirmAction, idempotency_key: confirmAction ? actionIdempotencyKey : undefined, attachment_ids: attachmentIds.length ? attachmentIds : undefined };
    try {
      const result = await sendChat(input);
      if (result.conversation_id && result.conversation_id !== conversationId) { setConversationId(result.conversation_id); router.replace(`/app/chat?conversation_id=${encodeURIComponent(result.conversation_id)}`); }
      setMessages((current) => [...current, messageFromChat(result)]);
      if (result.action && !confirmAction) { setAction(result.action); setActionIdempotencyKey((current) => current ?? (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : localId("action"))); } else { setAction(null); setActionIdempotencyKey(undefined); }
      setAttachmentIds([]);
      if (result.ticket) { setCreatedTicket(result.ticket); showToast({ tone: "success", message: `Ticket ${result.ticket.ticket_code} đã được tạo.` }); }
    } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi tin nhắn, vui lòng thử lại." }); }
    finally { setPending(false); }
  }
  function confirmTicket() { const payload = action?.payload ?? {}; void submit(String(payload.description ?? "Tôi cần hỗ trợ từ ban quản lý."), true, payload); }
  async function handleAttachment(file: File) { const invalid = validateAttachment(file); if (invalid) return showToast({ tone: "error", message: invalid }); setUploading(true); try { const uploaded = await uploadAttachment(file); setAttachmentIds((current) => [...current, uploaded.id]); showToast({ tone: "success", message: "File đã sẵn sàng đính kèm." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Upload file thất bại." }); } finally { setUploading(false); } }

  return <AppShell><PageHeader eyebrow="Resident space / Chat" title="Hỏi chatbot" description="Tra cứu handbook, quy định và tiện ích. Nếu cần xử lý vận hành, chatbot sẽ giúp bạn tạo ticket." actions={<Link href="/app/tickets/new"><Button variant="outline"><Ticket size={16} /> Tạo ticket trực tiếp</Button></Link>} /><div className="chat-layout"><aside className="chat-sidebar"><Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Trợ lý OnBxrd</h3><p>Handbook Q&A</p></div><Bot size={19} color="#087f77" /></div><label className="field-label" htmlFor="chat-unit">Unit gửi yêu cầu</label><select id="chat-unit" className="select" value={selectedUnitId} onChange={(event) => setSelectedUnitId(event.target.value)} disabled={profile.isLoading || pending}><option value="">Chọn unit</option>{profile.data?.units.map((unit) => <option value={unit.id} key={unit.id}>{unit.unit_number} · Tòa {unit.building}</option>)}</select><div className="suggestion-list"><button className="suggestion" onClick={() => void submit("Quy định sử dụng phòng gym là gì?")}>Quy định sử dụng phòng gym?</button><button className="suggestion" onClick={() => void submit("Tôi muốn báo một sự cố")}>Tôi muốn báo một sự cố</button><button className="suggestion" onClick={() => void submit("Giờ yên tĩnh của tòa nhà là khi nào?")}>Giờ yên tĩnh của tòa nhà?</button></div></Card><Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Nguyên tắc phản hồi</h3></div><Info size={17} color="#087f77" /></div><p style={{ color: "var(--muted)", fontSize: 11, lineHeight: 1.55 }}>Câu trả lời luôn kèm nguồn handbook khi có. Chatbot không tự tạo ticket nếu bạn chưa xác nhận.</p></Card><Card className="chat-sidebar-card"><div className="section-heading"><div><h3>Knowledge base</h3><p>Thông tin từ backend</p></div><BookOpen size={18} color="#7754b8" /></div><Badge tone="success"><Check size={12} /> Đang hoạt động</Badge></Card></aside><section className="chat-window"><header className="chat-header"><div className="chat-header-title"><div className="bot-avatar"><Bot size={18} /></div><div><strong>OnBxrd Assistant</strong><span>Handbook & resident support · {conversationId ? "conversation đang mở" : "conversation mới"}</span></div></div><IconButton label="Thông tin chatbot"><HelpCircle size={18} /></IconButton></header><div className="chat-messages">{conversation.isError && <div className="error-state">Không thể tải conversation này. Vui lòng kiểm tra quyền truy cập hoặc thử lại.</div>}{messages.length === 0 && !conversation.isError && <div className="chat-empty"><div className="bot-avatar"><WandSparkles size={19} /></div><h2>Bạn muốn biết điều gì?</h2><p>Hỏi về nội quy, giờ mở cửa tiện ích hoặc mô tả sự cố trong căn hộ.</p></div>}{messages.map((message) => <ChatMessage key={message.id} message={message} />)}{pending && <div className="message"><div className="bot-avatar" style={{ width: 27, height: 27 }}><Bot size={14} /></div><div className="typing"><span /><span /><span /></div></div>}{createdTicket && <div className="action-card"><strong>Ticket {createdTicket.ticket_code} đã được tạo</strong><p>Ticket đã được lưu bởi backend.</p><Link href={`/app/tickets/${createdTicket.id}`}><Button size="sm">Mở ticket</Button></Link></div>}{action && <div className="action-card"><strong><Sparkles size={14} style={{ verticalAlign: "-2px" }} /> Mình đã chuẩn bị thông tin tạo ticket</strong><p>{String(action.payload?.title ?? "Yêu cầu hỗ trợ")} · {String(action.payload?.location ?? "—")}</p><div className="action-actions"><Button size="sm" onClick={confirmTicket} disabled={pending}>Xác nhận tạo ticket</Button><Button size="sm" variant="outline" onClick={() => { setAction(null); setActionIdempotencyKey(undefined); }}>Chỉnh sửa thông tin</Button></div></div>}</div><form className="composer" onSubmit={(event) => { event.preventDefault(); void submit(); }}><label className="icon-button" aria-label="Đính kèm file"><Paperclip size={18} /><input type="file" hidden accept="image/*,.pdf,.doc,.docx" disabled={uploading || pending} onChange={(event) => { const file = event.target.files?.[0]; if (file) void handleAttachment(file); event.currentTarget.value = ""; }} /></label><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Viết câu hỏi hoặc mô tả sự cố…" rows={1} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); } }} /><Button aria-label="Gửi tin nhắn" type="submit" disabled={pending || uploading || !draft.trim() || !selectedUnitId}><Send size={16} /> <span className="desktop-only">{uploading ? "Đang upload…" : "Gửi"}</span></Button></form>{attachmentIds.length > 0 && <div className="composer-attachments">{attachmentIds.length} file sẽ được gửi cùng tin nhắn</div>}</section></div></AppShell>;
}

function ChatMessage({ message }: { message: ConversationMessage }) { const isUser = message.role === "user"; const isSystem = message.role === "system"; return <div className={`message message-${message.role}`}>{!isUser && !isSystem && <div className="bot-avatar" style={{ width: 27, height: 27, flex: "0 0 auto" }}><Bot size={14} /></div>}<div><div className="message-bubble">{message.content}{message.citations?.length > 0 && <div className="citation-list">{message.citations.map((citation, index) => <span className="citation" key={`${citation.title}-${index}`}><BookOpen size={12} />{citation.title}{citation.section ? ` · ${citation.section}` : ""}{citation.page ? ` · tr. ${citation.page}` : ""}</span>)}</div>}</div><div className="message-meta">{isUser ? "Bạn" : isSystem ? "Hệ thống" : "OnBxrd Assistant"} · {fromNow(message.created_at)}</div></div></div>; }
