"use client";

import Link from "next/link";
import { ArrowLeft, FilePlus2, Paperclip, Send, UploadCloud } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AppShell } from "@/components/app-shell";
import { Button, Card, Input, PageHeader, Select, Textarea } from "@/components/ui";
import { uploadAttachment, validateAttachment } from "@/lib/data";
import { useResidentProfile } from "@/features/resident/queries";
import { useCreateTicket } from "@/features/tickets/queries";
import { useUiStore } from "@/stores/ui-store";
import { label } from "@/lib/format";

const ticketSchema = z.object({
  unit_id: z.string().min(1, "Chọn căn hộ cần hỗ trợ"),
  category: z.string().min(2, "Nhập nhóm sự cố"),
  priority: z.enum(["low", "medium", "high", "urgent"]),
  title: z.string().min(2, "Tiêu đề tối thiểu 2 ký tự"),
  description: z.string().min(5, "Mô tả tối thiểu 5 ký tự"),
  location: z.string().min(2, "Vị trí tối thiểu 2 ký tự"),
});
type TicketForm = z.infer<typeof ticketSchema>;

export default function NewTicketPage() {
  const profile = useResidentProfile();
  const create = useCreateTicket();
  const showToast = useUiStore((state) => state.showToast);
  const [attachments, setAttachments] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [idempotencyKey] = useState(() => typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `ticket-${Date.now()}`);
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<TicketForm>({ resolver: zodResolver(ticketSchema), defaultValues: { unit_id: "", category: "maintenance", priority: "medium" } });

  useEffect(() => {
    const primary = profile.data?.units.find((unit) => unit.is_primary) ?? profile.data?.units[0];
    if (primary) setValue("unit_id", primary.id, { shouldValidate: true });
  }, [profile.data?.units, setValue]);

  useEffect(() => {
    const subject = new URLSearchParams(window.location.search).get("subject");
    if (subject) setValue("title", subject);
  }, [setValue]);

  async function onSubmit(values: TicketForm) {
    try {
      const ticket = await create.mutateAsync({ ...values, attachment_ids: attachments, idempotencyKey });
      showToast({ tone: "success", message: "Ticket đã được tạo thành công." });
      window.location.href = `/app/tickets/${ticket.id}`;
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tạo ticket." });
    }
  }

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    const invalid = Array.from(files).map(validateAttachment).find(Boolean);
    if (invalid) { showToast({ tone: "error", message: invalid }); return; }
    setUploading(true);
    try {
      const uploaded = await Promise.all(Array.from(files).slice(0, 5).map((file) => uploadAttachment(file)));
      setAttachments((current) => [...current, ...uploaded.map((item) => item.id)]);
      showToast({ tone: "success", message: `${uploaded.length} file đã sẵn sàng đính kèm.` });
    } catch { showToast({ tone: "error", message: "Upload file thất bại, vui lòng thử lại." }); }
    finally { setUploading(false); }
  }

  return <AppShell><PageHeader eyebrow="Tickets / New" title="Tạo ticket mới" description="Mô tả rõ sự cố để ban quản lý có thể xử lý nhanh hơn." actions={<Link href="/app/tickets"><Button variant="ghost"><ArrowLeft size={16} /> Quay lại tickets</Button></Link>} /><div className="detail-layout"><Card><form className="form-grid" onSubmit={handleSubmit(onSubmit)}><div className="section-heading"><div><h2>Thông tin yêu cầu</h2><p>Ticket sẽ tạo một conversation riêng để bạn theo dõi.</p></div><FilePlus2 size={20} color="#087f77" /></div><div className="form-grid form-grid-two"><Select label="Căn hộ / unit" error={errors.unit_id?.message} {...register("unit_id")}><option value="">Chọn unit</option>{profile.data?.units.map((unit) => <option value={unit.id} key={unit.id}>{unit.unit_number} · Tòa {unit.building} {unit.is_primary ? "(chính)" : ""}</option>)}</Select><Select label="Mức độ ưu tiên" error={errors.priority?.message} {...register("priority")}><option value="low">{label("low")}</option><option value="medium">{label("medium")}</option><option value="high">{label("high")}</option><option value="urgent">{label("urgent")}</option></Select></div><Input label="Nhóm sự cố" placeholder="Ví dụ: plumbing, maintenance, parking" error={errors.category?.message} {...register("category")} /><Input label="Tiêu đề" placeholder="Ví dụ: Rò rỉ nước dưới bồn rửa bếp" error={errors.title?.message} {...register("title")} /><Textarea label="Mô tả chi tiết" placeholder="Điều gì đã xảy ra? Xảy ra từ khi nào?" error={errors.description?.message} {...register("description")} /><Input label="Vị trí" placeholder="Ví dụ: Căn hộ A-1204, khu bếp" error={errors.location?.message} {...register("location")} /><label className="upload-zone"><UploadCloud size={22} /><strong>{uploading ? "Đang upload…" : "Đính kèm hình ảnh hoặc tài liệu"}</strong><span>Tối đa 5 file · File được upload trực tiếp lên private storage</span><input type="file" multiple hidden accept="image/*,.pdf,.doc,.docx" onChange={(event) => void handleFiles(event.target.files)} /></label>{attachments.length > 0 && <div className="file-row"><Paperclip size={15} color="#087f77" /><div className="file-copy"><strong>{attachments.length} file đã sẵn sàng</strong><span>Attachment sẽ được gửi cùng ticket</span></div></div>}<div className="form-actions"><Link href="/app/tickets"><Button type="button" variant="ghost">Hủy</Button></Link><Button type="submit" disabled={create.isPending || uploading}><Send size={15} />{create.isPending ? "Đang tạo…" : "Tạo ticket"}</Button></div></form></Card><Card><div className="section-heading"><div><h2>Trước khi gửi</h2><p>Thông tin giúp xử lý đúng người</p></div></div><div className="activity-list"><div className="activity-item"><div className="activity-icon">1</div><div className="activity-copy"><strong>Chọn đúng unit</strong><span>Chỉ các unit bạn được phép truy cập mới xuất hiện.</span></div></div><div className="activity-item"><div className="activity-icon">2</div><div className="activity-copy"><strong>Thêm vị trí cụ thể</strong><span>Ví dụ tầng, phòng hoặc khu vực chung.</span></div></div><div className="activity-item"><div className="activity-icon">3</div><div className="activity-copy"><strong>Kiểm tra lại trước khi gửi</strong><span>Không gửi thông tin nhạy cảm trong mô tả.</span></div></div></div></Card></div></AppShell>;
}
