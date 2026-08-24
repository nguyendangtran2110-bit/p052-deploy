"use client";

import Link from "next/link";
import { ArrowLeft, Bot, CalendarClock, ChevronRight, Download, FileText, MessageCircle, Paperclip, Send, UploadCloud, UserRound, XCircle } from "lucide-react";
import { useState } from "react";
import { useParams } from "next/navigation";
import { Badge, Button, Card, Divider, IconButton, PageHeader } from "@/components/ui";
import { fromNow, formatDate, formatFileSize, label } from "@/lib/format";
import { downloadAttachment, updateTicketStatus, uploadAttachment, validateAttachment } from "@/lib/data";
import { useConversation, useSendTicketMessage, useTicket } from "@/features/tickets/queries";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useUiStore } from "@/stores/ui-store";

export default function TicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const ticket = useTicket(ticketId);
  const conversation = useConversation(ticketId);
  const send = useSendTicketMessage(ticketId);
  const queryClient = useQueryClient();
  const cancel = useMutation({ mutationFn: () => updateTicketStatus(ticketId, "cancelled", "Resident cancelled ticket"), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ticket", ticketId], exact: true }) });
  const showToast = useUiStore((state) => state.showToast);
  const [draft, setDraft] = useState("");
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const current = conversation.data?.ticket ?? ticket.data;

  if (ticket.isError || conversation.isError) return <div className="error-state">Không thể tải ticket hoặc conversation. Vui lòng thử lại.</div>;
  if (!current) return <div className="empty-state"><FileText size={25} /><h3>Đang tải ticket…</h3></div>;
  const active = current;

  async function submitMessage() {
    if (!draft.trim() || send.isPending) return;
    try {
      await send.mutateAsync({ message: draft, conversation_id: active.conversation_id, unit_id: active.unit_id, attachment_ids: attachmentIds });
      setDraft("");
      setAttachmentIds([]);
      showToast({ tone: "success", message: "Tin nhắn đã được gửi." });
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi tin nhắn." });
    }
  }

  async function handleAttachment(file: File) {
    const invalid = validateAttachment(file);
    if (invalid) { showToast({ tone: "error", message: invalid }); return; }
    setUploading(true);
    try {
      const uploaded = await uploadAttachment(file, { ticket_id: active.id });
      setAttachmentIds((items) => [...items, uploaded.id]);
      showToast({ tone: "success", message: "File đã sẵn sàng đính kèm." });
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Upload file thất bại." });
    } finally {
      setUploading(false);
    }
  }

  async function download(fileId: string) {
    try {
      const file = await downloadAttachment(fileId);
      window.open(file.download_url, "_blank", "noopener,noreferrer");
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tải file." });
    }
  }

  async function cancelTicket() {
    if (!window.confirm("Bạn có chắc muốn hủy ticket này không?")) return;
    try { await cancel.mutateAsync(); showToast({ tone: "success", message: "Ticket đã được hủy." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể hủy ticket." }); }
  }

  return <><PageHeader eyebrow={`Tickets / ${current.ticket_code}`} title={current.title} description={`${current.ticket_code} · Cập nhật ${fromNow(current.updated_at)}`} actions={<Link href="/app/tickets"><Button variant="ghost"><ArrowLeft size={16} /> Tất cả tickets</Button></Link>} /><div className="detail-layout"><div className="detail-main"><Card><div className="detail-header"><div><div className="detail-title"><h2>{current.ticket_code}</h2><Badge tone={current.status === "resolved" ? "success" : current.status === "in_progress" ? "warning" : "info"}>{label(current.status)}</Badge><Badge tone={current.priority === "urgent" || current.priority === "high" ? "danger" : "neutral"}>{label(current.priority)}</Badge></div><p className="detail-subtitle">{current.description}</p></div><div className="detail-actions">{current.status === "submitted" && <Button variant="danger" size="sm" onClick={() => void cancelTicket()}><XCircle size={14} /> Hủy ticket</Button>}</div></div><Divider /><div className="info-grid" style={{ marginTop: 20 }}><div className="info-item"><span>Nhóm sự cố</span><strong>{current.category}</strong></div><div className="info-item"><span>Nguồn tạo</span><strong>{label(current.source)}</strong></div><div className="info-item"><span>Vị trí</span><strong>{current.location}</strong></div><div className="info-item"><span>Ngày gửi</span><strong>{formatDate(current.submitted_at)}</strong></div></div></Card><Card><div className="section-heading"><div><h2>Lịch sử trạng thái</h2><p>Mọi thay đổi được ghi nhận trong ticket</p></div><CalendarClock size={18} color="var(--primary)" /></div><div className="timeline">{current.events.map((event) => <div className="timeline-item" key={event.id}><div className="timeline-dot" /><div className="timeline-copy"><strong>{label(event.event_type)}</strong><span>{event.comment ?? "Cập nhật trạng thái ticket"}</span><small>{formatDate(event.created_at)}</small></div></div>)}</div></Card><Card padding={false}><div className="chat-header"><div className="chat-header-title"><div className="bot-avatar"><MessageCircle size={17} /></div><div><strong>Conversation của ticket</strong><span>{current.handoff_status === "management_active" ? "Ban quản lý đang xử lý" : "Chatbot sẽ hỗ trợ bước tiếp theo"}</span></div></div><Badge tone={current.handoff_status === "management_active" ? "warning" : "success"}>{label(current.handoff_status)}</Badge></div><div className="chat-messages" style={{ minHeight: 300, maxHeight: 460 }}>{conversation.data?.messages.map((message) => <div className={`message message-${message.role}`} key={message.id}>{message.role !== "user" && message.role !== "system" && <div className="bot-avatar" style={{ width: 27, height: 27, flex: "0 0 auto" }}>{message.role === "management" ? <UserRound size={14} /> : <Bot size={14} />}</div>}<div><div className="message-bubble">{message.content}{message.attachment_ids?.length > 0 && <div className="citation-list">{message.attachment_ids.map((id) => <button className="citation" key={id} type="button" onClick={() => void download(id)}>Tải attachment {id}</button>)}</div>}</div><div className="message-meta">{message.role === "user" ? "Bạn" : message.role === "management" ? "Ban quản lý" : "Hệ thống"} · {fromNow(message.created_at)}</div></div></div>)}{conversation.data && !conversation.data.messages.length && <div className="empty-state"><MessageCircle size={22} /><h3>Chưa có trao đổi</h3><p>Gửi tin nhắn để bổ sung thông tin.</p></div>}</div><form className="composer" onSubmit={(event) => { event.preventDefault(); void submitMessage(); }}><label className="icon-button" aria-label="Đính kèm"><Paperclip size={17} /><input type="file" hidden accept="image/*,.pdf,.doc,.docx" disabled={uploading || send.isPending} onChange={(event) => { const file = event.target.files?.[0]; if (file) void handleAttachment(file); event.currentTarget.value = ""; }} /></label><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={current.handoff_status === "management_active" ? "Gửi tin nhắn cho ban quản lý…" : "Bổ sung thông tin cho chatbot…"} rows={1} /><Button type="submit" disabled={!draft.trim() || send.isPending || uploading}><Send size={15} /> Gửi</Button></form>{attachmentIds.length > 0 && <div className="composer-attachments">{attachmentIds.length} file sẽ được gửi cùng tin nhắn</div>}</Card></div><aside className="detail-aside"><Card><div className="section-heading"><div><h3>Handoff</h3><p>Trạng thái người đang xử lý</p></div><MessageCircle size={18} color="var(--primary)" /></div><Badge tone={current.handoff_status === "management_active" ? "warning" : current.handoff_status === "waiting_management" ? "purple" : "success"}>{label(current.handoff_status)}</Badge><div className="activity-item" style={{ marginTop: 14 }}><div className="activity-icon">{current.handoff_status === "management_active" ? <UserRound size={14} /> : <Bot size={14} />}</div><div className="activity-copy"><strong>{current.handoff_status === "management_active" ? "Ban quản lý" : "OnBxrd Assistant"}</strong><span>{current.handoff_status === "management_active" ? "Bạn có thể tiếp tục nhắn trong thread này." : "Tin nhắn tiếp theo sẽ được chatbot tiếp nhận."}</span></div></div></Card><Card><div className="section-heading"><div><h3>Tệp đính kèm</h3><p>{current.attachments.length} file</p></div><Paperclip size={17} color="var(--primary)" /></div>{current.attachments.length ? current.attachments.map((file) => <div className="file-row" key={file.id}><div className="file-icon"><FileText size={14} /></div><div className="file-copy"><strong>{file.filename}</strong><span>{formatFileSize(file.size_bytes)}</span></div><IconButton label={`Tải ${file.filename}`} onClick={() => void download(file.id)}><Download size={15} /></IconButton></div>) : <p style={{ color: "var(--muted)", fontSize: 11 }}>Chưa có file đính kèm.</p>}<label className="upload-zone compact-upload"><UploadCloud size={18} /><span>Upload file cho ticket</span><input type="file" hidden accept="image/*,.pdf,.doc,.docx" onChange={(event) => { const file = event.target.files?.[0]; if (file) void handleAttachment(file); event.currentTarget.value = ""; }} /></label></Card><Card><div className="section-heading"><div><h3>Đơn vị</h3><p>Thông tin ticket</p></div><ChevronRight size={16} color="var(--muted)" /></div><div className="info-item"><span>Unit ID</span><strong>{current.unit_id}</strong></div></Card></aside></div></>;
}
