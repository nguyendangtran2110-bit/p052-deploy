"use client";

import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/components/ui";

const HOVER_GRACE_MS = 100;

type SidebarNavLinkProps = {
  href: string;
  label: string;
  icon: LucideIcon;
  active: boolean;
  onNavigate: () => void;
};

export function SidebarNavLink({ href, label, icon: Icon, active, onNavigate }: SidebarNavLinkProps) {
  const timer = useRef<number | undefined>(undefined);
  const [isPowered, setIsPowered] = useState(false);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  function powerOn() {
    window.clearTimeout(timer.current);
    setIsPowered(true);
  }

  function powerOff() {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setIsPowered(false), HOVER_GRACE_MS);
  }

  return <Link
    href={href}
    onClick={onNavigate}
    onPointerEnter={(event) => { if (event.pointerType !== "touch") powerOn(); }}
    onPointerLeave={powerOff}
    onFocus={powerOn}
    onBlur={powerOff}
    className={cn("side-link", active && "side-link-active", isPowered && "side-link-powered")}
  >
    <Icon size={18} /><span>{label}</span>
  </Link>;
}
