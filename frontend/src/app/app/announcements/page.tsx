"use client";

import Link from "next/link";
import { Bell, CalendarDays, ChevronRight, Filter, Megaphone } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Card, EmptyState, Input, PageHeader, Select } from "@/components/ui";
import { fromNow, label } from "@/lib/format";
import { useAnnouncements } from "@/features/announcements/queries";

export default function AnnouncementsPage() {
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [type, setType] = useState("");
  const [priority, setPriority] = useState("");
  const announcements = useAnnouncements({ unread_only: unreadOnly, type: type || undefined, priority: priority || undefined, offset: 0, limit: 20 });
  const items = announcements.data?.items ?? [];

  return <AppShell><PageHeader eyebrow="Resident space / Announcements" title="Thông báo cư dân" description="Bộ lọc type, priority và unread được gửi trực tiếp lên backend." /><Card padding={false}><div className="tabs"><button className={`tab ${!unreadOnly ? "tab-active" : ""}`} onClick={() => setUnreadOnly(false)}>Tất cả</button><button className={`tab ${unreadOnly ? "tab-active" : ""}`} onClick={() => setUnreadOnly(true)}>Chưa đọc</button></div><div style={{ padding: 16, borderBottom: "1px solid var(--line)" }}><div className="filter-bar"><Select aria-label="Loại thông báo" value={type} onChange={(event) => setType(event.target.value)}><option value="">Mọi loại</option><option value="maintenance">Bảo trì</option><option value="facility">Tiện ích</option><option value="regulation_update">Quy định</option><option value="event">Sự kiện</option><option value="emergency">Khẩn cấp</option></Select><Select aria-label="Mức độ" value={priority} onChange={(event) => setPriority(event.target.value)}><option value="">Mọi mức độ</option><option value="normal">Bình thường</option><option value="important">Quan trọng</option><option value="urgent">Khẩn cấp</option></Select><Filter size={16} color="#9aa9ad" /></div></div>{announcements.isError ? <div className="error-state">Không thể tải danh sách thông báo.</div> : items.length ? <div className="announcement-list" style={{ padding: "0 22px" }}>{items.map((item) => <Link href={`/app/announcements/${item.id}`} className="announcement-row" key={item.id}>{!item.is_read && <span className="unread-dot" />}<div className="announcement-row-main"><div className="announcement-row-title">{item.title}</div><div className="announcement-row-excerpt">{item.content}</div><div className="announcement-row-meta"><span><Megaphone size={11} style={{ verticalAlign: "-2px" }} /> {label(item.type)}</span><span><CalendarDays size={11} style={{ verticalAlign: "-2px" }} /> {fromNow(item.published_at)}</span>{item.expires_at && <span>Hết hạn {fromNow(item.expires_at)}</span>}</div></div><div style={{ display: "flex", alignItems: "center", gap: 9 }}>{item.priority !== "normal" && <Badge tone={item.priority === "urgent" ? "danger" : "warning"}>{label(item.priority)}</Badge>}<ChevronRight size={16} color="#aab8ba" /></div></Link>)}</div> : <EmptyState icon={<Bell size={21} />} title={unreadOnly ? "Bạn đã đọc hết thông báo" : "Chưa có thông báo"} description="Khi có thông tin mới từ ban quản lý, thông báo sẽ xuất hiện tại đây." />}</Card></AppShell>;
}
