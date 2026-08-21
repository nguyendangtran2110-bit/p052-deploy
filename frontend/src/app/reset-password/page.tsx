"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthLayout } from "@/components/auth-layout";
import { Button, Input } from "@/components/ui";
import { resetPassword } from "@/lib/data";
import { USE_MOCKS } from "@/lib/api-client";
import { useUiStore } from "@/stores/ui-store";

export default function ResetPasswordPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (pending) return;
    if (password.length < 12) return showToast({ tone: "error", message: "Mật khẩu cần tối thiểu 12 ký tự." });
    if (password !== confirm) return showToast({ tone: "error", message: "Mật khẩu xác nhận chưa khớp." });
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token && !USE_MOCKS) return showToast({ tone: "error", message: "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn." });
    setPending(true);
    try {
      await resetPassword(token ?? "mock-reset-token", password);
      showToast({ tone: "success", message: "Mật khẩu đã được đặt lại." });
      router.push("/login");
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể đặt lại mật khẩu." });
    } finally {
      setPending(false);
    }
  }

  return <AuthLayout eyebrow="Account recovery"><div className="auth-form-header"><div className="eyebrow">Mật khẩu mới</div><h2>Chọn mật khẩu an toàn</h2><p>Liên kết reset chỉ dùng một lần và có thời hạn 15 phút.</p></div><form className="auth-form" onSubmit={submit}><Input label="Mật khẩu mới" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required hint="Tối thiểu 12 ký tự." /><Input label="Nhập lại mật khẩu" type="password" value={confirm} onChange={(event) => setConfirm(event.target.value)} required /><Button type="submit" size="lg" disabled={pending}>{pending ? "Đang lưu…" : "Lưu mật khẩu"} {!pending && <ArrowRight size={16} />}</Button></form><div className="auth-note"><CheckCircle2 size={14} style={{ verticalAlign: "-3px", marginRight: 5 }} /> Sau khi thành công, bạn sẽ được chuyển về trang đăng nhập.</div><div className="auth-links"><Link href="/login">Quay lại đăng nhập</Link><span /></div></AuthLayout>;
}
