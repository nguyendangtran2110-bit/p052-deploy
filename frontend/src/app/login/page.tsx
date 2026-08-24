"use client";

import Link from "next/link";
import { ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthLayout } from "@/components/auth-layout";
import { Button, Input } from "@/components/ui";
import { login } from "@/lib/data";
import { USE_MOCKS } from "@/lib/api-client";
import { setSession } from "@/lib/auth-session";
import { useUiStore } from "@/stores/ui-store";

export default function LoginPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  async function submit(event: React.FormEvent) { event.preventDefault(); if (!email || !password) return; setPending(true); try { const tokens = await login(email, password); setSession(tokens); router.push(tokens.account.role === "management" ? "/management" : "/app"); } catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Email hoặc mật khẩu không đúng." }); } finally { setPending(false); } }
  return <AuthLayout><div className="auth-form-header"><div className="eyebrow">Chào mừng trở lại</div><h2>Đăng nhập workspace</h2><p>Sử dụng email tài khoản OnBxrd của bạn để tiếp tục.</p></div><form className="auth-form" onSubmit={submit}><Input label="Email" type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(event) => setEmail(event.target.value)} required /><Input label="Mật khẩu" type="password" autoComplete="current-password" placeholder="Nhập mật khẩu" value={password} onChange={(event) => setPassword(event.target.value)} required /><div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--muted)", fontSize: 11 }}><LockKeyhole size={14} /> Phiên đăng nhập được bảo vệ</div><Button type="submit" size="lg" disabled={pending}>{pending ? "Đang đăng nhập…" : "Đăng nhập"} {!pending && <ArrowRight size={16} />}</Button></form><div className="auth-links"><Link href="/forgot-password">Quên mật khẩu?</Link><Link href="/register">Đăng ký resident</Link></div>{USE_MOCKS && <div className="auth-note"><Mail size={14} style={{ verticalAlign: "-3px", marginRight: 5 }} /> Mock mode: mọi email hợp lệ có thể dùng để xem giao diện.</div>}</AuthLayout>;
}
