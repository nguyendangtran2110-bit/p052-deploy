"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Eye, Megaphone, Paperclip, Send } from "lucide-react";
import { useState } from "react";
import { Badge, Button, Card, Input, PageHeader, Select, Textarea } from "@/components/ui";
import { useAnnouncementMutations } from "@/features/announcements/queries";
import { useUnits } from "@/features/management/queries";
import { fetchAnnouncement, updateAnnouncement, uploadAttachment, validateAttachment } from "@/lib/data";
import type { AnnouncementScopeType } from "@/types";
import { useUiStore } from "@/stores/ui-store";

export default function NewAnnouncementPage() {
  const router = useRouter();
  const mutations = useAnnouncementMutations();
  const units = useUnits({ limit: 500 });
  const showToast = useUiStore((state) => state.showToast);
  const [form, setForm] = useState<{ title: string; content: string; type: string; priority: string; scope: AnnouncementScopeType; projectCode: string; building: string; unitId: string }>({ title: "", content: "", type: "general", priority: "normal", scope: "all_residents", projectCode: "", building: "", unitId: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  function setField<K extends keyof typeof form>(key: K, value: (typeof form)[K]) { setForm((current) => ({ ...current, [key]: value })); }

  async function save() {
    if (form.title.trim().length < 2 || form.content.trim().length < 2) return showToast({ tone: "error", message: "Title và content là bắt buộc." });
    if (form.scope === "project" && !form.projectCode.trim()) return showToast({ tone: "error", message: "Project scope cần project_code." });
    if (form.scope === "building" && (!form.projectCode.trim() || !form.building.trim())) return showToast({ tone: "error", message: "Building scope cần project_code và building." });
    if (form.scope === "unit" && !form.unitId) return showToast({ tone: "error", message: "Unit scope cần chọn unit UUID thật." });
    const scope = form.scope === "all_residents"
      ? { scope_type: "all_residents" as const }
      : form.scope === "project"
        ? { scope_type: "project" as const, project_code: form.projectCode.trim() }
        : form.scope === "building"
          ? { scope_type: "building" as const, project_code: form.projectCode.trim(), building: form.building.trim() }
          : { scope_type: "unit" as const, unit_id: form.unitId };
    try {
      const invalid = files.map(validateAttachment).find(Boolean);
      if (invalid) return showToast({ tone: "error", message: invalid });
      const item = await mutations.create.mutateAsync({ title: form.title.trim(), content: form.content.trim(), type: form.type, priority: form.priority, scopes: [scope] });
      let attachmentIds: string[] = [];
      if (files.length) {
        setUploading(true);
        const uploaded = await Promise.all(files.map((file) => uploadAttachment(file, { announcement_id: item.id })));
        attachmentIds = uploaded.map((file) => file.id);
        const latest = await fetchAnnouncement(item.id, true);
        await updateAnnouncement(item.id, { version: latest.version, attachment_ids: attachmentIds });
      }
      showToast({ tone: "success", message: "Draft announcement đã được tạo." });
      router.push(`/management/announcements/${item.id}`);
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tạo announcement." });
    } finally {
      setUploading(false);
    }
  }

  const selectedUnit = units.data?.find((unit) => unit.id === form.unitId);
  return <><PageHeader eyebrow="Management / Announcements / New" title="Tạo announcement" description="Tạo draft trước, review audience và publish bằng một bước xác nhận riêng." actions={<Link href="/management/announcements"><Button variant="ghost"><ArrowLeft size={16} /> Danh sách</Button></Link>} /><div className="editor-layout"><Card><div className="editor-form"><div className="section-heading"><div><h2>Announcement draft</h2><p>Không có scheduled publish trong MVP.</p></div><Megaphone size={19} color="var(--primary)" /></div><Input label="Tiêu đề" placeholder="Ví dụ: Bảo trì hệ thống cấp nước tòa A" value={form.title} onChange={(event) => setField("title", event.target.value)} /><div className="form-grid form-grid-two"><Select label="Type" value={form.type} onChange={(event) => setField("type", event.target.value)}><option value="general">Chung</option><option value="maintenance">Bảo trì</option><option value="facility">Tiện ích</option><option value="regulation_update">Cập nhật quy định</option><option value="event">Sự kiện</option><option value="emergency">Khẩn cấp</option></Select><Select label="Priority" value={form.priority} onChange={(event) => setField("priority", event.target.value)}><option value="normal">Bình thường</option><option value="important">Quan trọng</option><option value="urgent">Khẩn cấp</option></Select></div><Textarea label="Nội dung" placeholder="Viết nội dung announcement…" value={form.content} onChange={(event) => setField("content", event.target.value)} /><div className="form-grid form-grid-two"><Select label="Audience scope" value={form.scope} onChange={(event) => setField("scope", event.target.value as AnnouncementScopeType)}><option value="all_residents">Tất cả cư dân</option><option value="project">Project</option><option value="building">Building</option><option value="unit">Unit</option></Select>{form.scope === "unit" ? <Select label="Unit" value={form.unitId} onChange={(event) => setField("unitId", event.target.value)}><option value="">Chọn unit</option>{units.data?.map((unit) => <option value={unit.id} key={unit.id}>{unit.unit_number} · Tòa {unit.building} · {unit.id}</option>)}</Select> : <Input label="Project code" placeholder="P-001" value={form.projectCode} onChange={(event) => setField("projectCode", event.target.value)} disabled={form.scope === "all_residents"} />}</div>{form.scope === "building" && <Input label="Building" placeholder="A" value={form.building} onChange={(event) => setField("building", event.target.value)} />}{form.scope === "unit" && selectedUnit && <p className="field-hint">Unit hợp lệ: {selectedUnit.unit_number} · {selectedUnit.id}</p>}<label className="upload-zone"><Paperclip size={19} /><strong>{files.length ? `${files.length} file đã chọn` : "Đính kèm file"}</strong><span>Upload qua private S3 presigned URL sau khi draft được tạo</span><input type="file" multiple hidden accept="image/*,.pdf,.doc,.docx" onChange={(event) => setFiles(Array.from(event.target.files ?? []).slice(0, 5))} /></label><div className="form-actions"><Link href="/management/announcements"><Button type="button" variant="ghost">Hủy</Button></Link><Button type="button" variant="outline"><Eye size={15} /> Preview</Button><Button type="button" onClick={() => void save()} disabled={mutations.create.isPending || mutations.update.isPending || uploading}><Send size={15} /> {uploading ? "Đang upload…" : "Lưu draft"}</Button></div></div></Card><Card className="editor-preview"><div className="preview-label">Live preview</div><div className="announcement-row" style={{ paddingTop: 0, borderTop: 0 }}><span className="unread-dot" /><div className="announcement-row-main"><div className="announcement-row-title">{form.title || "Tiêu đề announcement"}</div><div className="announcement-row-excerpt">{form.content || "Nội dung sẽ hiển thị ở đây…"}</div><div className="announcement-row-meta"><span>{form.type}</span><span>Vừa tạo</span></div></div><Badge tone={form.priority === "urgent" ? "danger" : form.priority === "important" ? "warning" : "neutral"}>{form.priority}</Badge></div><div className="divider" style={{ margin: "20px 0" }} /><div className="info-item"><span>Audience</span><strong>{form.scope === "all_residents" ? "Tất cả cư dân" : form.scope === "unit" ? selectedUnit?.unit_number ?? "Chưa chọn unit" : `${form.scope} ${form.projectCode} ${form.building}`}</strong></div></Card></div></>;
}
