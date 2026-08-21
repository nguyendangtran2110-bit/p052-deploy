import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

export function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger" | "outline"; size?: "sm" | "md" | "lg" }) {
  return <button className={cn("button", `button-${variant}`, `button-${size}`, className)} {...props} />;
}

export function IconButton({ label, className, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <button aria-label={label} title={label} className={cn("icon-button", className)} {...props} />;
}

export function Input({ label, hint, error, className, ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string; hint?: string; error?: string }) {
  return <label className={cn("field", className)}>{label && <span className="field-label">{label}</span>}<input className={cn("input", error && "input-error")} {...props} />{hint && !error && <span className="field-hint">{hint}</span>}{error && <span className="field-error">{error}</span>}</label>;
}

export function Textarea({ label, hint, error, className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; hint?: string; error?: string }) {
  return <label className={cn("field", className)}>{label && <span className="field-label">{label}</span>}<textarea className={cn("input textarea", error && "input-error")} {...props} />{hint && !error && <span className="field-hint">{hint}</span>}{error && <span className="field-error">{error}</span>}</label>;
}

export function Select({ label, hint, error, className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label?: string; hint?: string; error?: string; children: ReactNode }) {
  return <label className={cn("field", className)}>{label && <span className="field-label">{label}</span>}<select className={cn("input", error && "input-error")} {...props}>{children}</select>{hint && !error && <span className="field-hint">{hint}</span>}{error && <span className="field-error">{error}</span>}</label>;
}

export function Badge({ children, tone = "neutral", className }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "danger" | "info" | "purple"; className?: string }) {
  return <span className={cn("badge", `badge-${tone}`, className)}>{children}</span>;
}

export function Card({ children, className, padding = true }: { children: ReactNode; className?: string; padding?: boolean }) {
  return <section className={cn("card", padding && "card-padding", className)}>{children}</section>;
}

export function Divider() {
  return <div className="divider" />;
}

export function EmptyState({ icon, title, description, action }: { icon?: ReactNode; title: string; description: string; action?: ReactNode }) {
  return <div className="empty-state">{icon && <div className="empty-icon">{icon}</div>}<h3>{title}</h3><p>{description}</p>{action}</div>;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} aria-hidden="true" />;
}

export function WorkspaceLoading() {
  return <div className="workspace-loading" role="status" aria-live="polite"><div className="workspace-loading-card"><div className="workspace-loading-mark">O</div><div className="workspace-loading-spinner" aria-hidden="true" /><span>Đang tải workspace…</span></div></div>;
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>;
}

export function ProgressBar({ value, tone = "teal" }: { value: number; tone?: "teal" | "orange" | "purple" }) {
  return <div className="progress-track"><span className={`progress-value progress-${tone}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></div>;
}

export function Drawer({ title, description, onClose, children }: { title: string; description?: string; onClose: () => void; children: ReactNode }) {
  return <div className="drawer-overlay" role="dialog" aria-modal="true" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><aside className="drawer"><div className="drawer-header"><div><h2>{title}</h2>{description && <p>{description}</p>}</div><IconButton label="Đóng" onClick={onClose}>×</IconButton></div>{children}</aside></div>;
}
