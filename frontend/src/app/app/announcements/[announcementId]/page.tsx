"use client";

import Link from "next/link";
import { ArrowLeft, Bell, Bot, CalendarDays, Download, FileText, MessageCircle, Paperclip, PlusCircle } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useRef } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, Divider, EmptyState, PageHeader } from "@/components/ui";
import { downloadAttachment } from "@/lib/data";
import { formatDate, formatFileSize, label } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";
import { useAnnouncement, useMarkRead } from "@/features/announcements/queries";

export default function AnnouncementDetailPage() {
  const { announcementId } = useParams<{ announcementId: string }>();
  const announcement = useAnnouncement(announcementId);
  const markRead = useMarkRead();
  const showToast = useUiStore((state) => state.showToast);
  const marked = useRef(false);
  useEffect(() => { if (announcement.data && !announcement.data.is_read && !marked.current) { marked.current = true; markRead.mutate(announcement.data.id); } }, [announcement.data, markRead]);
  if (announcement.isError) return <AppShell><EmptyState icon={<Bell size={22} />} title="Không thể tải thông báo" description="Vui lòng thử lại hoặc kiểm tra quyền truy cập." /></AppShell>;
  if (!announcement.data) return <AppShell><EmptyState icon={<Bell size={22} />} title="Đang tải thông báo…" description="Đang kiểm tra quyền truy cập và nội dung mới nhất." /></AppShell>;
  const item = announcement.data;
  async function download(id: string) { try { const file = await downloadAttachment(id); window.open(file.download_url, "_blank", "noopener,noreferrer"); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tải file." }); } }
  return <AppShell><PageHeader eyebrow={`Announcements / ${item.announcement_code}`} title={item.title} description={`Phát hành ${formatDate(item.published_at)}${item.expires_at ? ` · Hết hạn ${formatDate(item.expires_at)}` : ""}`} actions={<Link href="/app/announcements"><Button variant="ghost"><ArrowLeft size={16} /> Tất cả thông báo</Button></Link>} /><div className="detail-layout"><main className="detail-main"><Card><div className="detail-title"><Badge tone={item.priority === "urgent" ? "danger" : item.priority === "important" ? "warning" : "neutral"}>{label(item.priority)}</Badge><Badge tone="info">{label(item.type)}</Badge></div><div className="announcement-detail-content" style={{ marginTop: 22 }}>{item.content}</div><Divider /><div className="scope-list" style={{ marginTop: 18 }}>{item.scopes.map((scope) => <span className="scope-chip" key={scope.id}>{scope.scope_type === "all_residents" ? "Tất cả cư dân" : scope.scope_type === "unit" ? `Unit ${scope.unit_id}` : scope.building ? `Tòa ${scope.building}` : scope.project_code ?? "Audience được phép"}</span>)}</div></Card>{item.attachments.length > 0 && <Card><div className="section-heading"><div><h2>Tài liệu đính kèm</h2><p>File được lưu trong private storage</p></div><Paperclip size={18} color="#087f77" /></div>{item.attachments.map((file) => <div className="file-row" key={file.id}><div className="file-icon"><FileText size={14} /></div><div className="file-copy"><strong>{file.filename}</strong><span>{formatFileSize(file.size_bytes)}</span></div><Button size="sm" variant="outline" onClick={() => void download(file.id)}><Download size={14} /> Tải xuống</Button></div>)}</Card>}</main><aside className="detail-aside"><Card><div className="section-heading"><div><h3>Muốn hỏi thêm?</h3><p>Tiếp tục từ thông báo này</p></div><MessageCircle size={18} color="#087f77" /></div><div className="form-grid"><Link href="/app/chat"><Button variant="secondary"><Bot size={15} /> Hỏi chatbot</Button></Link><Link href={`/app/tickets/new?subject=${encodeURIComponent(item.title)}`}><Button variant="outline"><PlusCircle size={15} /> Tạo ticket</Button></Link></div></Card><Card><div className="section-heading"><div><h3>Thông tin phát hành</h3></div><CalendarDays size={17} color="#087f77" /></div><div className="info-grid"><div className="info-item"><span>Ngày phát hành</span><strong>{formatDate(item.published_at)}</strong></div><div className="info-item"><span>Trạng thái</span><strong>{label(item.status)}</strong></div><div className="info-item"><span>Mã thông báo</span><strong>{item.announcement_code}</strong></div></div></Card></aside></div></AppShell>;
}
