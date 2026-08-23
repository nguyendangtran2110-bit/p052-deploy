"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, KeyRound, LogOut, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Button, Card, Input, PageHeader } from "@/components/ui";
import { changePassword, logoutAll } from "@/lib/data";
import { clearSession } from "@/lib/auth-session";
import { useUiStore } from "@/stores/ui-store";

export default function SecurityPage() {
  const router = useRouter();
  const showToast = useUiStore((state) => state.showToast);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pending, setPending] = useState(false);
  const [logoutPending, setLogoutPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (next.length < 12) return showToast({ tone: "error", message: "Mật khẩu mới cần tối thiểu 12 ký tự." });
    if (next !== confirm) return showToast({ tone: "error", message: "Mật khẩu xác nhận chưa khớp." });
    setPending(true);
    try {
      await changePassword(current, next);
      setCurrent(""); setNext(""); setConfirm("");
      showToast({ tone: "success", message: "Mật khẩu đã được cập nhật." });
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể đổi mật khẩu." });
    } finally {
      setPending(false);
    }
  }

  async function handleLogoutAll() {
    if (!window.confirm("Đăng xuất khỏi tất cả thiết bị?")) return;
    setLogoutPending(true);
    try {
      await logoutAll();
    } catch (error) {
      showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể gọi logout-all; phiên local vẫn sẽ được xóa." });
    } finally {
      clearSession();
      router.replace("/login");
    }
  }

  return <><PageHeader eyebrow="Account / Security" title="Bảo mật tài khoản" description="Access token chỉ tồn tại trong memory; refresh token được dùng để khôi phục phiên sau reload." actions={<Link href="/app/profile"><Button variant="ghost"><ArrowLeft size={16} /> Quay lại tài khoản</Button></Link>} /><div className="grid-two"><Card><div className="section-heading"><div><h2>Đổi mật khẩu</h2><p>Dùng mật khẩu tối thiểu 12 ký tự.</p></div><KeyRound size={19} color="var(--primary)" /></div><form className="form-grid" onSubmit={submit}><Input label="Mật khẩu hiện tại" type="password" autoComplete="current-password" value={current} onChange={(event) => setCurrent(event.target.value)} required /><Input label="Mật khẩu mới" type="password" autoComplete="new-password" value={next} onChange={(event) => setNext(event.target.value)} required hint="Tối thiểu 12 ký tự, nên kết hợp chữ hoa, chữ thường, số và ký tự đặc biệt." /><Input label="Nhập lại mật khẩu mới" type="password" autoComplete="new-password" value={confirm} onChange={(event) => setConfirm(event.target.value)} required /><div className="form-actions"><Button type="submit" disabled={pending}>{pending ? "Đang cập nhật…" : "Cập nhật mật khẩu"}</Button></div></form></Card><Card><div className="section-heading"><div><h2>Quản lý phiên</h2><p>Đóng mọi phiên đang đăng nhập</p></div><ShieldCheck size={19} color="var(--primary)" /></div><div className="notice-card"><ShieldCheck size={17} /><div><strong>Thiết bị hiện tại</strong><p>Phiên đang hoạt động trên trình duyệt này.</p></div></div><Button variant="danger" onClick={() => void handleLogoutAll()} disabled={logoutPending}><LogOut size={15} /> {logoutPending ? "Đang đăng xuất…" : "Logout tất cả phiên"}</Button></Card></div></>;
}
