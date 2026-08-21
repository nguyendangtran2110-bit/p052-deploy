"use client";

import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { useEffect } from "react";
import { useUiStore } from "@/stores/ui-store";
import { IconButton } from "@/components/ui";

export function ToastViewport() {
  const toast = useUiStore((state) => state.toast);
  const clearToast = useUiStore((state) => state.clearToast);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(clearToast, 4200);
    return () => window.clearTimeout(timer);
  }, [toast, clearToast]);

  if (!toast) return null;
  const Icon = toast.tone === "success" ? CheckCircle2 : toast.tone === "error" ? AlertCircle : Info;
  return <div className={`toast toast-${toast.tone}`} role="status"><Icon size={18} /><span>{toast.message}</span><IconButton label="Đóng thông báo" onClick={clearToast}><X size={16} /></IconButton></div>;
}

export function ConnectionPill({ state }: { state: "connected" | "connecting" | "offline" }) {
  const label = state === "connected" ? "Realtime đang bật" : state === "connecting" ? "Đang kết nối" : "Mất kết nối";
  return <span className={`connection-pill connection-${state}`}><span className="connection-dot" />{label}</span>;
}

export function ErrorState({ message = "Không thể tải dữ liệu.", onRetry }: { message?: string; onRetry?: () => void }) {
  return <div className="error-state"><AlertCircle size={18} /><div><strong>Có lỗi xảy ra</strong><p>{message}</p>{onRetry && <button className="text-button" onClick={onRetry}>Thử lại</button>}</div></div>;
}
