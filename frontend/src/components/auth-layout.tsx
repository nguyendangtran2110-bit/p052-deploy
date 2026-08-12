import Link from "next/link";
import type { ReactNode } from "react";
import { ToastViewport } from "@/components/feedback";

export function AuthLayout({ children, eyebrow = "Resident operations" }: { children: ReactNode; eyebrow?: string }) {
  return <div className="auth-page"><section className="auth-visual"><Link href="/login" className="brand"><div className="brand-mark">O</div><div><strong>OnBxrd</strong><span>Resident operations</span></div></Link><div className="auth-copy"><div className="eyebrow">{eyebrow}</div><h1>Everyday living, handled.</h1><p>Một nơi đơn giản để hỏi đáp, gửi yêu cầu và kết nối với ban quản lý tòa nhà.</p></div><div className="auth-quote">“Không còn phải nhớ xem quy định nằm ở đâu — chỉ cần hỏi OnBxrd.”<strong>— Cư dân tòa A</strong></div></section><section className="auth-panel"><div className="auth-form-wrap">{children}</div></section><ToastViewport /></div>;
}
