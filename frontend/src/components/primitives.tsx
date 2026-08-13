import Link from "next/link";
import { Children, cloneElement, useEffect, useId, useLayoutEffect, useRef } from "react";
import type { ButtonHTMLAttributes, HTMLAttributes, ReactElement, ReactNode } from "react";
import { createPortal } from "react-dom";
import { ArrowIcon, CheckIcon } from "@/src/components/icons";

export function PageHeader({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <header className="page-header reveal">
      <div className="page-header-copy">
        <h1 tabIndex={-1}>{title}</h1>
        <p>{description}</p>
      </div>
      {action ? <div className="page-header-action">{action}</div> : null}
    </header>
  );
}

export function Card({ children, className = "", as: Tag = "section", ...props }: { children: ReactNode; className?: string; as?: "section" | "article" | "div" } & HTMLAttributes<HTMLElement>) {
  return <Tag className={`card ${className}`} {...props}>{children}</Tag>;
}

export function Button({ className = "", kind = "primary", children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { kind?: "primary" | "secondary" | "quiet" | "danger" }) {
  return <button className={`button button-${kind} ${className}`} {...props}>{children}</button>;
}

export function ButtonLink({ href, children, kind = "primary", className = "" }: { href: string; children: ReactNode; kind?: "primary" | "secondary" | "quiet"; className?: string }) {
  return <Link className={`button button-${kind} ${className}`} href={href}>{children}</Link>;
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status.toLowerCase().replaceAll(" ", "-")}`}><span className="status-dot" />{status}</span>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <Card className="empty-state">
      <div className="signal-orbit" aria-hidden="true"><span /><span /><span /></div>
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </Card>
  );
}

type FieldControlProps = {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
};

export function FormField({ id, label, hint, error, children }: { id?: string; label: string; hint?: string; error?: string; children: ReactElement<FieldControlProps> }) {
  const generatedId = useId();
  const controlId = id ?? `field-${generatedId.replaceAll(":", "")}`;
  const descriptions = [hint ? `${controlId}-hint` : "", error ? `${controlId}-error` : ""].filter(Boolean).join(" ");
  const control = Children.only(children);
  return (
    <label className="field" htmlFor={controlId}>
      <span className="field-label">{label}</span>
      {cloneElement(control, {
        id: control.props.id ?? controlId,
        "aria-describedby": descriptions || control.props["aria-describedby"],
        "aria-invalid": error ? true : control.props["aria-invalid"],
      })}
      {hint ? <span id={`${controlId}-hint`} className="field-hint">{hint}</span> : null}
      {error ? <span id={`${controlId}-error`} className="field-error">{error}</span> : null}
    </label>
  );
}

export function ModalDialog({ open, title, description, focusKey = title, onClose, children }: { open: boolean; title: string; description?: string; focusKey?: string; onClose: () => void; children: ReactNode }) {
  const titleId = useId();
  const descriptionId = useId();
  const dialogRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const closeRef = useRef(onClose);

  useEffect(() => { closeRef.current = onClose; }, [onClose]);

  useEffect(() => {
    if (!open) return;
    triggerRef.current = document.activeElement as HTMLElement;
    const dialog = dialogRef.current;
    const background = document.querySelector<HTMLElement>(".app-shell, .public-shell");
    background?.setAttribute("inert", "");
    const focusable = () => Array.from(dialog?.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])') ?? []);
    window.setTimeout(() => (dialog?.querySelector<HTMLElement>("[data-safe-focus]") ?? focusable()[0] ?? dialog)?.focus(), 0);
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); closeRef.current(); return; }
      if (event.key !== "Tab") return;
      const items = focusable();
      if (!items.length) { event.preventDefault(); dialog?.focus(); return; }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      background?.removeAttribute("inert");
      window.setTimeout(() => triggerRef.current?.focus(), 0);
    };
  }, [open]);

  useLayoutEffect(() => {
    if (!open) return;
    const dialog = dialogRef.current;
    const target = dialog?.querySelector<HTMLElement>("h2") ?? dialog;
    target?.focus({ preventScroll: true });
  }, [focusKey, open]);

  if (!open) return null;
  return createPortal(<div className="dialog-scrim" onMouseDown={(event) => { if (event.target === event.currentTarget) closeRef.current(); }}><section ref={dialogRef} className="dialog" role="dialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={description ? descriptionId : undefined} tabIndex={-1}><h2 id={titleId} tabIndex={-1}>{title}</h2>{description ? <p id={descriptionId}>{description}</p> : null}{children}</section></div>, document.body);
}

export function SignalLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link className="signal-link" href={href}>{children}<ArrowIcon /></Link>;
}

export function CheckList({ items }: { items: string[] }) {
  return <ul className="check-list">{items.map((item) => <li key={item}><CheckIcon />{item}</li>)}</ul>;
}
