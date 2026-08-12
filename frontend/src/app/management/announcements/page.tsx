"use client";

import Link from "next/link";
import { ChevronRight, FileEdit, Plus } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, EmptyState, PageHeader, Select } from "@/components/ui";
import { useAnnouncements } from "@/features/announcements/queries";
import { formatDate, label } from "@/lib/format";

export default function ManagementAnnouncementsPage() {
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const list = useAnnouncements({ status: status || undefined, type: type || undefined, offset: 0, limit: 50 }, true);
  const items = list.data?.items ?? [];

  return <AppShell>
    <PageHeader eyebrow="Management / Announcements" title="Announcement lifecycle" description="Soạn draft, review scope, publish và archive. Published content dùng version để xử lý conflict an toàn." actions={<Link href="/management/announcements/new"><Button><Plus size={16} /> Tạo announcement</Button></Link>} />
    <Card padding={false}>
      <div style={{ padding: 16, borderBottom: "1px solid var(--line)" }}>
        <div className="filter-bar">
          <Select aria-label="Status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Mọi status</option><option value="draft">Draft</option><option value="published">Published</option><option value="archived">Archived</option></Select>
          <Select aria-label="Type" value={type} onChange={(event) => setType(event.target.value)}><option value="">Mọi type</option><option value="maintenance">Maintenance</option><option value="facility">Facility</option><option value="event">Event</option><option value="emergency">Emergency</option></Select>
        </div>
      </div>
      {list.isError ? <div className="error-state">Không thể tải announcement. Vui lòng thử lại.</div> : list.isLoading ? <div className="empty-state"><p>Đang tải announcement…</p></div> : items.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Announcement</th><th>Type / priority</th><th>Status</th><th>Audience</th><th>Version</th><th>Updated</th><th /></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><Link href={`/management/announcements/${item.id}`}><div className="row-title">{item.title}</div><div className="row-subtitle">{item.announcement_code}</div></Link></td><td><Badge tone={item.priority === "urgent" ? "danger" : item.priority === "important" ? "warning" : "neutral"}>{label(item.priority)}</Badge><div className="row-subtitle">{label(item.type)}</div></td><td><Badge tone={item.status === "published" ? "success" : item.status === "draft" ? "info" : "neutral"}>{label(item.status)}</Badge></td><td>{item.scopes[0]?.scope_type === "all_residents" ? "All residents" : item.scopes[0]?.building ? `Tòa ${item.scopes[0].building}` : "Custom scope"}</td><td>v{item.version}</td><td>{formatDate(item.updated_at)}</td><td><Link href={`/management/announcements/${item.id}`}><ChevronRight size={16} color="#9aa9ad" /></Link></td></tr>)}</tbody></table></div> : <EmptyState title="Chưa có announcement" description="Không có announcement phù hợp với bộ lọc server." />}
      <div className="pagination"><span>{list.data?.total ?? 0} announcement</span><span style={{ color: "#9aa9ad" }}><FileEdit size={13} style={{ verticalAlign: "-2px" }} /> Draft có thể sửa/xóa · Published chỉ archive</span></div>
    </Card>
  </AppShell>;
}
