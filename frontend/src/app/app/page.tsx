"use client";

import Link from "next/link";
import { ArrowRight, Bell, Bot, CheckCircle2, ChevronRight, FilePlus2, Home, Megaphone, MessageCircle, Sparkles, Ticket, Wrench } from "lucide-react";
import { Badge, Button, Card, PageHeader, ProgressBar } from "@/components/ui";
import { fromNow, label } from "@/lib/format";
import { useResidentProfile } from "@/features/resident/queries";
import { useTickets } from "@/features/tickets/queries";
import { useAnnouncements, useUnreadCount } from "@/features/announcements/queries";

export default function ResidentHomePage() {
  const profile = useResidentProfile();
  const tickets = useTickets({ limit: 4 });
  const unread = useUnreadCount();
  const announcements = useAnnouncements({ limit: 2 });
  const name = profile.data?.full_name?.split(" ").slice(-1)[0] ?? "bạn";
  const primaryUnit = profile.data?.units.find((unit) => unit.is_primary) ?? profile.data?.units[0];
  const openTickets = tickets.data?.items.filter((ticket) => !["resolved", "rejected", "cancelled"].includes(ticket.status)) ?? [];
  const recentAnnouncements = announcements.data?.items.slice(0, 2) ?? [];

  return <div className="dashboard-grid">
    <PageHeader eyebrow="Resident space" title={`Chào ${name}, hôm nay bạn cần gì?`} description="Theo dõi yêu cầu, hỏi nhanh handbook và nhận thông báo mới từ ban quản lý." actions={<><Link href="/app/chat"><Button><Bot size={17} /> Hỏi chatbot</Button></Link><Link href="/app/tickets/new"><Button variant="outline"><FilePlus2 size={17} /> Tạo ticket</Button></Link></>} />
    <section className="card welcome-panel"><div><div className="welcome-meta"><Home size={14} /> {primaryUnit?.unit_number ?? "Chưa có unit"}{primaryUnit ? ` · Tòa ${primaryUnit.building}` : ""}</div><h1>Không gian sống của bạn</h1><p>Chatbot có thể tra cứu quy định, tiện ích và giúp ghi nhận sự cố mà không cần gọi điện.</p></div><div className="welcome-actions"><Link href="/app/chat"><Button variant="primary">Bắt đầu trò chuyện <ArrowRight size={16} /></Button></Link><Link href="/app/announcements"><Button variant="outline">{unread.data?.unread_count ?? 0} thông báo mới</Button></Link></div></section>
    <div className="quick-actions"><Link href="/app/chat" className="quick-action"><MessageCircle size={20} /><span>Hỏi chatbot <ChevronRight size={14} /></span></Link><Link href="/app/tickets/new" className="quick-action"><FilePlus2 size={20} /><span>Tạo ticket <ChevronRight size={14} /></span></Link><Link href="/app/tickets" className="quick-action"><Ticket size={20} /><span>Xem tickets <ChevronRight size={14} /></span></Link><Link href="/app/announcements" className="quick-action"><Megaphone size={20} /><span>Thông báo <ChevronRight size={14} /></span></Link></div>
    <div className="grid-two">
      <Card><div className="section-heading"><div><h2>Ticket gần đây</h2><p>Những yêu cầu cần bạn theo dõi</p></div><Link className="link" href="/app/tickets">Xem tất cả</Link></div>{openTickets.length ? openTickets.slice(0, 3).map((ticket) => <Link href={`/app/tickets/${ticket.id}`} className="ticket-row" key={ticket.id}><div className="stat-icon"><Wrench size={16} /></div><div className="ticket-row-main"><div className="ticket-row-title">{ticket.title}</div><div className="ticket-row-meta"><span>{ticket.ticket_code}</span><span>·</span><span>{fromNow(ticket.updated_at)}</span><Badge tone={ticket.priority === "urgent" || ticket.priority === "high" ? "danger" : "neutral"}>{label(ticket.priority)}</Badge></div></div><div className="ticket-row-aside"><Badge tone={ticket.status === "in_progress" ? "warning" : ticket.status === "resolved" ? "success" : "info"}>{label(ticket.status)}</Badge></div></Link>) : <div className="empty-state"><CheckCircle2 size={24} /><h3>{tickets.isLoading ? "Đang tải ticket" : "Tất cả đã ổn"}</h3><p>{tickets.isLoading ? "Đang lấy dữ liệu từ backend." : "Bạn không có ticket đang mở."}</p></div>}</Card>
      <Card><div className="section-heading"><div><h2>Thông báo mới</h2><p>Luôn cập nhật tình hình tòa nhà</p></div><Link className="link" href="/app/announcements">Xem tất cả</Link></div>{recentAnnouncements.map((item) => <Link href={`/app/announcements/${item.id}`} className="announcement-row" key={item.id}>{!item.is_read && <span className="unread-dot" />}<div className="announcement-row-main"><div className="announcement-row-title">{item.title}</div><div className="announcement-row-excerpt">{item.content}</div><div className="announcement-row-meta"><span>{label(item.type)}</span><span>{fromNow(item.published_at)}</span></div></div>{item.priority !== "normal" && <Badge tone={item.priority === "urgent" ? "danger" : "warning"}>{label(item.priority)}</Badge>}</Link>)}{!announcements.isLoading && recentAnnouncements.length === 0 && <div className="empty-state"><p>Chưa có thông báo.</p></div>}</Card>
    </div>
    <div className="grid-three"><Card><div className="section-heading"><div><h2>Trạng thái hỗ trợ</h2><p>Realtime của workspace</p></div><Sparkles size={18} color="var(--primary)" /></div><div className="metric-mini"><div className="metric-mini-icon"><MessageCircle size={17} /></div><div className="metric-mini-copy"><span>Ticket đang xử lý</span><strong>{openTickets.length}</strong></div></div><ProgressBar value={Math.min(100, openTickets.length * 25)} /></Card><Card><div className="section-heading"><div><h2>Đơn vị cư trú</h2><p>Thông tin từ hồ sơ resident</p></div><Home size={18} color="var(--primary)" /></div><div className="metric-mini"><div className="metric-mini-icon"><Home size={17} /></div><div className="metric-mini-copy"><span>Unit chính</span><strong>{primaryUnit?.unit_number ?? "—"}</strong></div></div><p className="stat-foot">Vai trò: {primaryUnit ? label(primaryUnit.resident_role) : "—"}</p></Card><Card><div className="section-heading"><div><h2>Nhắc nhở</h2><p>Thông tin quan trọng</p></div><Bell size={18} color="var(--primary)" /></div><div className="activity-item"><div className="activity-icon"><Bell size={14} /></div><div className="activity-copy"><strong>{unread.data?.unread_count ?? 0} thông báo chưa đọc</strong><span>Mở trang announcements để xem chi tiết.</span></div></div></Card></div>
  </div>;
}
