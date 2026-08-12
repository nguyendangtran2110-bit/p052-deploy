"use client";

import Link from "next/link";
import { ArrowRight, Check, UserRound } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthLayout } from "@/components/auth-layout";
import { Button, Input } from "@/components/ui";
import { requestRegistration } from "@/lib/data";
import { useUiStore } from "@/stores/ui-store";

export default function RegisterPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [values, setValues] = useState({ resident_code: "", email: "", password: "" });
  const [pending, setPending] = useState(false);
  async function submit(event: React.FormEvent) { event.preventDefault(); if (values.password.length < 12) return showToast({ tone: "error", message: "Mật khẩu cần tối thiểu 12 ký tự." }); setPending(true); try { await requestRegistration(values); router.push(`/register/verify?email=${encodeURIComponent(values.email)}`); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gửi yêu cầu đăng ký." }); } finally { setPending(false); } }
  return <AuthLayout eyebrow="Resident onboarding"><div className="auth-form-header"><div className="eyebrow">Đăng ký resident</div><h2>Tạo tài khoản của bạn</h2><p>Hồ sơ resident cần được ban quản lý provision trước khi đăng ký.</p></div><form className="auth-form" onSubmit={submit}><Input label="Resident code" placeholder="RES-1204" value={values.resident_code} onChange={(event) => setValues({ ...values, resident_code: event.target.value })} required hint="Mã có trong email hoặc thông tin bàn giao căn hộ." /><Input label="Email" type="email" value={values.email} onChange={(event) => setValues({ ...values, email: event.target.value })} required /><Input label="Mật khẩu" type="password" value={values.password} onChange={(event) => setValues({ ...values, password: event.target.value })} required hint="Tối thiểu 12 ký tự." /><Button type="submit" size="lg" disabled={pending}>{pending ? "Đang gửi…" : "Tiếp tục xác thực"} {!pending && <ArrowRight size={16} />}</Button></form><div className="auth-note"><Check size={14} style={{ verticalAlign: "-3px", marginRight: 5 }} /> Sau bước này, mã OTP 6 số sẽ được gửi qua email. OnBxrd không hiển thị OTP trong log hoặc UI.</div><div className="auth-links"><Link href="/login">Đã có tài khoản? Đăng nhập</Link><span /></div></AuthLayout>;
}
