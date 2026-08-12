"use client";

import Link from "next/link";
import { ArrowLeft, Bot, CalendarClock, CheckCircle2, Headphones, MessageCircle, Paperclip, Send, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, Divider, IconButton, Input, PageHeader, Select } from "@/components/ui";
import { useConversation, useManagementConversationActions, useTicket } from "@/features/tickets/queries";
import { useManagementAccounts } from "@/features/management/queries";
import { downloadAttachment, fetchAccount, uploadAttachment, validateAttachment } from "@/lib/data";
import { formatDate, fromNow, label } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";

export default function ManagementTicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const ticket = useTicket(ticketId);
  const conversation = useConversation(ticketId);
  const current = conversation.data?.ticket ?? ticket.data;
  const actions = useManagementConversationActions(ticketId, conversation.data?.conversation_id);
  const auth = useQuery({ queryKey: ["auth", "me"], queryFn: fetchAccount });
  const isAdmin = auth.data?.role === "management" && auth.data.management_profile?.management_role === "admin";
  const accounts = useManagementAccounts({ status: "active" }, isAdmin);
  const showToast = useUiStore((state) => state.showToast);
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState(current?.status ?? "in_progress");
  const [assignee, setAssignee] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (current) {
      setStatus(current.status);
      setAssignee(current.assigned_to_id ?? current.assigned_manager_id ?? auth.data?.id ?? "");
      setDueAt(current.due_at ? current.due_at.slice(0, 16) : "");
    }
  }, [auth.data?.id, current]);

  if (ticket.isError || conversation.isError) return <AppShell><div className="error-state">Không thể tải ticket hoặc conversation. Vui lòng thử lại.</div></AppShell>;
  if (!current || !conversation.data) return <AppShell><div className="empty-state"><Headphones size={24} /><h3>Đang tải conversation…</h3><p>Kiểm tra quyền và tải dữ liệu mới nhất.</p></div></AppShell>;
  const active = current;
  const conv = conversation.data;

  async function takeOver() { try { await actions.takeover.mutateAsync(conv.conversation_version); showToast({ tone: "success", message: "Bạn đã nhận conversation này." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Conversation đã được người khác nhận." }); } }
  async function send() { if (!draft.trim()) return; try { await actions.send.mutateAsync({ message: draft, version: conv.conversation_version, attachment_ids: attachmentIds }); setDraft(""); setAttachmentIds([]); showToast({ tone: "success", message: "Đã gửi phản hồi." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi phản hồi." }); } }
  async function handback() { try { await actions.handback.mutateAsync({ version: conv.conversation_version, note: "Management đã xử lý xong phần cần thiết." }); showToast({ tone: "success", message: "Conversation đã handback về bot." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể handback." }); } }
  async function updateStatus() { try { await actions.status.mutateAsync({ status }); showToast({ tone: "success", message: "Status ticket đã cập nhật." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể cập nhật status." }); } }
  async function saveAssignment() {
    try {
      const due = dueAt ? new Date(dueAt).toISOString() : null;
      await actions.assign.mutateAsync({ assignee: assignee || null, dueAt: due });
      showToast({ tone: "success", message: "Assignment đã cập nhật." });
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể cập nhật assignment." });
    }
  }
  async function handleAttachment(file: File) {
    const invalid = validateAttachment(file);
    if (invalid) { showToast({ tone: "error", message: invalid }); return; }
    setUploading(true);
    try { const uploaded = await uploadAttachment(file, { ticket_id: active.id }); setAttachmentIds((items) => [...items, uploaded.id]); showToast({ tone: "success", message: "File đã sẵn sàng đính kèm." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Upload file thất bại." }); }
    finally { setUploading(false); }
  }
  async function download(id: string) { try { const file = await downloadAttachment(id); window.open(file.download_url, "_blank", "noopener,noreferrer"); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tải file." }); } }

  return <AppShell><PageHeader eyebrow={`Management / Tickets / ${current.ticket_code}`} title={current.title} description={`${current.ticket_code} · cập nhật ${fromNow(current.updated_at)} · conversation version ${conv.conversation_version}`} actions={<Link href="/management/tickets"><Button variant="ghost"><ArrowLeft size={16} /> Ticket queue</Button></Link>} /><div className="detail-layout"><main className="detail-main"><Card><div className="detail-header"><div><div className="detail-title"><h2>{current.ticket_code}</h2><Badge tone={current.status === "resolved" ? "success" : current.status === "in_progress" ? "warning" : "info"}>{label(current.status)}</Badge><Badge tone={current.priority === "urgent" ? "danger" : "warning"}>{label(current.priority)}</Badge></div><p className="detail-subtitle">{current.description}</p></div><div className="detail-actions">{conv.handoff_status === "waiting_management" && <Button size="sm" onClick={() => void takeOver()} disabled={actions.takeover.isPending}><Headphones size={14} /> Take over</Button>}{conv.handoff_status === "management_active" && <Button size="sm" variant="outline" onClick={() => void handback()} disabled={actions.handback.isPending}>Handback bot</Button>}</div></div><Divider /><div className="info-grid" style={{ marginTop: 20 }}><div className="info-item"><span>Resident ID</span><strong>{current.resident_id}</strong></div><div className="info-item"><span>Unit ID</span><strong>{current.unit_id}</strong></div><div className="info-item"><span>Category</span><strong>{current.category}</strong></div><div className="info-item"><span>Created</span><strong>{formatDate(current.created_at)}</strong></div></div></Card><Card padding={false}><div className="chat-header"><div className="chat-header-title"><div className="bot-avatar"><MessageCircle size={17} /></div><div><strong>Conversation thread</strong><span>{label(conv.handoff_status)} · version {conv.conversation_version}</span></div></div><Badge tone={conv.handoff_status === "management_active" ? "warning" : conv.handoff_status === "waiting_management" ? "purple" : "success"}>{label(conv.handoff_status)}</Badge></div><div className="chat-messages" style={{ minHeight: 350, maxHeight: 490 }}>{conv.messages.map((message) => <div className={`message message-${message.role}`} key={message.id}>{message.role !== "user" && message.role !== "system" && <div className="bot-avatar" style={{ width: 27, height: 27, flex: "0 0 auto" }}>{message.role === "management" ? <UserRound size={14} /> : <Bot size={14} />}</div>}<div><div className="message-bubble">{message.content}{message.attachment_ids?.length > 0 && <div className="citation-list">{message.attachment_ids.map((id) => <button className="citation" type="button" key={id} onClick={() => void download(id)}>Tải attachment {id}</button>)}</div>}</div><div className="message-meta">{message.role === "user" ? "Resident" : message.role === "management" ? "Management" : "System"} · {fromNow(message.created_at)}</div></div></div>)}</div>{conv.handoff_status === "management_active" ? <form className="composer" onSubmit={(event) => { event.preventDefault(); void send(); }}><label className="icon-button" aria-label="Đính kèm"><Paperclip size={17} /><input type="file" hidden accept="image/*,.pdf,.doc,.docx" disabled={uploading || actions.send.isPending} onChange={(event) => { const file = event.target.files?.[0]; if (file) void handleAttachment(file); event.currentTarget.value = ""; }} /></label><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Trả lời resident…" rows={1} /><Button type="submit" disabled={!draft.trim() || actions.send.isPending || uploading}><Send size={15} /> Gửi</Button></form> : <div style={{ padding: 17, color: "#788e91", background: "#f8fbfa", borderTop: "1px solid var(--line)", fontSize: 12, textAlign: "center" }}>Take over conversation để bắt đầu phản hồi resident.</div>}{attachmentIds.length > 0 && <div className="composer-attachments">{attachmentIds.length} file sẽ được gửi cùng phản hồi</div>}</Card></main><aside className="detail-aside"><Card><div className="section-heading"><div><h3>Quick actions</h3><p>Thao tác nghiệp vụ</p></div><Headphones size={18} color="#087f77" /></div><div className="form-grid"><Select label="Ticket status" value={status} onChange={(event) => setStatus(event.target.value as typeof status)}><option value="submitted">Đã gửi</option><option value="approved">Đã duyệt</option><option value="in_progress">Đang xử lý</option><option value="resolved">Đã giải quyết</option><option value="rejected">Từ chối</option><option value="cancelled">Đã hủy</option></Select><Button variant="secondary" onClick={() => void updateStatus()} disabled={actions.status.isPending}><CheckCircle2 size={15} /> Cập nhật status</Button><Select label="Assignee" value={assignee} onChange={(event) => setAssignee(event.target.value)}><option value="">Unassign</option>{auth.data?.role === "management" && <option value={auth.data.id}>Tôi ({auth.data.management_profile?.full_name ?? auth.data.email})</option>}{isAdmin && accounts.data?.items.filter((item) => item.id !== auth.data?.id).map((item) => <option value={item.id} key={item.id}>{item.management_profile?.full_name ?? item.email}</option>)}</Select><Input label="Due at" type="datetime-local" value={dueAt} onChange={(event) => setDueAt(event.target.value)} /><Button variant="outline" onClick={() => void saveAssignment()} disabled={actions.assign.isPending}>Lưu assignment</Button>{!isAdmin && <p className="form-help">Danh sách account khác chỉ hiển thị cho admin; bạn vẫn có thể gán cho chính mình hoặc unassign.</p>}</div></Card><Card><div className="section-heading"><div><h3>Audit timeline</h3><p>Ticket events</p></div><CalendarClock size={17} color="#087f77" /></div><div className="timeline">{current.events.map((event) => <div className="timeline-item" key={event.id}><div className="timeline-dot" /><div className="timeline-copy"><strong>{label(event.event_type)}</strong><span>{event.comment ?? "Operational update"}</span><small>{formatDate(event.created_at)}</small></div></div>)}</div></Card></aside></div></AppShell>;
}
