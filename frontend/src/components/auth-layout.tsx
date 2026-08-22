import Link from "next/link";
import type { ReactNode } from "react";
import { ToastViewport } from "@/components/feedback";
import { ThemeControl } from "@/components/theme-control";

export function AuthLayout({ children, eyebrow = "Resident operations" }: { children: ReactNode; eyebrow?: string }) {
  return <div className="auth-page"><a className="skip-link" href="#main-content">Bỏ qua đến nội dung chính</a><section className="auth-visual"><div className="auth-visual-top"><Link href="/" className="brand"><div className="brand-mark">O</div><div><strong>OnBxrd</strong><span>Resident operations</span></div></Link><ThemeControl compact /></div><div className="auth-copy"><div className="eyebrow">{eyebrow}</div><h1>Everyday living, handled.</h1><p>Một nơi đơn giản để hỏi đáp, gửi yêu cầu và kết nối với ban quản lý tòa nhà.</p></div><div className="auth-quote">Clear context for guidance, requests, and building updates.<strong>Resident operations workspace</strong></div></section><section id="main-content" className="auth-panel"><div className="auth-form-wrap">{children}</div></section><ToastViewport /></div>;
}
