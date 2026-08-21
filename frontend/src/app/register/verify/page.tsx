"use client";

import Link from "next/link";
import { ArrowLeft, ArrowRight, MailCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthLayout } from "@/components/auth-layout";
import { Button, Input } from "@/components/ui";
import { resendVerification, verifyRegistration } from "@/lib/data";
import { setSession } from "@/lib/auth-session";
import { useUiStore } from "@/stores/ui-store";

export default function VerifyRegistrationPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [seconds, setSeconds] = useState(60);
  const [pending, setPending] = useState(false);
  const [resending, setResending] = useState(false);

  useEffect(() => { const value = new URLSearchParams(window.location.search).get("email"); if (value) setEmail(value); }, []);
  useEffect(() => { if (!seconds) return; const timer = window.setInterval(() => setSeconds((value) => Math.max(0, value - 1)), 1000); return () => window.clearInterval(timer); }, [seconds]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!/^\d{6}$/.test(code)) return showToast({ tone: "error", message: "Nhập đúng mã OTP 6 số." });
    setPending(true);
    try { const tokens = await verifyRegistration(email, code); setSession(tokens); router.push("/app"); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Mã xác thực không hợp lệ hoặc đã hết hạn." }); }
    finally { setPending(false); }
  }

  async function resend() {
    if (seconds > 0 || resending) return;
    setResending(true);
    try { await resendVerification(email); setSeconds(60); showToast({ tone: "success", message: "Mã xác thực mới đã được gửi." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi lại mã xác thực." }); }
    finally { setResending(false); }
  }

  return <AuthLayout eyebrow="Verify email"><div className="auth-form-header"><div className="eyebrow">Xác thực email</div><h2>Kiểm tra hộp thư</h2><p>Mã 6 số đã được gửi tới <strong>{email}</strong>. Mã có thời hạn ngắn và chỉ dùng một lần.</p></div><form className="auth-form" onSubmit={submit}><Input label="Mã xác thực" inputMode="numeric" maxLength={6} placeholder="000000" value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))} required /><Button type="submit" size="lg" disabled={pending}>{pending ? "Đang xác thực…" : "Xác thực và vào app"} {!pending && <ArrowRight size={16} />}</Button></form><div className="auth-note"><MailCheck size={14} style={{ verticalAlign: "-3px", marginRight: 5 }} /> Không nhận được email? <button className="text-button" onClick={() => void resend()} disabled={seconds > 0 || resending}>{resending ? "Đang gửi…" : seconds > 0 ? `Gửi lại sau ${seconds}s` : "Gửi lại mã"}</button></div><div className="auth-links"><Link href="/register"><ArrowLeft size={13} style={{ verticalAlign: "-2px" }} /> Quay lại</Link><span /></div></AuthLayout>;
}
