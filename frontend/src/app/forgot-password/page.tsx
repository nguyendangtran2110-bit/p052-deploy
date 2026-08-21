"use client";

import Link from "next/link";
import { ArrowLeft, ArrowRight, Mail } from "lucide-react";
import { useState } from "react";
import { AuthLayout } from "@/components/auth-layout";
import { Button, Input } from "@/components/ui";
import { forgotPassword } from "@/lib/data";
import { useUiStore } from "@/stores/ui-store";

export default function ForgotPasswordPage() {
  const showToast = useUiStore((state) => state.showToast);
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    try {
      await forgotPassword(email);
      setSent(true);
      showToast({ tone: "success", message: "Nếu email hợp lệ, hướng dẫn sẽ được gửi." });
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi hướng dẫn đặt lại mật khẩu." });
    } finally {
      setPending(false);
    }
  }

  return <AuthLayout eyebrow="Account recovery"><div className="auth-form-header"><div className="eyebrow">Quên mật khẩu</div><h2>Đặt lại quyền truy cập</h2><p>Nhập email tài khoản. Vì lý do bảo mật, OnBxrd hiển thị cùng một phản hồi cho email tồn tại và không tồn tại.</p></div>{sent ? <div className="auth-note" style={{ marginTop: 28 }}><Mail size={16} style={{ verticalAlign: "-3px", marginRight: 6 }} /> Kiểm tra email của bạn để mở liên kết đặt lại mật khẩu.</div> : <form className="auth-form" onSubmit={submit}><Input label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="you@example.com" /><Button type="submit" size="lg" disabled={pending}>{pending ? "Đang gửi…" : "Gửi hướng dẫn"} {!pending && <ArrowRight size={16} />}</Button></form>}<div className="auth-links"><Link href="/login"><ArrowLeft size={13} style={{ verticalAlign: "-2px" }} /> Quay lại đăng nhập</Link><span /></div></AuthLayout>;
}
