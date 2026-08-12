import { formatDistanceToNow, format } from "date-fns";
import { vi } from "date-fns/locale";

export function formatDate(value?: string | null, pattern = "dd/MM/yyyy HH:mm") {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : format(date, pattern, { locale: vi });
}

export function fromNow(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : formatDistanceToNow(date, { addSuffix: true, locale: vi });
}

export function formatFileSize(size?: number | null) {
  if (!size) return "0 B";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function initials(name?: string | null) {
  return (name ?? "OnBxrd")
    .split(" ")
    .filter(Boolean)
    .slice(-2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export const labelMap: Record<string, string> = {
  submitted: "Đã gửi",
  approved: "Đã duyệt",
  in_progress: "Đang xử lý",
  resolved: "Đã giải quyết",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
  low: "Thấp",
  medium: "Trung bình",
  high: "Cao",
  urgent: "Khẩn cấp",
  form: "Biểu mẫu",
  chat: "Chatbot",
  bot_active: "Bot đang hỗ trợ",
  waiting_management: "Chờ ban quản lý",
  management_active: "Ban quản lý đang xử lý",
  general: "Chung",
  maintenance: "Bảo trì",
  facility: "Tiện ích",
  regulation_update: "Cập nhật quy định",
  event: "Sự kiện",
  emergency: "Khẩn cấp",
  normal: "Bình thường",
  important: "Quan trọng",
  draft: "Bản nháp",
  published: "Đã phát hành",
  archived: "Đã lưu trữ",
  admin: "Admin",
  manager: "Manager",
  staff: "Staff",
  indexed: "Đã lập chỉ mục",
  indexing: "Đang lập chỉ mục",
  pending: "Đang chờ",
  failed: "Thất bại",
};

export const label = (value?: string | null) => (value ? labelMap[value] ?? value.replaceAll("_", " ") : "—");
