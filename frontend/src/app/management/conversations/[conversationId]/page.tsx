"use client";

import Link from "next/link";
import { ArrowLeft, Bot, Download, Headphones, MessageCircle, Paperclip, Send, UserRound } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, EmptyState, PageHeader } from "@/components/ui";
import { useManagementConversationActions } from "@/features/tickets/queries";
import { downloadAttachment, fetchManagementConversation, uploadAttachment, validateAttachment } from "@/lib/data";
import { fromNow } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";

export default function ManagementConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const conversation = useQuery({ queryKey: ["conversation", conversationId], queryFn: () => fetchManagementConversation(conversationId), enabled: Boolean(conversationId) });
  const actions = useManagementConversationActions("", conversation.data?.conversation_id);
  const showToast = useUiStore((state) => state.showToast);
  const [draft, setDraft] = useState("");
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  if (conversation.isError) return <AppShell><div className="error-state">Không thể tải conversation. Vui lòng kiểm tra quyền truy cập.</div></AppShell>;
  if (!conversation.data) return <AppShell><EmptyState icon={<Headphones size={24} />} title="Đang tải conversation…" description="Đang lấy dữ liệu mới nhất từ backend." /></AppShell>;
  const item = conversation.data;

  async function takeOver() { try { await actions.takeover.mutateAsync(item.conversation_version); showToast({ tone: "success", message: "Conversation đã được nhận." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể takeover conversation." }); } }
  async function handback() { try { await actions.handback.mutateAsync({ version: item.conversation_version, note: "Management đã xử lý xong." }); showToast({ tone: "success", message: "Conversation đã handback về bot." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể handback conversation." }); } }
  async function send() { if (!draft.trim() || actions.send.isPending) return; try { await actions.send.mutateAsync({ message: draft, version: item.conversation_version, attachment_ids: attachmentIds }); setDraft(""); setAttachmentIds([]); showToast({ tone: "success", message: "Đã gửi phản hồi." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi phản hồi." }); } }
  async function attach(file: File) { const invalid = validateAttachment(file); if (invalid) return showToast({ tone: "error", message: invalid }); setUploading(true); try { const uploaded = await uploadAttachment(file); setAttachmentIds((ids) => [...ids, uploaded.id]); showToast({ tone: "success", message: "File đã sẵn sàng đính kèm." }); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Upload thất bại." }); } finally { setUploading(false); } }
  async function download(id: string) { try { const file = await downloadAttachment(id); window.open(file.download_url, "_blank", "noopener,noreferrer"); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tải file." }); } }

  return <AppShell><PageHeader eyebrow="Management / Conversations" title="General conversation" description={`${item.conversation_id} · version ${item.conversation_version}`} actions={<Link href="/management/conversations"><Button variant="ghost"><ArrowLeft size={16} /> Handoff queue</Button></Link>} /><Card padding={false}><div className="chat-header"><div className="chat-header-title"><div className="bot-avatar"><MessageCircle size={17} /></div><div><strong>Conversation thread</strong><span>{item.unit_id ? `Unit ${item.unit_id}` : "Không gắn unit"} · {item.handoff_status}</span></div></div><div className="detail-actions">{item.handoff_status === "waiting_management" && <Button size="sm" onClick={() => void takeOver()} disabled={actions.takeover.isPending}><Headphones size={14} /> Take over</Button>}{item.handoff_status === "management_active" && <Button size="sm" variant="outline" onClick={() => void handback()} disabled={actions.handback.isPending}>Handback bot</Button>}</div></div><div className="chat-messages" style={{ minHeight: 420 }}>{item.messages.map((message) => <div className={`message message-${message.role}`} key={message.id}>{message.role === "management" ? <div className="bot-avatar" style={{ width: 27, height: 27 }}><UserRound size={14} /></div> : message.role === "assistant" ? <div className="bot-avatar" style={{ width: 27, height: 27 }}><Bot size={14} /></div> : null}<div><div className="message-bubble">{message.content}{message.attachment_ids?.length > 0 && <div className="citation-list">{message.attachment_ids.map((id) => <button className="citation" type="button" key={id} onClick={() => void download(id)}><Download size={12} /> Tải attachment {id}</button>)}</div>}</div><div className="message-meta">{message.role} · {fromNow(message.created_at)}</div></div></div>)}</div>{item.handoff_status === "management_active" ? <form className="composer" onSubmit={(event) => { event.preventDefault(); void send(); }}><label className="icon-button" aria-label="Đính kèm"><Paperclip size={17} /><input type="file" hidden accept="image/*,.pdf,.doc,.docx" disabled={uploading || actions.send.isPending} onChange={(event) => { const file = event.target.files?.[0]; if (file) void attach(file); event.currentTarget.value = ""; }} /></label><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Trả lời resident…" rows={1} /><Button type="submit" disabled={!draft.trim() || uploading || actions.send.isPending}><Send size={15} /> Gửi</Button></form> : <div className="empty-state"><p>Take over conversation để bắt đầu phản hồi.</p></div>}{attachmentIds.length > 0 && <div className="composer-attachments">{attachmentIds.length} file sẽ được gửi cùng phản hồi</div>}</Card></AppShell>;
}
